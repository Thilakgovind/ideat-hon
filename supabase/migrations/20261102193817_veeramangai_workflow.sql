-- Additive workflow state, transactional events and a Gmail delivery outbox.
-- Run after 004_veeramangai_sports.sql. No production data is seeded.
begin;
alter table public.vm_athlete_profiles add column if not exists email_updates boolean not null default false;
alter table public.vm_support_requests add column if not exists coordinator_id uuid references auth.users(id);
alter table public.vm_support_requests add column if not exists updated_at timestamptz not null default now();
create index if not exists vm_requests_coordinator on public.vm_support_requests(coordinator_id);

create table if not exists public.vm_notification_contacts (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email text not null check (length(email) <= 320), consented_at timestamptz not null default now()
);
create table if not exists public.vm_workflow_events (
  actor_id uuid not null references auth.users(id) on delete cascade,
  event_id uuid not null, fingerprint text not null, result jsonb,
  created_at timestamptz not null default now(), primary key(actor_id,event_id)
);
create table if not exists public.vm_notification_outbox (
  id uuid primary key default gen_random_uuid(), event_id uuid not null,
  request_id uuid not null references public.vm_support_requests(id) on delete cascade,
  recipient_id uuid not null references auth.users(id) on delete cascade,
  state text not null default 'pending' check (state in ('pending','sending','sent','uncertain','suppressed')),
  claim_id uuid, provider_id text, attempted_at timestamptz, created_at timestamptz not null default now(),
  unique(event_id,recipient_id)
);
create index if not exists vm_outbox_pending on public.vm_notification_outbox(state,created_at);
create index if not exists vm_outbox_request on public.vm_notification_outbox(request_id);
create index if not exists vm_outbox_recipient on public.vm_notification_outbox(recipient_id);

alter table public.vm_notification_contacts enable row level security;
alter table public.vm_workflow_events enable row level security;
alter table public.vm_notification_outbox enable row level security;
revoke all on public.vm_notification_contacts, public.vm_workflow_events, public.vm_notification_outbox from anon, authenticated;
grant select,insert,update,delete on public.vm_notification_contacts, public.vm_workflow_events, public.vm_notification_outbox to service_role;

create or replace function public.vm_save_profile(p_actor uuid, p_profile jsonb, p_email text)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare result jsonb;
begin
  if p_actor is null or length(trim(p_profile->>'display_name')) not between 1 and 50 then
    raise exception 'invalid_profile';
  end if;
  insert into public.vm_athlete_profiles(user_id,display_name,district_id,sport_id,language,email_updates)
  values(p_actor,p_profile->>'display_name',p_profile->>'district_id',p_profile->>'sport_id',p_profile->>'language',
    coalesce((p_profile->>'email_updates')::boolean,false))
  on conflict(user_id) do update set display_name=excluded.display_name,district_id=excluded.district_id,
    sport_id=excluded.sport_id,language=excluded.language,email_updates=excluded.email_updates;
  if coalesce((p_profile->>'email_updates')::boolean,false) and p_email is not null then
    insert into public.vm_notification_contacts(user_id,email) values(p_actor,p_email)
    on conflict(user_id) do update set email=excluded.email,consented_at=now();
  else
    delete from public.vm_notification_contacts where user_id=p_actor;
    update public.vm_notification_outbox set state='suppressed' where recipient_id=p_actor and state='pending';
  end if;
  select to_jsonb(p) into result from public.vm_athlete_profiles p where user_id=p_actor;
  return result;
end $$;

create or replace function public.vm_request_change(p_actor uuid,p_event uuid,p_action text,p_data jsonb)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  event public.vm_workflow_events%rowtype;
  req public.vm_support_requests%rowtype;
  digest text := md5(jsonb_build_object('action',p_action,'data',p_data)::text);
  v_result jsonb;
  rid uuid;
  target_status text;
begin
  if p_actor is null or p_event is null then raise exception 'invalid_event'; end if;
  -- Concurrent inserts wait on the unique key. The entire mutation rolls back on error.
  insert into public.vm_workflow_events(actor_id,event_id,fingerprint)
    values(p_actor,p_event,digest) on conflict do nothing;
  select * into event from public.vm_workflow_events where actor_id=p_actor and event_id=p_event for update;
  if event.fingerprint <> digest then raise exception 'event_conflict'; end if;
  if event.result is not null then return event.result || '{"duplicate":true}'::jsonb; end if;
  if p_action = 'submit' then
    if not exists(select 1 from public.vm_athlete_profiles where user_id=p_actor) then raise exception 'profile_required'; end if;
    if p_data->>'opportunity_id' is not null and not exists(
      select 1 from public.vm_opportunities where id=p_data->>'opportunity_id' and source='verified' and status='open'
        and (deadline is null or deadline >= current_date)
    ) then raise exception 'sample_opportunity'; end if;
    insert into public.vm_support_requests(user_id,category,opportunity_id,coordinator_id)
      values(p_actor,p_data->>'category',p_data->>'opportunity_id',(p_data->>'coordinator_id')::uuid) returning * into req;
  elsif p_action = 'transition' then
    rid := (p_data->>'request_id')::uuid;
    select * into req from public.vm_support_requests where id=rid for update;
    if not found then raise exception 'request_not_found'; end if;
    target_status := p_data->>'status';
    if (target_status='cancelled' and req.user_id<>p_actor) or
       (target_status<>'cancelled' and (req.coordinator_id is null or req.coordinator_id<>p_actor)) then
      raise exception 'request_forbidden';
    end if;
    if req.status <> p_data->>'expected_status' or not (
      (req.status='submitted' and target_status in ('reviewing','declined','cancelled')) or
      (req.status='reviewing' and target_status in ('approved','declined','cancelled'))
    ) then raise exception 'invalid_transition'; end if;
    update public.vm_support_requests set status=target_status,updated_at=now() where id=rid returning * into req;
  else raise exception 'invalid_action'; end if;
  insert into public.vm_request_events(request_id,status) values(req.id,req.status);
  -- Each recipient must independently opt into generic email updates on their profile.
  insert into public.vm_notification_outbox(event_id,request_id,recipient_id)
    select p_event,req.id,c.user_id from public.vm_notification_contacts c
    where c.user_id in (req.user_id,req.coordinator_id) on conflict do nothing;
  v_result := jsonb_build_object('request',to_jsonb(req),'duplicate',false,'notification','queued_if_opted_in');
  update public.vm_workflow_events set result=v_result where actor_id=p_actor and event_id=p_event;
  return v_result;
end $$;

create or replace function public.vm_claim_notifications(p_event uuid default null)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare delivery record; result jsonb := '[]'::jsonb; token uuid;
begin
  update public.vm_notification_outbox o set state='suppressed' where state='pending'
    and not exists(select 1 from public.vm_notification_contacts c where c.user_id=o.recipient_id);
  for delivery in
    select o.id,c.email from public.vm_notification_outbox o
    join public.vm_notification_contacts c on c.user_id=o.recipient_id
    where o.state='pending' and (p_event is null or o.event_id=p_event)
    order by o.created_at,o.id limit 20 for update of o skip locked
  loop
    token := gen_random_uuid();
    update public.vm_notification_outbox set state='sending',claim_id=token,attempted_at=now() where id=delivery.id;
    result := result || jsonb_build_array(jsonb_build_object('delivery_id',delivery.id,'claim_id',token,
      'to',delivery.email,'subject','Veeramangai: a request update is ready',
      'message','There is an update in your Veeramangai workspace. Sign in to review it. This email contains no request details.'));
  end loop;
  return result;
end $$;

create or replace function public.vm_finish_notification(p_id uuid,p_claim uuid,p_status text,p_provider text)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare delivery public.vm_notification_outbox%rowtype;
begin
  select * into delivery from public.vm_notification_outbox where id=p_id for update;
  if not found or delivery.claim_id is distinct from p_claim then raise exception 'claim_conflict'; end if;
  if p_status not in ('sent','uncertain') or (p_status='sent' and coalesce(length(p_provider),0)=0) then raise exception 'claim_conflict'; end if;
  if delivery.state='sent' and delivery.provider_id=p_provider and p_status='sent' then
    return jsonb_build_object('delivery_id',p_id,'state','sent');
  end if;
  if delivery.state<>'sending' then raise exception 'claim_conflict'; end if;
  update public.vm_notification_outbox set state=p_status,provider_id=p_provider where id=p_id;
  return jsonb_build_object('delivery_id',p_id,'state',p_status);
end $$;

revoke all on function public.vm_save_profile(uuid,jsonb,text) from public,anon,authenticated;
revoke all on function public.vm_request_change(uuid,uuid,text,jsonb) from public,anon,authenticated;
revoke all on function public.vm_claim_notifications(uuid) from public,anon,authenticated;
revoke all on function public.vm_finish_notification(uuid,uuid,text,text) from public,anon,authenticated;
grant execute on function public.vm_save_profile(uuid,jsonb,text) to service_role;
grant execute on function public.vm_request_change(uuid,uuid,text,jsonb) to service_role;
grant execute on function public.vm_claim_notifications(uuid) to service_role;
grant execute on function public.vm_finish_notification(uuid,uuid,text,text) to service_role;
notify pgrst,'reload schema';
commit;

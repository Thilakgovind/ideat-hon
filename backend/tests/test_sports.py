import json
from pathlib import Path
import pytest
from backend import sports_store
from backend.seed.sports_sample import generate, PUBLIC_TABLES, PRIVATE_TABLES
from backend.seed_sports import normalize
from backend.tests.test_veeramangai import client

def test_sample_relations_and_uniform_rows():
    data=generate()
    assert data==generate()
    assert [len(data[t]) for t in PUBLIC_TABLES]==[12,6,72,648,288]
    assert sum(map(len,data.values())) > 1000
    assert len({o['name'] for o in data['vm_opportunities']}) == 648
    assert not any(t in data for t in PRIVATE_TABLES)
    for table,rows in data.items():
        assert len({r['id'] for r in rows})==len(rows)
        assert all(set(r)==set(rows[0]) and r['source']=='sample' for r in rows)
    districts={r['id'] for r in data['vm_districts']}
    orgs={r['id'] for r in data['vm_organizations']}
    sports={r['id'] for r in data['vm_sports']}
    for row in data['vm_opportunities']:
        assert row['district_id'] in districts and row['sport_id'] in sports and row['organization_id'] in orgs
        assert row['status']=='sample' and row['starts_on'] is None and row['application_url'] is None
    assert 'phone' not in json.dumps(data)
    assert normalize([{'a':1},{'b':2}])==[{'a':1,'b':None},{'a':None,'b':2}]

def test_catalog_fallback_and_private_guard():
    result=client.get('/api/veeramangai/catalog')
    assert result.status_code==200
    body=result.json()
    assert len(body['opportunities'])==648 and 'Sample' in body['notice']
    assert all(v=='sample_fallback' for v in body['storage'].values())
    assert body['opportunities'][0]['sport']=='Athletics'
    with pytest.raises(ValueError):
        sports_store.read('vm_support_requests')

def test_remote_catalog_and_failure(monkeypatch):
    monkeypatch.setattr(sports_store.config,'has',lambda _:True)
    class Response:
        def raise_for_status(self): pass
        def json(self): return [{'id':'verified_reference'}]
    monkeypatch.setattr(sports_store.httpx,'get',lambda *a,**kw:Response())
    assert sports_store.read('vm_sports')==([{'id':'verified_reference'}],'supabase')
    def fail(*a,**kw): raise sports_store.httpx.ConnectError('offline')
    monkeypatch.setattr(sports_store.httpx,'get',fail)
    assert sports_store.read('vm_sports')[1]=='sample_fallback'

def test_migration_privacy():
    sql=(Path(__file__).resolve().parents[2]/'supabase/migrations/004_veeramangai_sports.sql').read_text()
    for table in (*PUBLIC_TABLES,*PRIVATE_TABLES):
        assert 'public.'+table in sql and "'"+table+"'" in sql
    assert 'enable row level security' in sql
    assert '(select auth.uid()) = user_id' in sql
    assert 'revoke all' in sql and 'grant select on public.vm_athlete_profiles' in sql
    assert 'drop table' not in sql.lower() and 'truncate' not in sql.lower()

def test_n8n_does_not_forward_private_text():
    workflow=json.loads((Path(__file__).resolve().parents[2]/'n8n/veeramangai_avvai.json').read_text())
    assert workflow['active'] is False
    nodes={node['name']:node for node in workflow['nodes']}
    assert nodes['Incoming']['parameters']['authentication']=='none'
    assert 'text: prompts[body.topic]' in nodes['Minimize input']['parameters']['jsCode']
    assert '/api/veeramangai/chat' in nodes['Avvai backend']['parameters']['url']

def test_large_seed_batches_and_verifies(monkeypatch, capsys):
    from backend import seed_sports
    stored, batches = {}, []
    monkeypatch.setattr(seed_sports,'write',generate)
    monkeypatch.setattr(seed_sports.config,'has',lambda _:True)
    class Response:
        status_code=200
        def __init__(self,rows): self.rows=rows
        def json(self): return self.rows
    class Client:
        def __init__(self,**kw): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def post(self,url,params,headers,json):
            table=url.rsplit('/',1)[1]
            batches.append(len(json))
            stored.setdefault(table,{}).update({r['id']:r for r in json})
            return Response([])
        def get(self,url,params,headers):
            if params.get('limit')==0: return Response([])
            ids=params['id'][4:-1].split(',')
            assert len(ids)<=100
            table=url.rsplit('/',1)[1]
            return Response([stored[table][key] for key in ids])
    monkeypatch.setattr(seed_sports.httpx,'Client',Client)
    assert seed_sports.main([])==0
    assert max(batches)<=200 and len(batches)==9
    assert sum(map(len,stored.values()))==1026
    assert 'vm_opportunities: 648' in capsys.readouterr().out

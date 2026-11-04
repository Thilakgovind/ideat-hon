from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend import vm_workflow as w, veeramangai as v

app=FastAPI()
app.include_router(w.router)
app.include_router(v.router)
client=TestClient(app)

def test_private_endpoints_require_login():
    assert client.get('/api/veeramangai/workspace').status_code==401
    assert client.post('/api/veeramangai/automation/claim',json={}).status_code==401

def test_coordinator_is_not_any_signed_in_user():
    app.dependency_overrides[w.identity]=lambda:{'auth_id':'00000000-0000-0000-0000-000000000001'}
    try:
        assert client.get('/api/veeramangai/coordinator/requests').status_code==403
    finally:
        app.dependency_overrides.clear()

def test_n8n_receives_only_task_and_language(monkeypatch):
    monkeypatch.setattr(v.local_model, 'enabled', lambda: True)
    monkeypatch.setenv('VM_N8N_GUIDE_URL','https://n8n.example/webhook/guide')
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'reply':'Prepare a fee request.','module':'funding','provider':'gemini'}
    def post(url,**kw):
        assert kw['json']=={'topic':'funding','lang':'en'}
        return Response()
    monkeypatch.setattr(v.httpx,'post',post)
    result=client.post('/api/veeramangai/assistant',json={'text':'My name is Person and I need fee support','lang':'en'})
    assert result.json()['orchestration']=='n8n'

def test_n8n_failure_uses_backend(monkeypatch):
    monkeypatch.setenv('VM_N8N_GUIDE_URL','https://n8n.example/webhook/guide')
    def fail(*a,**kw): raise v.httpx.ConnectError('offline')
    monkeypatch.setattr(v.httpx,'post',fail)
    monkeypatch.setattr(v.config,'has',lambda _:False)
    r=client.post('/api/veeramangai/assistant',json={'text':'travel'})
    assert r.status_code==200 and r.json()['orchestration']=='backend_fallback'

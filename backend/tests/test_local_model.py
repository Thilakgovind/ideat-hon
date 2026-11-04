from backend import local_model as m, veeramangai as v

def test_local_model_json_validation(monkeypatch):
    class Reply:
        def raise_for_status(self): pass
        def json(self): return {'done':True,'message':{'content':'{"reply":"Prepare your equipment request."}'}}
    monkeypatch.setattr(m.httpx,'post',lambda *a,**kw: Reply())
    assert m.generate('Prepare equipment request','en')['provider']=='ollama'

def test_remote_ollama_url_refused(monkeypatch):
    monkeypatch.setenv('OLLAMA_BASE_URL','https://remote.example')
    assert m.generate('test','en') is None

def test_local_selection_bypasses_cloud_and_keeps_names_out(monkeypatch):
    monkeypatch.setenv('AVVAI_MODEL_PROVIDER','ollama')
    # Isolate the local fallback path; production guidance prefers n8n when configured.
    monkeypatch.setenv('VM_N8N_GUIDE_URL', '')
    def generate(instruction,lang):
        assert 'Priya' not in instruction and '5000011111' not in instruction
        return {'reply':instruction,'provider':'ollama','model':'qwen2.5:3b'}
    monkeypatch.setattr(m,'generate',generate)
    result=v.chat(v.Message(text='Priya 5000011111 needs fee help'))
    assert result['provider']=='ollama'

def test_local_failure_returns_fixed_reply(monkeypatch):
    monkeypatch.setenv('AVVAI_MODEL_PROVIDER','ollama')
    monkeypatch.setattr(m,'generate',lambda *a:None)
    assert v.chat(v.Message(text='rest'))['provider']=='fallback'

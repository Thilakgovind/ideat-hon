from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend import veeramangai

app = FastAPI()
app.include_router(veeramangai.router)
client = TestClient(app)

def test_sports_guidance_selects_feature_without_actions(monkeypatch):
    monkeypatch.setattr(veeramangai.config, 'has', lambda name: False)
    for text, module in [('entry fee help', 'funding'), ('trusted travel', 'travel'), ('coach rest', 'support'), ('find a trial', 'opportunities')]:
        result = client.post('/api/veeramangai/chat', json={'text': text}).json()
        assert result['href'] == f'/veeramangai/{module}'
        assert result['provider'] == 'fallback' and result['sample']

def test_only_app_instructions_are_sent_to_gemini(monkeypatch):
    monkeypatch.setattr(veeramangai.config, 'has', lambda name: True)
    def fail_after_check(*args, **kwargs):
        prompt = str(kwargs['json'])
        assert 'Priya' not in prompt and '5000011111' not in prompt
        raise ValueError('simulated invalid response')
    monkeypatch.setattr(veeramangai.httpx, 'post', fail_after_check)
    r = client.post('/api/veeramangai/chat', json={'text': 'Priya 5000011111 needs travel help'})
    assert r.status_code == 200 and r.json()['provider'] == 'fallback'

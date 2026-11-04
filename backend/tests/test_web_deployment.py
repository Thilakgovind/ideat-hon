"""The built app must deep-link without hiding missing API or asset errors."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from backend.spa import FrontendFiles
    (tmp_path / 'index.html').write_text('<html>Avvai</html>', encoding='utf-8')
    server = FastAPI()
    server.mount('/', FrontendFiles(directory=tmp_path, html=True))
    return TestClient(server)


@pytest.mark.parametrize('path', ['/veeramangai', '/veeramangai/login', '/veeramangai/requests', '/trip/demo'])
def test_deep_links(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert 'Avvai' in response.text
    assert response.headers['cache-control'] == 'no-cache'


@pytest.mark.parametrize('path', ['/api/missing', '/assets/missing.js', '/.env', '/veeramangai/missing.js'])
def test_missing_resources_stay_missing(client, path):
    assert client.get(path).status_code == 404

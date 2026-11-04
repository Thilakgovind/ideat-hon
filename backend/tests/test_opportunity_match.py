from fastapi.testclient import TestClient

from backend.app import app


def test_opportunity_match_is_grounded_and_ranked():
    response = TestClient(app).post('/api/veeramangai/opportunities/match', json={
        'sport': 'Athletics', 'district': 'Chennai', 'kind': 'trial', 'limit': 3,
    })
    assert response.status_code == 200
    body = response.json()
    assert len(body['matches']) == 3
    assert all(row['sport'] == 'Athletics' and row['district'] == 'Chennai' for row in body['matches'])
    assert all(row['source'] == 'sample' or row['status'] != 'open' for row in body['matches'])


def test_opportunity_match_query_can_return_empty_without_invention():
    response = TestClient(app).post('/api/veeramangai/opportunities/match', json={'query': 'underwater fencing'})
    assert response.status_code == 200
    assert response.json()['matches'] == []


def test_chat_includes_grounded_opportunity_matches():
    response = TestClient(app).post('/api/veeramangai/chat', json={
        'text': 'Find an Athletics trial in Chennai', 'lang': 'en',
    })
    assert response.status_code == 200
    body = response.json()
    assert body['module'] == 'opportunities'
    assert body['matches']
    assert all(row['sport'] == 'Athletics' and row['district'] == 'Chennai' for row in body['matches'])

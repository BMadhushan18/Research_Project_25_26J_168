from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_db_health_no_db(monkeypatch):
    # Simulate no DB available
    monkeypatch.setattr('app.db.is_available', lambda: False)
    r = client.get('/db/health')
    assert r.status_code == 200
    assert r.json() == {'available': False}


def test_db_health_yes(monkeypatch):
    monkeypatch.setattr('app.db.is_available', lambda: True)
    r = client.get('/db/health')
    assert r.status_code == 200
    assert r.json() == {'available': True}

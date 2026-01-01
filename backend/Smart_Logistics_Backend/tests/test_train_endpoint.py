import os
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_for_model.csv')


def test_train_sync():
    # Run synchronous training
    with open(TEST_CSV, 'rb') as f:
        resp = client.post('/train?background=false', files={'file': ('training_for_model.csv', f, 'text/csv')})
    assert resp.status_code == 200
    assert resp.json().get('status') == 'completed'


def test_train_background_and_status():
    with open(TEST_CSV, 'rb') as f:
        resp = client.post('/train', files={'file': ('training_for_model.csv', f, 'text/csv')})
    assert resp.status_code == 200
    data = resp.json()
    assert 'job_id' in data
    job_id = data['job_id']

    # poll for completion (fast for our synthetic dataset)
    for _ in range(30):
        s = client.get(f'/train/{job_id}')
        assert s.status_code == 200
        if s.json().get('status') == 'completed':
            break
        time.sleep(0.1)
    else:
        assert False, 'Background training did not complete in time'

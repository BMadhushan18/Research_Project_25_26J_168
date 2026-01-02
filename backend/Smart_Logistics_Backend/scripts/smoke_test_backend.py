from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

print('GET /db/health')
r = client.get('/db/health')
print(r.status_code, r.json())

print('\nPOST /predict')
r = client.post('/predict', json={'boq_text':'Supply and lay 50 m3 concrete using ACC cement'})
print(r.status_code)
print(json.dumps(r.json(), indent=2))

print('\nPOST /train (sync)')
with open('data/training_for_model.csv','rb') as f:
    files = {'file':('training_for_model.csv', f, 'text/csv')}
    r = client.post('/train?background=false', files=files)
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print('No JSON response:', e)

print('\nSmoke tests completed')

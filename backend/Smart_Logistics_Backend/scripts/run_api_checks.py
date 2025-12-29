from fastapi.testclient import TestClient
from backend.Smart_Logistics_Backend import runtime_shim as shim

client = TestClient(shim.app)

print('GET / ->', client.get('/').status_code, client.get('/').json())
print('GET /demo/health ->', client.get('/demo/health').status_code, client.get('/demo/health').json())

# GET OpenAPI summary
openapi = client.get('/openapi.json')
print('OpenAPI status:', openapi.status_code)
if openapi.status_code == 200:
    data = openapi.json()
    print('API title:', data.get('info', {}).get('title'))
    print('Paths count:', len(data.get('paths', {})))

# GET swagger ui HTML
docs_html = client.get('/api/docs')
print('/api/docs status:', docs_html.status_code)
print('Sample /api/docs HTML starts with:', docs_html.text.strip()[:120])

# POST demo predict
resp = client.post('/demo/predict', json={'material_tons': 3.5})
print('POST /demo/predict status:', resp.status_code, resp.json())

# Auth demo login
login = client.post('/api/v1/login', json={'username':'test','password':'p'})
print('POST /api/v1/login:', login.status_code, login.json())

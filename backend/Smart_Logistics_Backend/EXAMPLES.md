# Smart Logistics Backend — Examples

This file contains quick cURL and Python examples for common workflows.

## Base

Set base URL and obtain a token before calling protected endpoints.

```bash
BASE=http://127.0.0.1:8000
# login and save token
TOKEN=$(curl -s -X POST "$BASE/api/v1/login" -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' | jq -r '.access_token')
# example headers
AUTH_HEADER="Authorization: Bearer $TOKEN"
```

---

## Demo: Health

curl:

```bash
curl -X GET "$BASE/demo/health"
```

Python:

```python
import requests
print(requests.get("http://127.0.0.1:8000/demo/health").json())
```

---

## Demo: Predict

curl:

```bash
curl -X POST "$BASE/demo/predict" -H "Content-Type: application/json" -d '{"terrain":"urban","material_tons":5}'
```

Python:

```python
import requests
r = requests.post("http://127.0.0.1:8000/demo/predict", json={"terrain":"urban","material_tons":5})
print(r.json())
```

---

## Forecast (protected)

curl:

```bash
curl -X POST "$BASE/api/v1/forecast" -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"material_demands":{"cement":500}}'
```

Python:

```python
import requests
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
r = requests.post("http://127.0.0.1:8000/api/v1/forecast", headers=headers, json={"material_demands":{"cement":500}})
print(r.json())
```

---

## Upload Document (multipart, protected)

curl:

```bash
curl -X POST "$BASE/api/v1/upload-document" -H "$AUTH_HEADER" -F "file=@/path/to/boq.xlsx" -F "project_name=My Project"
```

Python:

```python
import requests
headers = {"Authorization": f"Bearer {TOKEN}"}
files = {"file": open("/path/to/boq.xlsx","rb")}
data = {"project_name":"My Project"}
r = requests.post("http://127.0.0.1:8000/api/v1/upload-document", headers=headers, files=files, data=data)
print(r.json())
```

---

## Optimize (protected)

curl:

```bash
curl -X POST "$BASE/api/v1/optimize" -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"predictions":{"fuel_liters":100},"constraints":{},"optimization_goals":["cost"]}'
```

Python:

```python
import requests
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
r = requests.post("http://127.0.0.1:8000/api/v1/optimize", headers=headers, json={"predictions":{"fuel_liters":100},"constraints":{},"optimization_goals":["cost"]})
print(r.json())
```

---

## Federated Update (protected)

curl:

```bash
curl -X POST "$BASE/api/v1/federated-update" -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"client_id":"client_1","model_parameters":{"w":[0.1,0.2]},"num_samples":100}'
```

---

## Projects & Statistics (protected)

curl:

```bash
curl -X GET "$BASE/api/v1/projects/<user_id>" -H "$AUTH_HEADER"
curl -X GET "$BASE/api/v1/statistics" -H "$AUTH_HEADER"
```

---

## Admin: Reload Config (header auth)

curl:

```bash
curl -X POST "$BASE/admin/reload-config" -H "X-Admin-Token: $ADMIN_TOKEN"
```

Replace `$ADMIN_TOKEN` with your admin token.

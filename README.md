# Telco Rule-Based Churn Risk Engine

Rule-based churn risk microservice for a telecom provider. The service ingests customer data plus support ticket history and returns a deterministic risk category without using machine learning.

## Features

- `POST /predict-risk` endpoint for churn risk evaluation
- FastAPI-generated OpenAPI documentation at `/docs` and `/openapi.json`
- Rule engine based on customer contract, ticket behavior, and charge changes
- JSON application logging
- Prometheus-compatible metrics exposed at `/metrics`
- Unit and API tests with `pytest`
- Docker image, Kubernetes deployment manifest, and CI pipeline
- Docker Compose observability stack with Prometheus and Grafana
- Ticket log simulation script for synthetic support behavior

## Business Rules

The API applies the following rules in priority order:

1. More than 5 tickets in the last 30 days -> `High`
2. Month-to-Month contract and at least one complaint ticket in the last 30 days -> `High`
3. Monthly charges increased and at least 3 tickets were raised in the last 30 days -> `Medium`
4. Otherwise -> `Low`

## Project Structure

```text
.
├── app/
├── data/
├── k8s/
├── monitoring/
├── scripts/
├── tests/
├── .github/workflows/ci.yml
├── Dockerfile
└── requirements.txt
```

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs:

- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`

Sample request:

```bash
curl -X POST http://localhost:8000/predict-risk \
  -H "Content-Type: application/json" \
  -d @data/sample_request.json
```

## Docker

```bash
docker build -t telco-rule-engine .
docker run -p 8000:8000 telco-rule-engine
```

## Local Observability Stack

```bash
docker compose up --build
```

Endpoints:

- API: `http://localhost:8000/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Tests

```bash
pytest
```

## Deployment

Apply the Kubernetes manifest:

```bash
kubectl apply -f k8s/deployment.yaml
```

## Monitoring

- Prometheus scrape target: `/metrics`
- Example Prometheus config: `monitoring/prometheus.yml`
- Example Grafana dashboard: `monitoring/grafana-dashboard.json`
- Structured inference logs are emitted to standard output

## Dataset and Ticket Simulation

Place the Kaggle Telco churn CSV at `data/Telco-Customer-Churn.csv` if you want to enrich the project with real customer records. Then generate simulated support activity:

```bash
python scripts/simulate_ticket_logs.py
```

# Telco Churn Risk Engine

Telecom churn risk microservice that evolves from a rule-based DevOps service into an ML-backed system. The current implementation includes an ML training pipeline, saved model artifacts, and an inference API driven by customer and ticket behavior.

## Features

- `POST /predict-risk` endpoint for ML churn risk inference
- `GET /model-info` endpoint for model metadata and evaluation metrics
- FastAPI-generated OpenAPI documentation at `/docs` and `/openapi.json`
- Feature engineering for ticket frequency windows, sentiment, category counts, ticket spacing, and monthly charge changes
- Model training pipeline with persisted artifacts and evaluation metrics
- JSON application logging
- Prometheus-compatible metrics exposed at `/metrics`
- Unit and API tests with `pytest`
- Docker image, Kubernetes deployment manifest, and CI pipeline
- Docker Compose observability stack with Prometheus and Grafana
- Ticket log simulation script for synthetic support behavior

## ML Features

The training and inference flows generate these features:

1. Ticket frequency over 7, 30, and 90 days
2. Average ticket sentiment score
3. Ticket category counts over 90 days
4. Average time between tickets
5. Change in monthly charges
6. Contract type, tenure, and current monthly charges

## Model Evaluation

The training pipeline reports:

1. F1 score
2. ROC-AUC
3. Average precision for the Precision-Recall tradeoff
4. Precision and recall

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

## Train Model

```bash
python scripts/train_model.py
```

Artifacts are written to `artifacts/churn_model.joblib` and `artifacts/metrics.json`.

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

Default Grafana login:

- Username: `admin`
- Password: `admin`

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
- Grafana provisioning: `monitoring/grafana/provisioning/`
- Structured inference logs are emitted to standard output

## Dataset and Ticket Simulation

Place the Kaggle Telco churn CSV at `data/Telco-Customer-Churn.csv` to train from the Telco Customer Churn dataset. Ticket logs are simulated and saved automatically during training, or you can generate them explicitly:

```bash
python scripts/simulate_ticket_logs.py
```

## Architecture Docs

GitHub-renderable Mermaid diagrams and assignment notes are available in `docs/`.

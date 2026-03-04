# DevOps Architecture

```mermaid
flowchart LR
    U[Client or CRM System] --> API[Rule-Based Risk API]
    OPS[Operations Team] --> GH[Git Repository]
    GH --> CI[CI Pipeline]
    CI --> TEST[Unit Tests]
    TEST --> BUILD[Docker Build]
    BUILD --> REG[Container Registry]
    REG --> CD[Deployment Pipeline]
    CD --> K8S[Kubernetes Deployment]
    K8S --> API

    CUST[(Customer Data)]
    TICK[(Ticket Logs)]
    CUST --> API
    TICK --> API

    API --> RULES[Business Rule Engine]
    RULES --> RESP[Risk Category Response]

    API --> LOGS[Structured Logs]
    API --> METRICS[Prometheus Metrics]
    METRICS --> PROM[Prometheus]
    PROM --> GRAF[Grafana Dashboard]
    LOGS --> MON[Log Monitoring]
```

## Notes

- Churn logic is fully deterministic and stored as business rules.
- CI/CD validates code, builds the container image, and deploys the service.
- Monitoring focuses on API health, latency, request volume, and logs.


# MLOps Architecture

```mermaid
flowchart LR
    subgraph Sources[Data Sources]
        CUST[(Customer Data)]
        TICK[(Ticket Logs)]
        LABELS[(Churn Labels)]
    end

    subgraph DataOps[Data and Feature Layer]
        ING[Data Ingestion Pipeline]
        VAL[Data Validation]
        FE[Feature Engineering Pipeline]
        FS[(Feature Store)]
    end

    subgraph Train[Training and Registry]
        TRAIN[Training Pipeline]
        EVAL[Evaluation and Validation]
        REGM[(Model Registry)]
        EXP[(Experiment Tracking)]
    end

    subgraph Serve[Serving Layer]
        CI[CI Pipeline]
        CD[CD Pipeline]
        INF[Inference Service]
        MON[Model Monitoring]
    end

    subgraph Obs[Observability]
        PROM[Prometheus]
        GRAF[Grafana]
        ALERT[Alerts]
        DRIFT[Drift Detection]
    end

    CUST --> ING
    TICK --> ING
    LABELS --> ING
    ING --> VAL
    VAL --> FE
    FE --> FS
    FS --> TRAIN
    TRAIN --> EVAL
    TRAIN --> EXP
    EVAL --> REGM
    REGM --> CI
    CI --> CD
    CD --> INF

    CUST --> INF
    TICK --> INF
    FS --> INF

    INF --> MON
    INF --> PROM
    PROM --> GRAF
    MON --> DRIFT
    DRIFT --> ALERT
    EVAL --> ALERT
```

## Notes

- MLOps adds automated data validation, experiment tracking, model registry, and drift monitoring.
- Deployment decisions depend on both software quality and model quality gates.
- Monitoring extends beyond service uptime to data quality, prediction quality, and model decay.


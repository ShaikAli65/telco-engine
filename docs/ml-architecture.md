# ML Architecture

```mermaid
flowchart LR
    U[Client or CRM System] --> INF[Model Inference API]

    CUST[(Customer Data)]
    TICK[(Ticket Logs)]
    CUST --> FE[Feature Engineering]
    TICK --> FE

    FE --> TRAIN[Training Script]
    TRAIN --> EVAL[Model Evaluation]
    EVAL --> ART[Saved Model Artifact]

    ART --> INF
    FE --> INF
    INF --> PRED[Predicted Churn Risk]

    DS[Data Scientist or ML Engineer] --> GH[Git Repository]
    GH --> CI[CI Pipeline]
    CI --> TEST[Code and Model Tests]
    TEST --> BUILD[Docker Build]
    BUILD --> REG[Container Registry]
    REG --> DEPLOY[Deployment]
    DEPLOY --> INF

    INF --> LOGS[Inference Logs]
    INF --> METRICS[Service Metrics]
    EVAL --> REPORT[Evaluation Reports]
```

## Notes

- Rule logic is replaced by a trained classifier model.
- The system now depends on feature engineering, model training, and saved artifacts.
- Evaluation metrics such as F1, ROC-AUC, and Precision-Recall become mandatory.


# Observability

> *"Metrics without dashboards are noise. Dashboards without alerts are museums."*

This document explains the Prometheus metrics, Grafana dashboard, structured logging, and MLflow tracking that make this system observable.

---

## What We Track and Why

We split observability into three signals — each answers a different question:

| Signal | Tool | Question It Answers |
|--------|------|-------------------|
| **Metrics** | Prometheus + Grafana | Is the system healthy right now? |
| **Logs** | JSON-structured stdout | What exactly happened for this request? |
| **Traces** | MLflow experiments | How are our evaluation scores trending over time? |

We deliberately chose not to add distributed tracing (OpenTelemetry). For a starter RAG system with a single service, traces add complexity without proportional insight. Metrics + logs + experiment tracking cover the Three Signals.

---

## Prometheus Metrics

The app exposes metrics at `GET /metrics`. Prometheus scrapes this endpoint every 15 seconds.

### Metric reference

| Metric | Type | What It Captures | Why It Matters |
|--------|------|------------------|----------------|
| `rag_requests_total` | Counter | HTTP request count by endpoint, method, status | Error rate = `rag_requests_total{status=~"5.."}` / `rag_requests_total` |
| `rag_request_duration_seconds` | Histogram | Request latency by endpoint | p95 > 30s on `/query` = bad chunking or slow model |
| `rag_retrieval_duration_seconds` | Histogram | Retrieval pipeline latency | Spikes here mean Qdrant is struggling or the query is bad |
| `rag_generation_duration_seconds` | Histogram | LLM generation latency | High = model is too large, consider gpt-4o-mini |
| `rag_chunks_retrieved_total` | Histogram | Chunks returned per query | Consistently retrieving 1 chunk means your top_k is too low |
| `rag_tokens_total` | Counter | Prompt and completion tokens | Trend up = your documents are growing or your prompts are bloating |
| `rag_cost_usd_total` | Counter | Estimated USD cost | Track this against your OpenAI bill |
| `rag_documents_ingested_total` | Counter | Documents ingested by strategy | See which chunking strategy is used most |
| `rag_evaluation_scores` | Gauge | Latest faithfulness/relevancy/recall | Alert when faithfulness drops below 0.7 |

### Understanding histograms

`rag_request_duration_seconds` is a histogram, not a summary. It exposes:
- `_count` — total number of requests
- `_sum` — total duration in seconds
- `_bucket{le="X"}` — count of requests <= X seconds

To calculate p95 in Grafana: `histogram_quantile(0.95, rate(rag_request_duration_seconds_bucket[5m]))`

---

## Grafana Dashboard

The dashboard is pre-provisioned — open [localhost:3000](http://localhost:3000) (no login required).

### Panel guide

| Panel | Query | What To Look For |
|-------|-------|------------------|
| **Request Rate** | `rate(rag_requests_total[1m])` | Steady = healthy. Flatline = app is down. |
| **Error Rate** | `rate(rag_requests_total{status_code=~"5.."}[1m])` | Should be near zero. Spikes = bugs. |
| **Latency p50/p95** | `histogram_quantile(0.5/0.95, ...)` | p95 should be < 10s for queries. Ingestion should be < 2s. |
| **Retrieval Latency** | `rag_retrieval_duration_seconds_count` | Should be < 100ms. High = Qdrant indexing issue. |
| **Generation Latency** | `rag_generation_duration_seconds_count` | Should be < 8s for gpt-4o-mini. |
| **Chunks Retrieved** | `rag_chunks_retrieved_total_count` | Should match your top_k parameter. |
| **Token Usage** | `rate(rag_tokens_total[5m])` | Watch for prompt bloat over time. |
| **Estimated Cost** | `rag_cost_usd_total` | Track daily/weekly trend. |
| **Evaluation Scores** | `rag_evaluation_scores` | Should stay above 0.7. Investigate drops. |

### Adding alerts

This dashboard doesn't include Alertmanager. For production, add:

```
# prometheus/alerts.yml
groups:
  - name: rag-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(rag_requests_total{status_code=~"5.."}[5m]) > 0.05
        for: 5m
      - alert: LowFaithfulness
        expr: rag_evaluation_scores{metric="faithfulness"} < 0.7
```

Then configure Alertmanager to route to Slack/PagerDuty.

---

## Structured Logging

Every log line is JSON, parseable without regex:

```json
{"timestamp": "2026-05-07T12:29:32", "level": "INFO", "name": "app.api.query", "message": "Query processed in 5.2s"}
```

This includes uvicorn access logs:

```json
{"timestamp": "2026-05-07T12:29:32", "level": "INFO", "name": "uvicorn.access", "message": "172.21.0.1:54321 - "POST /query HTTP/1.1" 200"}
```

### Why JSON

- **Grep-friendly**: `docker compose logs app | rg '"level": "ERROR"'`
- **Log aggregator ready**: Loki, ELK, and Datadog can ingest without custom parsing
- **Structured fields**: The `name` field lets you filter by component (`uvicorn.access` vs `app.api.query`)

---

## MLflow Tracking

MLflow serves as our experiment tracker — it captures every operation with latency and cost metrics.

### Experiments

| Experiment | When It Logs | Key Parameters | Key Metrics |
|------------|-------------|----------------|-------------|
| `rag-ingestion` | Each document ingested | filename, chunking_strategy | chunk_count, ingest_latency_ms |
| `rag-queries` | Each query answered | query, alpha, top_k, model | prompt_tokens, completion_tokens, estimated_cost_usd, latency |
| `rag-evaluation` | Each evaluation run | query | faithfulness, answer_relevancy, context_recall |

### Fire-and-forget design

MLflow is never on the critical path. Every call is wrapped in try/except:

```python
try:
    mlflow.set_experiment("rag-queries")
    with mlflow.start_run():
        mlflow.log_params(...)
        mlflow.log_metrics(...)
except Exception:
    logger.warning("Failed to log to MLflow", exc_info=True)
```

This means: if MLflow is down, the app still works — you just don't get tracking for that request.

### Cost tracking

Every query logs `estimated_cost_usd` to MLflow, calculated as:

```
cost = prompt_tokens * $0.00000015 + completion_tokens * $0.0000006
```

These rates match gpt-4o-mini pricing. Adjust `COST_PER_INPUT_TOKEN` and `COST_PER_OUTPUT_TOKEN` in `app/api/query.py` if you change models.

Open [localhost:5000](http://localhost:5000) to compare runs, filter by date range, and export data.

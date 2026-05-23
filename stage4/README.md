# Monitoring and Observability Stack

Production-grade observability for the local AI infrastructure stack.
Tracks RAG pipeline performance, agent tool routing behavior, and
host system resources in real time with drift detection via Evidently AI.

## Architecture

RAG Pipeline (port 8000)  ──► /metrics ──┐
Agent API    (port 8001)  ──► /metrics ──┤
Host System          ──► node-exporter ──┤
│
Prometheus (port 9090)
scrapes every 15s
│
Grafana (port 3000)
visualizes all metrics
RAG Pipeline queries ──► Evidently (port 8050)
logs answer quality metrics

RAG Pipeline (port 8000)  ──► /metrics ──┐
Agent API    (port 8001)  ──► /metrics ──┤
Host System          ──► node-exporter ──┤
│
Prometheus (port 9090)
scrapes every 15s
│
Grafana (port 3000)
visualizes all metrics
RAG Pipeline queries ──► Evidently (port 8050)
logs answer quality metrics

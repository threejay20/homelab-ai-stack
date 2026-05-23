from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from evidently.report import Report
from evidently.metric_preset import TextOverviewPreset
from evidently.metrics import (
    ColumnSummaryMetric,
    DatasetSummaryMetric
)
from datetime import datetime
import json
import os

app = FastAPI(
    title="Homelab AI Quality Monitor",
    description="Evidently AI monitoring for RAG pipeline quality",
    version="1.0.0"
)

# ─────────────────────────────────────────
# In-memory query log
# Stores recent RAG queries and answers
# for quality analysis
# ─────────────────────────────────────────
query_log = []
MAX_LOG_SIZE = 500

# ─────────────────────────────────────────
# Models
# ─────────────────────────────────────────
class QueryRecord(BaseModel):
    question: str
    answer: str
    collection: str
    timestamp: str = None
    answer_length: int = None
    question_length: int = None

class QualityReport(BaseModel):
    total_queries: int
    avg_answer_length: float
    avg_question_length: float
    short_answers: int
    timestamp: str

# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "Homelab AI Quality Monitor",
        "status": "running",
        "queries_logged": len(query_log)
    }

@app.get("/health")
def health():
    return {"status": "ok", "queries_logged": len(query_log)}

@app.post("/log")
def log_query(record: QueryRecord):
    """
    Log a RAG query and answer for quality monitoring.
    Called by the RAG pipeline after each query.
    """
    record.timestamp = datetime.utcnow().isoformat()
    record.answer_length = len(record.answer)
    record.question_length = len(record.question)

    query_log.append(record.dict())

    # Keep log size bounded
    if len(query_log) > MAX_LOG_SIZE:
        query_log.pop(0)

    return {"logged": True, "total": len(query_log)}

@app.get("/quality", response_model=QualityReport)
def quality_report():
    """
    Returns basic quality metrics over logged queries.
    """
    if len(query_log) == 0:
        raise HTTPException(
            status_code=404,
            detail="No queries logged yet"
        )

    df = pd.DataFrame(query_log)

    short_answers = int((df["answer_length"] < 100).sum())

    return QualityReport(
        total_queries=len(df),
        avg_answer_length=round(float(df["answer_length"].mean()), 1),
        avg_question_length=round(float(df["question_length"].mean()), 1),
        short_answers=short_answers,
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/report")
def evidently_report():
    """
    Runs an Evidently report over logged queries.
    Returns JSON summary of data quality metrics.
    """
    if len(query_log) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 5 queries to generate report. Have {len(query_log)}."
        )

    df = pd.DataFrame(query_log)
    df = df[["question_length", "answer_length"]].astype(float)

    report = Report(metrics=[
        DatasetSummaryMetric(),
        ColumnSummaryMetric(column_name="answer_length"),
        ColumnSummaryMetric(column_name="question_length"),
    ])

    report.run(reference_data=None, current_data=df)

    report_dict = json.loads(report.json())

    return {
        "status": "ok",
        "queries_analyzed": len(df),
        "timestamp": datetime.utcnow().isoformat(),
        "summary": report_dict.get("metrics", [])
    }

@app.get("/queries")
def recent_queries():
    """Return the last 20 logged queries."""
    return {
        "queries": query_log[-20:],
        "total": len(query_log)
    }

@app.delete("/log")
def clear_log():
    """Clear the query log — useful for testing."""
    query_log.clear()
    return {"cleared": True}

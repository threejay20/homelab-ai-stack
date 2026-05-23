# CI/CD for AI — Automated Evaluation Pipeline

Automated test suite and GitHub Actions pipeline for evaluating
RAG pipeline retrieval quality and agent tool routing correctness
on every push to main.

## Pipeline Architecture

Push to main
│
▼
GitHub Actions (ubuntu-latest)
│
├── Start full AI stack (Stage 1 + 2 + 2.5)
│
├── RAG Evaluation
│   ├── Health checks — Qdrant, Ollama connectivity
│   ├── Ingestion tests — chunk count, file validation
│   └── Retrieval quality — keyword assertions on known content
│
├── Agent Evaluation
│   ├── Health checks — all tool connectivity
│   ├── Routing tests — correct tool selected per question type
│   ├── Response structure — required fields present
│   └── Answer quality — content assertions
│
└── Pass / Fail reported on commit

## Test Coverage

| Test Class | What It Catches |
|---|---|
| `TestRAGHealth` | Dependency connectivity regressions |
| `TestRAGIngestion` | Broken ingestion pipeline, missing error handling |
| `TestRAGRetrieval` | Retrieval quality degradation, prompt regressions |
| `TestAgentHealth` | Tool connectivity failures |
| `TestToolRouting` | Routing logic regressions from prompt changes |
| `TestAgentResponse` | Response contract breakage, empty answers |
| `TestDirectToolEndpoints` | Individual tool failures independent of agent |

## Design Decisions

**Keyword assertions over exact match** — LLMs are non-deterministic.
Testing for domain-specific keywords from known source documents
provides meaningful quality signal without brittle exact-match tests
that fail on minor phrasing changes.

**Known test document in conftest.py** — ingesting a controlled
document with predictable content makes retrieval tests deterministic.
Testing against real ingested documents would introduce flakiness
from content drift.

**Tool isolation tests** — direct tool endpoints are tested
independently of the agent. This separates tool failures from
routing failures, making regression diagnosis fast.

**Logs on failure only** — container logs print automatically
when any step fails, providing immediate debugging context without
polluting successful run output.

## Running Tests Locally

```bash
# Ensure Stage 1, 2, and 2.5 are running first
cd stage3
pip install pytest httpx
pytest tests/ -v
```

Run a single test class:
```bash
pytest tests/test_rag.py::TestRAGRetrieval -v
pytest tests/test_agent.py::TestToolRouting -v
```

## AWS Bedrock Equivalent

| Local Component | AWS Equivalent |
|---|---|
| GitHub Actions | AWS CodePipeline + CodeBuild |
| pytest eval suite | CodeBuild test phase |
| Docker Compose test env | ECS task definitions |
| Keyword assertions | Bedrock model evaluation jobs |

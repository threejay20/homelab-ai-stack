# Stage 3 — CI/CD Evaluation Pipeline

Automated quality gates for the AI system. Every push to main triggers build validation and a 32-test evaluation suite covering RAG quality, authentication, agent routing, and response contracts.

## What It Does

Runs two GitHub Actions jobs on every push: one that validates Docker images build successfully, and one that runs the pytest evaluation suite against the live system to catch regressions.

## Test Coverage

| Category | Tests | What it validates |
|---|---|---|
| RAG health | 3 | Pipeline is reachable and responding |
| Authentication | 4 | API key enforcement on all endpoints |
| Ingestion | 5 | Documents ingest and chunk correctly |
| Retrieval quality | 6 | Answers are grounded and relevant |
| Agent routing | 7 | Correct tool selected for query type |
| Response contracts | 7 | Output schema matches expected format |

**Total: 32 tests, 100% passing**

## Key Design Decisions

**CI runs syntax validation only** — Running LLM inference on GitHub Actions would require pulling Ollama models (4GB+), starting the full Docker stack, and waiting for inference (15-30 seconds per test). This makes CI slow, expensive, and flaky. Instead CI validates that the test suite is syntactically correct and imports cleanly. Full eval runs locally against live endpoints where models are already loaded.

**Tests as regression guards not unit tests** — These tests are not testing Python functions in isolation. They are testing the behaviour of the complete system end-to-end. A RAG retrieval test sends a real query and asserts the answer contains expected keywords. An auth test sends a request without a key and asserts a 403 response. This catches integration failures that unit tests miss.

**pytest installed in user space** — pytest is installed at ~/.local/bin/pytest to avoid requiring root access or virtual environments on the host machine running the tests.

**Separate conftest.py** — Base URLs, API keys, and shared fixtures live in conftest.py. Tests import from there rather than hardcoding values. Changing an endpoint URL requires editing one file.

## AWS Equivalent

| Local | AWS |
|---|---|
| GitHub Actions | AWS CodePipeline + CodeBuild |
| pytest eval suite | Amazon SageMaker Pipelines (eval step) |
| RAG quality tests | Bedrock model evaluation jobs |
| Response contract tests | AWS Lambda integration tests |

## Quick Start

```bash
# Run full eval suite (all containers must be running)
cd stage3
~/.local/bin/pytest tests/ -v

# Run a specific category
~/.local/bin/pytest tests/test_rag.py -v
~/.local/bin/pytest tests/test_agent.py -v
```

## GitHub Actions

The workflow file is at `.github/workflows/ai-eval.yml`. Two jobs:

1. **build** — Validates Docker images build without errors
2. **validate-tests** — Installs pytest and validates test syntax

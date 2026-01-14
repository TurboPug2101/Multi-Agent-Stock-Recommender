# Testing Framework Documentation

## Overview

This directory contains the pytest testing framework for the AI Swing Trader backend. The framework includes unit tests, agent-specific tests, and integration tests with comprehensive mocking of external dependencies.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini              # Pytest configuration
├── unit/                   # Unit tests (max 2 tests per file)
│   ├── test_cache.py
│   ├── test_base_agent.py
│   ├── test_tool_registry.py
│   └── test_schemas.py
├── agents/                 # Agent-specific tests
│   ├── test_scouting_agent.py
│   ├── test_technical_agent.py
│   ├── test_sentiment_agent.py
│   └── test_strategist_agent.py
├── integration/            # Integration tests
│   ├── test_orchestrator.py
│   └── test_agent_workflow.py
└── fixtures/               # Test data and mocks
    ├── mock_data.py
    └── mock_responses.py
```

## Running Tests

### Install Test Dependencies

```bash
cd backend
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Agent tests only
pytest tests/agents/ -v

# Integration tests only
pytest tests/integration/ -v
```

### Run with Coverage

```bash
pytest tests/ -v --cov=. --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run Specific Test File

```bash
pytest tests/unit/test_cache.py -v
```

### Run with Markers

```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Skip slow tests
pytest -m "not slow" -v
```

## Test Configuration

### Environment Variables

Tests use mocked APIs by default. To use real APIs (for integration testing):

```bash
export USE_REAL_APIS=true
pytest tests/ -v
```

### Pytest Configuration

Configuration is in `pytest.ini`:
- Test discovery patterns
- Markers (unit, integration, slow, requires_api)
- Coverage settings
- Output options

## Test Fixtures

### Available Fixtures (in conftest.py)

- `isolated_cache`: Fresh cache instance for each test
- `mock_data_provider`: Mocked StockDataProvider
- `mock_groq_client`: Mocked Groq LLM client
- `mock_kite_client`: Mocked Kite trading client
- `sample_scouting_input`: Sample input for scouting agent
- `sample_scouting_output`: Sample output from scouting agent
- `sample_technical_input/output`: Technical agent samples
- `sample_sentiment_input/output`: Sentiment agent samples
- `sample_strategist_input`: Strategist agent input
- `mock_environment_variables`: Mocked env vars


## CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop` branches

GitHub Actions workflow: `.github/workflows/test.yml`

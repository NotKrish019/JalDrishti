# Jaldrishti Test Suite

---

## 1. Overview
This directory contains tests organized by scope and stability guarantees.

```
tests/
├── README.md
├── smoke/       # Rapid sanity checks (imports, health endpoints, scaffold presence)
├── contracts/   # JSON schema syntax and contract validity tests
└── integration/ # Cross-module orchestration tests
```

---

## 2. Running Tests
Run all unit and smoke tests using `pytest`:
```bash
pytest
```
Or run individual suites:
```bash
pytest tests/smoke
pytest tests/contracts
```

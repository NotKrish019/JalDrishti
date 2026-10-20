# Jaldrishti Integration Subsystem

**Owner:** Swastik Parmar (Backend / Integration / System Orchestration)  
**Primary Ownership:**
- `/backend`
- `/integration`
- `/tests/backend`
- `/tests/integration`

---

## 1. Overview
The Integration module ensures end-to-end coherence across the subsystems:
- End-to-end data pipeline assembly (Vision → Engineering → Knowledge → Backend → Frontend).
- Golden sample input/output fixtures for regression testing.
- Contract conformance validation verifying that all subsystem payloads satisfy schemas in `/contracts`.
- Mock harness and integration test runners.

---

## 2. Directory Layout
```
integration/
├── README.md
├── examples/  # End-to-end sample input/output payloads
├── fixtures/  # Reusable mock responses for local testing
└── tests/     # End-to-end cross-module integration tests
```

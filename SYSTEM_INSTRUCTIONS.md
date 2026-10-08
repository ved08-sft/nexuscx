# System Instructions

Always read /docs/icd.md for API schemas and /docs/tdd.md for test strategies before generating code. Follow Red-Green-Refactor TDD rules.

---

## Operational Mandates for AI Assistant

1. **Interface Contract Adherence:**
   - Always read [`/docs/icd.md`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/docs/icd.md) for exact API schemas, wire formats, payload fields, status codes, and WebSocket frame structures before writing API or integration code.

2. **Test-Driven Development (TDD Workflow):**
   - Always read [`/docs/tdd.md`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/docs/tdd.md) for test strategies, mock patterns, assertion specs, and runner commands.
   - Follow strict Red-Green-Refactor rules:
     - **RED**: Write a failing unit or integration test demanding the behavior first. Confirm failure reason.
     - **GREEN**: Implement minimal code to pass the test.
     - **REFACTOR**: Harden, type-check, lint, and split code without changing behavior or breaking tests.

3. **Continuous Memory Tracking:**
   - Constantly read and update [`MEMORY.md`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/MEMORY.md) (and [`MARKDOWN FILES/memoryNEXUS.md`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/MARKDOWN%20FILES/memoryNEXUS.md)) to track completed tasks, current active files, phase status, and activity logs.

# Ticket 003: Fix baseline version pydantic ollama cli and test suite

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-21

## Goal and scope

Fix baseline package metadata (`__version__ = "0.2.0"`, `__license__ = "Apache-2.0"`), Pydantic v2 deprecation warnings, Ollama SDK object normalization and env override, CSV/ProcessorEngine path/retry/health bugs, `__main__`/`cli` entrypoint flags, and all 15 failing unit/integration tests.

## Acceptance criteria

- [x] AC-01: All 44 baseline tests pass with 0 warnings and `./project/governance-check.sh` reports `GOV-PASS`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

<!-- ticket-radar:start -->
## Ticket Radar

Initial planned-scope estimate; advisory only, not execution or merge approval.

| Measure | Initial assessment |
| --- | --- |
| Impact score | 52/100 |
| Complexity | M |
| Estimated effort | 51 min |
| Planning budget | 30 min |
| Split recommended | yes |

Diagnostics: RADAR-ACCEPTANCE-MISSING, RADAR-BUDGET-EXCEEDED.
<!-- ticket-radar:end -->

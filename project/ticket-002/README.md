# Ticket 002: Add pyyaml runtime dependency

- **ID**: ticket-002
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-21

## Goal and scope

Declare `pyyaml = "^6.0.1"` in `pyproject.toml` under `[tool.poetry.dependencies]` so `ConfigGenerator` and `TaskValidator` have PyYAML available at runtime.

## Acceptance criteria

- [x] AC-01: `pyyaml = "^6.0.1"` is declared in `pyproject.toml` and `./project/governance-check.sh` reports `GOV-PASS`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

<!-- ticket-radar:start -->
## Ticket Radar

Initial planned-scope estimate; advisory only, not execution or merge approval.

| Measure | Initial assessment |
| --- | --- |
| Impact score | 44/100 |
| Complexity | M |
| Estimated effort | 48 min |
| Planning budget | 30 min |
| Split recommended | yes |

Diagnostics: RADAR-ACCEPTANCE-MISSING, RADAR-BUDGET-EXCEEDED.
<!-- ticket-radar:end -->

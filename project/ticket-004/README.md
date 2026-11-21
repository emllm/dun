# Ticket 004: Consolidate dune modules with uritime routing and bottlenecks fixes

- **ID**: ticket-004
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-21

## Goal and scope

Consolidate `emllm/dune` modules (`TaskConfigGenerator`, `TaskValidator`, `InteractiveMapper`, `SmartEnvManager`) with `uritime/autonom` BM25-lite lexical routing, canonical distribution/module mapping (`dun.packages`), `semcod/bottlenecks` fixes, `< 500`-line modular layout under `src/dun/`, CLI `route`/`config`/`validate` subcommands, and offline test/benchmark coverage into `emllm/dun`.

## Acceptance criteria

- [x] AC-01: All `src/dun/*.py` modules are `< 500` lines, Pydantic v2 only, zero bare `except:`, all baseline + consolidated tests pass with 0 warnings, offline benchmark passes, and `./project/governance-check.sh` reports `GOV-PASS`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

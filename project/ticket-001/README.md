# Ticket 001: Adopt native new-project governance

- **ID**: ticket-001
- **Owner**: Tom Sapletta (repository owner; requested 2026-11-21)
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-21

## Goal and scope

Owner request (2026-11-21): adopt native governance in emllm/dun and prepare to
consolidate useful features from emllm/dune into dun before publishing the next
release to PyPI under `dun`.

This ticket installs the published `wellmanifest/new-project` 0.20.166 package
(`c9bb73ce5ce861e78c26619e36e5b016fda56e2d`) over the legacy two-key Wellman
scaffold and makes the repository pass its own governance gate:

- managed governance files, hooks, allocator and lock from the pinned adopter;
- target seeds `VERSION`, `CHANGELOG.md`, `TODO.md`, `project/TICKETS.md`;
- `pyproject.toml` `[tool.wellmanifest]` block and pytest governance plugin
  (scope granted through `bootstrap_packaging_scope.py`), plus the owner's
  pending metadata correction (Apache-2.0 licence matching `LICENSE`);
- Docker declared required; external images pinned to SHA-256 digests;
- `VERSION`/`pyproject.toml` aligned with the primary static `__version__` 0.2.0 in
  `src/dun/__init__.py` (line 16; cleanup of duplicate line 49 belongs to follow-up application ticket).
- `.governance/poa.json`: descriptive release plan for the dun package;
- `errors/**` assigned to the integration workstream (wellmanifest/logs catalog).

Scope amendment (2026-11-21, owner-approved plan): `allowedPaths` extended with
the adoption seeds and bindings the gate reported (`.gitattributes`, `.gitignore`,
`CHANGELOG.md`, `VERSION`, `Dockerfile`, `docker-compose.yml`). Optional root
seeds `project.sh`/`project.bat` are omitted to stay within the L budget.

Non-goals: product behaviour changes, dune code merge, PyPI publication.

## Acceptance criteria

- [ ] AC-01: `./project/governance-check.sh --base origin/main --head HEAD` reports GOV-PASS.
- [ ] AC-02: `wellman check` reports no governance errors beyond missing docs/errors indexes (next ticket).

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

<!-- ticket-radar:start -->
## Ticket Radar

Initial planned-scope estimate; advisory only, not execution or merge approval.

| Measure | Initial assessment |
| --- | --- |
| Impact score | 48/100 |
| Complexity | M |
| Estimated effort | 44 min |
| Planning budget | 30 min |
| Split recommended | yes |

Diagnostics: RADAR-ACCEPTANCE-MISSING, RADAR-BUDGET-EXCEEDED.
<!-- ticket-radar:end -->

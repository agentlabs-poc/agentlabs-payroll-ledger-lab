# Three-ledger simulation implementation plan

> For agentic workers: use superpowers:subagent-driven-development. Existing user authorization selects Sol-medium coding and the existing Lab PR; do not request a new execution choice.

**Goal:** Execute the approved four-table L1 design and export every required canonical row kind with a complete relationship map.

**Architecture:** Three monetary ledger tables plus typed immutable `payroll_l1_records`; L2 settings remain in `payroll_l2_records`. Python stdlib SQLite proof only. Exact-key references and atomic named operations preserve the existing integrity tests.

**Spec:** [Three-ledger design](three-ledger-simulation.md). This supersedes the old nine-table plan. Base before this task is recorded in the controller ledger after committing the design pin.

## Global constraints

- Work only in the lab checkout on `docs/payroll-handbook-compat`; no production code/API/CLI, browser dependencies, deployments or migrations.
- Exactly five physical tables: `payroll_draft_ledger`, `payroll_ledger`, `payroll_employer_liability_ledger`, `payroll_l1_records`, `payroll_l2_records`. No legacy-table compatibility views.
- KV envelope remains `tenant,key,value,ts,state`; no L3. Keys use approved dotted types, colon separators, backslash escapes only for literal colon/backslash within IDs; opaque case, strict parsing, numeric revisions.
- Preserve all existing tested integrity guarantees, one-employee atomic commit, integer minor units, optional review, holds, expiry, stable consumption and durable replay. No generic L1 writes or cross-employee bulk writes.
- Employer contribution increases both gross and deductions. Obligations, remittances and allocations are immutable typed rows in the one employer ledger, with exact references, proof and allocation caps.
- Root owns `docs/`, root README and PR metadata. Implementer owns only `sqlite_lab/` and any strictly necessary artifact ignores. No implementation worker subagents.
- This changes only disposable SQLite databases. Refuse opening old nine-table databases with a clear incompatible-prototype error; never silently migrate existing user files.

## Task 1: executable three-ledger model and complete row export

**Files:** modify `sqlite_lab/schema.sql`, `records.py`, `payroll.py`, `prove.py`, `test_records.py`, `test_payroll.py`, `README.md`. A small focused catalogue/export module and its tests may be added if needed; no framework.

**Interfaces:**
- Keep `Payroll(connection,tenant,actor)`, component/control/review/commit/ELR named operations and existing canonical key helpers.
- Add `define_earning(earning_id, revision, employee_id, component_key, amount_minor, effective_from, effective_until=None)` returning its L1 row. This explicitly creates the prototype earning entitlement; `create_draft` must not invent entitlement from a scalar amount.
- Use `create_draft(draft_id, employee_id, payroll_month, earning_keys, instruction_version_ids)`; remove the redundant calculation ID from the new canonical contract. Draft metadata uses `payroll.draft:<draft-id>:1` for one fixed snapshot; rebuild with another opaque draft ID.
- Retain instruction creation/version operations, now backed by full versioned `payroll.instruction` records with opaque version ID uniqueness and stable consumption identity. Keep complete component-version references, employee, cadence and bounds on each version.
- `run_proof(output_dir=None)` continues reporting measurements and gaps. With an output directory it also writes `canonical-rows.json` (every actual row grouped by the five tables) and `canonical-catalog.json` (one stored example per required kind plus meaning, identity, references, validation and indexed queries). No DB overwrite.
- Catalogue coverage is exactly nine L1 record types, one L2 type, and five ledger row kinds as listed in the spec. Source prototypes may retain targeted validation rather than claim full JSON Schema. Catalogue must match actual required fields, no placeholders.

### Steps and checks

- [ ] Add failing tests for exact five-table topology, source records and fixed draft metadata. Retain the literal RED output.

```python
names = {row[0] for row in connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
self.assertEqual(names, {
    'payroll_draft_ledger', 'payroll_ledger', 'payroll_employer_liability_ledger',
    'payroll_l1_records', 'payroll_l2_records'})
```

- [ ] Replace old tables with exact-key parent references to L1 and typed employer-ledger references. Reference types must agree (an earning key cannot stand in for draft metadata). Keep schema-level constraints/triggers for key/type/amount references and semantic uniqueness where feasible; authoritative wrapper transaction checks remain required.
- [ ] Extend the registry for `payroll.earning`, `payroll.instruction`, `payroll.draft`, preserving the existing six L1 types plus L2 settings. Add explicit partial/expression indexes for instruction opaque version IDs, employee/effective-month selection, draft identity, numeric revision, stable consumption and receipt replay. Canonical key/payload identity must agree; same employee/month does not imply one allowed payroll.
- [ ] Update named operations and existing tests to canonical sources/ledgers. Keep immutable source versions and exact draft references. Persist committed authority in receipt/posted evidence rather than mutable calculation status. Earnings validate component/employee/effective-month applicability; instructions resolve their monetary direction from component kind. An earning instruction adds to gross, a deduction reduces net, and employer contribution adds matching gross/deduction effects.
- [ ] Run a connected E101 fixture with earning salary5,000,000 and employer contribution300,000 plus monthly loan200,000. Assert literal totals and liability allocations:

```python
self.assertEqual((draft['gross_minor'], draft['deductions_minor'], draft['net_minor']),
                 (5_300_000, 500_000, 4_800_000))
self.assertEqual(payroll.elr_outstanding('OB1'), 100_000)  # after 200,000 allocated
```

- [ ] Preserve positive/negative tests for atomic rollback, reopen/replay, changed retry, competing commits, stale controls, optional approval/hold, exact history, disabled-current behavior, component uniqueness, escaped L1/L2 lookups, monthly expiry, stable one-time consumption across versions, and employer totals. Add a one-time earning/bonus case to verify direction and consumption, plus cross-type/tenant refs, duplicate source identity and over-allocation (including one remittance spanning obligations).
- [ ] Export actual rows and catalogue after the proof journey. Assert every required type/kind is witnessed, full examples agree with registry/schema and foreign references resolve within exported data (employee/actor/policy external references are labeled). Keep the original 16 supporting-role map and explicit HTTP replay gap, and add the former nine-table replacement map.
- [ ] Record representative actual query plans for source current/effective selection, draft/posted employee-month, ELR outstanding/allocation, applications and replay. Report fixture times/row counts/DB and index bytes without extrapolating scale. Do not add performance changes unrelated to the topology.
- [ ] Run `python3 -m unittest discover -s sqlite_lab -p 'test_*.py' -v`, `python3 -m py_compile sqlite_lab/*.py`, a fresh `python3 -m sqlite_lab.prove --output-dir <new-directory>`, and `git diff --check`. Document exact commands, source limitations and retained RED/GREEN paths.
- [ ] Self-review; commit only owned task files and report commit, suite count, proof directory, catalogue coverage and gaps. Do not push; root reviews and pushes existing PR.

## Controller completion

- [ ] Commit/push design pin before simulation edits.
- [ ] Reconcile Lab/Core current canonical inventories and add readable Mermaid relationship map while implementation runs.
- [ ] Independent scoped spec/quality review against the task diff; implementer resolves concrete correctness findings.
- [ ] Independently run final suite and proof. Retain source-bound complete rows, catalogue and evidence under a new evidence directory; preserve prior proof as historical evidence.
- [ ] Verify documentation examples/links and map coverage; final aggregate review; commit/push existing Lab #1 and Core #190. No merge or production readiness claim.

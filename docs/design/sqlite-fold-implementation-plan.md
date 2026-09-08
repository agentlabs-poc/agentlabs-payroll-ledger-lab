# SQLite payroll record folding implementation plan

> For agentic workers: use superpowers:subagent-driven-development. Implement only the lab proof below; production Core code is out of scope.

**Goal:** Demonstrate the 16 existing supporting roles in one `payroll_l1_records`
store, with L2 employee settings and no software-provided L3 store.

**Architecture:** Python standard-library wrappers over an isolated SQLite
database. Core canonical tables retain authoritative ledger identities/money;
supporting JSON records use one L1 table. L2 uses its own table. Consumers own
L3 composition and persistence. This is executable prototype evidence, not a
production-compatible migration or a complete recreation of historical APIs.

**Tech stack:** Python 3, sqlite3 (local SQLite 3.46.1 with JSON functions),
unittest; no added third-party dependencies or HTTP server.

**Spec:** [123 Architecture](123-architecture.md), [record design](payroll-records.md),
[SQLite proof sequence](sqlite-proof-plan.md), as corrected by the latest user
instruction: software provides L1/L2; L3 belongs to consumers.

## Global constraints

- Only the payroll lab is an implementation target. Core updates are docs only.
- Existing Lab #1 carries the work; no new PR, branch merge, live data or deployment.
- Use `tenant`, `key`, `value`, `ts`, and prototype `state` columns for each KV table.
- No L3 table, L3 mutation API or generic unrestricted L1 write method.
- Preserve one-employee atomic commit; no cross-employee bulk writes in L1.
- Monetary amounts use integer minor units; no float arithmetic. JSON examples
  may render decimal strings, but conversions must be exact.
- Prototype choices are documented assumptions, not approved production schemas.
- Test real temporary SQLite files, transactions and competing connections;
  assert observable behavior and literal expected amounts, not source text.
- Core's 16 old supporting tables must not be recreated under new SQL names.
- Do not change the browser app, its dependencies or production services.

## Task 1: executable consolidation proof

**Files:** create `sqlite_lab/schema.sql`, `sqlite_lab/records.py`,
`sqlite_lab/payroll.py`, `sqlite_lab/prove.py`,
`sqlite_lab/test_records.py`, `sqlite_lab/test_payroll.py`, and
`sqlite_lab/README.md`. A small `__init__.py` is allowed. Add only necessary
Python/artifact ignores to `.gitignore`. Root controller owns `docs/` and PR text.

**Interfaces:** keep storage/key validation in `records.py`, domain operations in
`payroll.py`, and consumer composition/measurement in `prove.py`. Use a scoped
`Payroll` wrapper taking a SQLite connection, tenant and actor. Expose named
component, instruction, draft/control/review, commit and ELR operations. Generic
reads and L2 settings writes are permitted; generic L1 writes remain private
implementation mechanics. No production REST/CLI contract is implied.

### Prototype contract choices

Use canonical key tokens and `<type>/<subject>/<record>` construction. Accept
only an explicitly validated separator-safe identifier grammar in this proof;
preserve opaque case. Version records use positive integer revisions validated
against JSON identity and ordered numerically. Reject unknown type/fields where
the prototype schema defines a closed payload. Required values cannot be null.
Replay identity includes tenant, actor, operation and subject; the same retry
with changed input fails. Do not use timestamps as identity.

Components use immutable definition/control revisions. Disabling creates a
new state revision; it must not revive older enabled revisions. Availability
changes to commit/application receipts are disallowed. New components are
tenant-owned in this first proof; platform-shared definitions are a recorded
gap. No artificial workflow/maker-checker requirement is imposed.

Keep prototype representations of the nine already-designated tables:
`payroll_instructions`, `payroll_instruction_versions`, `payroll_calculations`,
`payroll_calculation_revisions`, `payroll_draft_entries`,
`payroll_ledger_entries`, `payroll_statutory_obligations`,
`payroll_statutory_remittances`, `payroll_statutory_allocations`.
Use small columns sufficient for the scenario, enforced tenant-aware references
and immutable committed facts. Draft candidate identity/content hash belongs on
the canonical draft revision. Do not invent an accepted Salary Earning Ledger
table: salary entitlement is an external fixture input, explicitly scoped.

In `payroll_l1_records`, implement the reviewed candidate roles: component
definition, draft control, exact-content review, instruction resolution with
draft effects, committed application with posted effects, and operation receipt.
The receipt carries canonical request identity/hash, outcome, actor and required
before/after evidence. Records representing the same operation share evidence;
do not manufacture six receipts solely to resemble the six former evidence
tables. Exact HTTP response replay is a transport-adapter gap, not implemented
HTTP support.

In `payroll_l2_records`, support `payroll.employee.settings` as explicit employee
preferences (locale) and a policy reference, with revision/effective-month
validation. A policy reference is opaque until an auxiliary policy contract
exists; do not claim its external referent has been proved. No salary/deduction
facts or transient consumer workflow state belong in settings.

### Implementation and validation steps

- [ ] Write failing tests for keys, scope separation, JSON schema agreement,
  numeric revision ordering (2 versus 10), duplicate identity, effective versus
  current settings and disabled-current behavior. Run them and retain RED output.
- [ ] Implement schema plus minimal record wrapper. Enable and verify foreign
  keys per connection; validate JSON object payloads and create a small set of
  actual-query-driven expression/partial indexes with canonical predicates.
- [ ] Add failing payroll tests before domain implementation. Use E101 November
  2026 salary 5,000,000 minor units and loan deduction 200,000, expecting net
  4,800,000. Loan applies Oct 2026 through Feb 2027; test endpoints and expiry.
  Use a separate one-time fixture for consumption tests. Test fixed draft,
  optional approval, hold/release, exact review binding and commit.
- [ ] Implement a transactionally complete employee commit: posted entries,
  instruction applications/effects and permanent outcome receipt together.
  Validate draft/posted effect links in the same transaction. Use protected
  transaction entry (e.g. BEGIN IMMEDIATE) and expected-revision checks for races.
- [ ] Demonstrate payroll-backed ELR outstanding before remittance and reduced
  balance after explicit allocation; reject over-allocation. Use a separate
  balanced employer-contribution fixture so the simple salary/loan totals remain
  as specified. No accounting/bank workflow is implemented.
- [ ] Prove rollback on an injected storage failure, reopen durability, duplicate
  and changed retries, two competing connections committing one draft, stale
  control updates and cross-tenant reference rejection. Failure injection belongs
  in tests (e.g. temporary SQLite trigger), not a public domain API flag.
- [ ] Run the full focused suite with
  `python3 -m unittest discover -s sqlite_lab -p 'test_*.py' -v`.
- [ ] Make `python3 -m sqlite_lab.prove` create an isolated temporary file, run a
  representative journey and emit JSON containing outcomes, per-stage timings,
  SQLite/Python versions, row counts, relevant query plans, database/index space
  where measurable, and a literal 16-role mapping to witnessed records or
  explicit gaps. Provide an optional output directory for retained evidence.
  Refuse accidental reuse/overwrite of an existing user database.
- [ ] Document commands, exact prototype assumptions and unresolved PostgreSQL/
  HTTP/global-definition/salary-source gaps in `sqlite_lab/README.md`. Do not
  report complete production folding or performance improvements.
- [ ] Self-review for minimality and real failure assertions, run `git diff
  --check`, commit only task files and report test/measurement evidence.

## Task 2: approved canonical key grammar

The user's subsequent approval supersedes Task 1's provisional slash syntax.
Use `<type>:<subject>:<record>`, dot-separated registered type tokens, and
backslash escaping only for literal colon/backslash within identity segments.
Preserve opaque case; reject malformed/unknown/unnecessary escapes and empty
segments. Keep canonical numeric revision identity and numeric ordering.

Scope is `sqlite_lab/` only. Update shared construction/parsing, query/index
predicates and examples. First demonstrate failing round-trip, invalid encoding,
key/payload agreement and end-to-end escaped-identity tests; then implement and
run the full focused suite/prover. Keep all other prototype choices unchanged.
Root owns design docs. Commit locally; no production edits, push or new PR.

## Controller review and completion

- [ ] Correct Lab/Core design docs for consumer-owned L3 while coding runs.
- [ ] Review the implementer's exact diff for spec compliance and code quality;
  fix correctness gaps through the implementer and re-review the changed scope.
- [ ] Independently execute the proof, retain its measured result and update the
  lab's 16-role disposition with demonstrated versus unproved guarantees.
- [ ] Perform final scoped review, push existing branches and report the lab
  result without claiming production compatibility or merging any PR.

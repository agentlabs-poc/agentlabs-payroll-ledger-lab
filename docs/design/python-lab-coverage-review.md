# Python payroll lab: use-case and boundary review

Review date: 2026-09-09. Runtime baseline: `5dd02ba`.

This reviews the Python CLI/in-process SQLite reference against the current
three-ledger design and subsequent canonical decisions. It does not certify
production Go/PostgreSQL implementation or all possible payroll policies.
The review found material gaps. The five reproduced defects below were then
fixed at the user's request. The explicit unimplemented items remain outside
that correction; passing tests do not establish complete production conformance.

## Fix verification

All **58 test methods pass** after the corrections (0.510 seconds in the root
verification run). The five original defect descriptions below are retained as
history, with executable checks now passing.

- Commit finality uses durable commit evidence, including drafts with no monetary
  rows. Same-request replay remains available.
- Commit checks stable instruction consumption across cadence changes inside
  the existing transaction. No new bulk operation or cadence-policy API was added.
- Commit, hold/release, review and component-disable control inputs enforce
  boolean flags and positive integer revisions without boolean coercion.
- Existing database acceptance compares tables, indexes, triggers and their
  normalized definitions against the current `schema.sql`, before reset writes.
  This intentionally remains a prototype compatibility check, not a migration.
- Catalogue validation checks payable existence, receipt ownership/membership,
  draft identity and the exact component's payable classification.

The benchmark verifier now derives net from actual posted gross minus deductions,
rather than copying the expected net into the measured result. The 3,000-employee
run was stopped at the user's request; a fresh 100-employee run replaces it.

## Scope and evidence

The current model has exactly three monetary ledgers, `payroll_l1_records`, and
`payroll_l2_records`. L1 contains individual domain operations; L2 contains
auxiliary employee settings. Consumer scripts own L3 sequencing and policy
choices. There is no supplied L3 table or bulk L1 write.

Initial verification ran 43 existing tests: 42 passed and one errored because a
negative catalogue test still searched for the obsolete singular receipt field
`employer_liability_entry_id`. That assertion did not run. New boundary tests
retain failing assertions openly; a reproduced defect is not marked as passed.

Pre-fix review verification: **58 test methods, 53 passing and 5 failing methods**,
with 8 failure reports because the malformed-control test has four subcases.
There were no test errors. The complete run took 0.747 seconds. Fifteen focused
test methods were added. The obsolete catalogue fixture was corrected; its new
generic-payable reference check exposes an additional validation gap.

Run the evidence again with:

```sh
python3 -m unittest discover -s sqlite_lab -p 'test_*.py' -v
```

## Original review use-case map

Gap assessments in this table describe the pre-fix review. The fix verification
above supersedes the five defect statuses.

| Area | Evidence | Assessment |
|---|---|---|
| Five physical tables and separate L1/L2 ownership | `test_records.py` topology and layer tests | Covered |
| Canonical employee ownership, escaping, arity and numeric revisions | `test_records.py`; employee reuse and cross-owner tests in `test_payroll.py` | Covered |
| Exact component versions and immutable source facts | Component identity, source revision and reference tests | Covered |
| Inclusive monthly expiry; future revisions; disabled replacement | Effective-source and expiry tests; six-month demo | Covered |
| One-time consumption across versions | Existing test plus `test_payroll_edges.py` | Normal repeated consumption rejected; cadence-change bypass reproduced |
| Draft monetary snapshot and employee/month association | Draft tests and ledger reference constraints | Covered; multiple drafts per employee/month are permitted |
| Optional source reconciliation versus retained draft authority | Six-month demo and new addition-only edge test | Covered, including a newly added source without replacement |
| Hold, release, cancellation and exact/fresh approval | Control tests and six-month demo | Monetary drafts covered; zero-line finality gap |
| Commit replay, changed retry and rollback | Commit tests, injected receipt failure and two-connection test | Covered within the tested SQLite cases |
| Corrections reference an earlier employee payroll | Six-month demo and new correction edge test | Earlier reference accepted; wrong owner/month/missing reference rejected |
| Employer contributions balance gross and deductions | Connected totals test and Karnataka CLI walkthrough | Covered |
| Employee statutory deductions become authority payables; loan does not | Karnataka CLI walkthrough and new payable edge test | Covered; not a complete tax/eligibility engine |
| Unpaid ELR obligations, proof-bearing remittance and explicit allocation | Existing ELR tests and new payable edge test | Covered, including authority mismatch and allocation cap rejection |
| Effective L2 settings; old/new tax regime data | Settings tests and both Karnataka walkthrough modes | Covered for the supplied fixture and supported settings contract |
| Natural CLI, config precedence, tenant reads and malformed input | `test_cli_contract.py` | Additional coverage; commit type-validation defect |
| One-command reset, preserving config and refusing foreign data | `test_cli_contract.py` | Ordinary cases covered; same-name foreign schema defect |
| Catalogue reference closure | Corrected negative catalogue fixture plus new generic payable case | Employer-liability reference check passes; missing generic payable reference is accepted |
| 3,000 employees and one month | Separate running benchmark | Pending; volume is not proof of edge-case correctness |

## Reproduced defects, now fixed

1. **Commit accepts wrong JSON types.** A boolean control revision compares
   equal to integer revision 1. Policy flags are coerced with `bool(...)` or
   used for truthiness. Tests reproduce accepted `true` as a revision, `0` as
   `approval_required`, `"false"` as `reconcile_sources`, and `1` as
   `fresh_review_required`. L1 must validate the declared input types before
   interpreting controls or forming the replay request.
2. **Reset identifies a database only by table names.** An unrelated database
   containing the five expected names with incompatible columns is accepted and
   cleared. The ordinary foreign-table rejection works, but does not establish
   that the schema belongs to this lab. The compatibility guard needs stronger
   structural evidence before a destructive reset.

3. **An empty committed draft is not terminal.** The draft and receipt can exist
   without any monetary rows. Finality checks only look for posted monetary
   rows, and a subsequent review is accepted. Deriving finality from durable
   commit evidence preserves the accepted ledger model without inventing a
   prohibition on zero payroll. Additional control/recommit checks in the test
   sit after the first failing assertion; they are not independently passing proof.
4. **Cadence change bypasses one-time consumption.** The test commits a one-time
   instruction, revises the same stable identity to monthly, and successfully
   commits it again in December. Separate cadence-specific uniqueness indexes
   do not enforce prior one-time consumption across that change. Stable identity
   must retain its consumption evidence; the appropriate revision acceptance
   rule should be made explicit without moving loan policy into L1.
5. **Catalogue validation omits generic payable references.** Replacing a commit
   receipt's `payable_entry_ids` member with `MISSING` does not make `_catalogue`
   reject the exported evidence. The existing plural employer-liability check
   does reject a missing reference once the stale test fixture is corrected.
   This is an evidence-validation defect, not a demonstrated posting loss.

CLI failures are executable in `sqlite_lab/test_cli_contract.py`; finality and
consumption failures are in `sqlite_lab/test_payroll_edges.py`. These tests use
disposable databases. No user database was cleared by the review.
The catalogue failure is in the existing `sqlite_lab/test_payroll.py`.

## Explicit unimplemented items and policy boundaries

- Generic `key1`–`key10` storage columns are a preview, not the physical schema.
  The current benchmark measures serialized keys and existing expression indexes.
- Prefixed Base36 Snowflake IDs are pinned, but generator coordination, clock
  handling and conversion of derived IDs are not implemented or proved.
- Actor attribution is not production permission enforcement. This local demo
  has no auth-service permission tests, PostgreSQL RLS or production migration proof.
- Employee/component earning cardinality remains an explicit open decision.
  Do not add a uniqueness rule silently.
- Conflicting reviews have no pinned effective-decision rule. Current approval
  lookup accepts any matching approval. Do not invent organization policy in L1.
- The prototype rejects negative net. Carry-forward, recovery decisions,
  attendance interpretation, tax eligibility and after-exit accounting are not
  silently promoted into L1 by this review.
- Hardware failure, disk exhaustion, process-crash recovery, broad concurrency,
  arbitrary statutory situations and complete production security remain unproved.

## Benchmark integrity

The original 3,000-employee subprocess benchmark ran against unchanged runtime
files in a separate workspace-disk database until the user stopped it. That review
added only tests and documentation. Small test executions shared the host, so it was
not an isolated-machine performance measurement. The CLI boundary run occurred
at approximately 02:09:50 IST and took under one second. The payroll edge run
at approximately 02:13:21 IST took 0.058 seconds. The root verification of all
15 new tests took 0.290 seconds. Per-command resource
measurements do not include the separate review processes.

Runtime fixes were applied only after the 3,000-employee process stopped.
Changing imported runtime files during a subprocess benchmark would mix
implementations in one result; the replacement run uses the fixed code throughout.

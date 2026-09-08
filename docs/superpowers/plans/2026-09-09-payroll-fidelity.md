# Payroll simulation fidelity implementation plan

> Use superpowers:subagent-driven-development. User selected Sol-medium coding and approved fixing the studied gaps. Continue on the existing Lab PR; no new PR or production changes.

**Goal:** Make the actual SQLite rows and chronological HTML faithfully demonstrate canonical employee ownership, source applicability, draft finality, selected policy and multi-month payroll/liability behavior.

**Architecture:** Exactly three monetary ledgers plus one payroll L1 record store and one L2 store. Python standard-library SQLite domain operations; consuming Python code chooses workflow and supplies business amounts. HTML reads exported actual rows and previews decoded key columns. No L3 store, Layer-1 batch writes, new service or dependencies.

**Spec:** [Fidelity study](../../design/simulation-fidelity-review.md), [canonical identity contract](../../design/canonical-identities.md), Core payroll-operation-contracts and hrms-payroll-policy chapters.

**Latest user constraint:** this is demo work; do not expand regressions or run
extended review cycles. Validate by executing the actual walkthrough, checking
canonical keys, money and meaningful transitions, and building the HTML. The
original regression/review checklist below is superseded by this narrower
validation workflow; completed checks may be retained, but they must not delay
the working demonstration. Keep necessary compatibility edits small.

**Baseline:** Lab 5d421f6 on docs/payroll-handbook-compat. Only disposable fresh SQLite databases; no migration of user data. Root owns docs/ and diagrams; implementers own assigned code/tests/exports. No implementation worker subagents.

## Execution decisions and rationale

- Canonical employee ownership is required for every employee-owned record family, not only earnings. Retain existing local subject IDs and revisions; owner scope removes collisions without prescribing a generator or an employee/component cardinality policy.
- Use registered type tokens and escaped opaque identity fields. Preserve JSON representation and existing value fields; optional correction metadata is a domain requirement, separate from key storage projection. Do not introduce two independently writable identities.
- Source authority for a payroll month is the highest numeric revision whose effective_from is not later than that month, within tenant/employee/local source identity. Then check state and effective_until. Never fall back past an eligible disabled or expired replacement. Future-dated versions therefore do not disable an earlier applicable version prematurely. This implements applicable facts for the requested month; it does not mutate historical payroll.
- Reconciliation is an optional protected comparison of the full accepted employee-period source basis, including applicable additions, captured with the fixed draft. The canonical basis consists of current period-effective earning/instruction keys and relevant component availability, not external source origins or business overlap inference. The producer still chooses monetary inputs and whether to require this broad freshness guard. Store the basis evidence in existing draft metadata; no extra record type/table. Both fixed-draft authority and reconcile/rebuild must be shown.
- Approval must bind exact draft money. Whether hold/release requires a fresh approval is selected by the consumer; terminal cancellation and posted finality never vary.
- Corrections use an optional prior-posted-entry relation on a supplied one-time instruction. Validate same tenant/employee, committed referent, and strictly later payroll month at draft/commit boundaries. Do not invent recovery amounts, restore consumption or model after-exit correction inside payroll.
- Employer/remittance correspondence uses supplied employer, authority and currency scope. Period information must be retained, but cross-period allocations are not universally forbidden. No automatic allocation priority or statutory formulas.
- Physical key1–key10 migration/performance measurement is separate from these fidelity fixes. Preserve the working serialized-key SQLite store for this task and keep the decoded-column preview accurate. Do not silently claim physical partitioning or faster execution.

## Canonical serialized identity map

Tenant and owning store scope every row. Dots split registered namespace tokens; colons split identity fields. Literal colons/backslashes in opaque IDs keep the existing escape grammar; dots inside opaque IDs remain literal.

| Record type | Identity fields after the type |
|---|---|
| payroll.component | component_id, revision |
| payroll.earning | employee_id, earning_id, revision |
| payroll.instruction | employee_id, instruction_id, revision |
| payroll.draft | employee_id, draft_id, revision |
| payroll.draft.control | employee_id, draft_id, revision |
| payroll.draft.review | employee_id, draft_id, review_id |
| payroll.instruction.resolution | employee_id, draft_id, resolution_id |
| payroll.instruction.application | employee_id, instruction_id, application_id |
| payroll.operation.receipt (current employee operations) | employee_id, subject_id, receipt_id |
| payroll.employee.settings | employee_id, revision |

All used identity fields must agree with their JSON or exact referenced owner. Employee operations require explicit employee scope, including draft lookup/control/review/commit and instruction versions. Stable monetary row IDs must distinguish identical local draft IDs across employees. Current receipts are employee operations; do not invent a tenant-wide ELR receipt variant without a concrete need.

## CP1 — identity and period-effective sources

Owner: one Sol-medium implementation worker; sqlite_lab/ and necessary current fixture regeneration. Browser decoder adaptation can run independently from this map.

- [ ] Add failing regression cases for two employees reusing local earning/instruction/draft IDs, mismatch rejection, independent revision histories and future-effective source selection.
- [ ] Implement shared canonical key parsing/encoding from the map. Prefer one registry/helper to per-type parser copies. Reject old employee-less forms; update callers, source regeneration, exact refs, consumption/retry scopes, fixture/catalogue keys and stable monetary IDs.
- [ ] Scope history/current/effective lookup by tenant and employee where required. Enforce authoritative eligible revision and no disabled/expired fallback. Preserve immutable source history, exact draft/posted reference triggers and integer money.
- [ ] Update existing tests and catalogue reference closure to employee-qualified identities. All kinds and all exact reference edges must still resolve.
- [ ] Run relevant RED/GREEN tests, full SQLite suite and Python compile after changes settle. Regenerate current demo through actual operations. Commit owned files and report commands/results.
- [ ] Independent task review; fix only concrete correctness findings before CP2.

## CP2 — lifecycle, corrections, policy and liabilities

Depends on CP1. Owner: Sol-medium implementation worker; sqlite_lab/.

- [ ] Regress and fix terminal cancellation; reject controls/reviews on posted drafts; retain harmless committed replay without changing historical money.
- [ ] Regress and fix identical instruction-version retry before next-revision rejection. Changed retries fail; employee/executor scopes stay explicit.
- [ ] Capture the complete current employee-period source basis at draft creation and compare it inside commit's write transaction when freshness is requested, detecting additions, replacements and availability changes. Test newly added applicable sources, not only changed selected revisions. Preserve fixed-draft commit after source changes. Consumer can require exact approval and select fresh-control versus retained exact-content approval.
- [ ] Add optional supplied correction relation without another table/type. Regress same-month/earlier-month/cross-employee/uncommitted-reference rejection and later-month one-time correction. Old payroll and consumption remain immutable.
- [ ] Return the complete employer-liability posted-entry set. Preserve exact obligation provenance and full amounts. Retain supplied employer/authority/currency and reporting context in liability/remittance records; validate scope compatibility and caps for explicit allocations without a mandatory same-period rule.
- [ ] Cover multiple contributions, shared remittance, wrong-scope allocation, partial outstanding and complete closure. No new batch writes or accounting operations.
- [ ] Run focused regressions plus full suite after changes settle; commit and independent review.

## CP3 — actual multi-month walkthrough, UI and evidence

Depends on CP2. Backend demonstration worker owns demo/prove/tests/public JSON; separate UI worker owns src/ and UI checks. Root owns docs/diagrams.

- [ ] Two employees reuse local IDs safely. Show manager-supplied amounts, shared Basic/HRA definitions, employee earnings, monthly allowance, finite loan, one-time earning and deduction.
- [ ] Chronological actual-row journey covers October through March: five loan applications October–February; none in March; December earning replacement; November one-time event; linked December correction. Include hold/exclude/release, cancellation/rebuild, selected reconciliation versus fixed snapshot, and instruction/commit retry outcomes.
- [ ] Keep business policy in the consuming script; every employee commit is a separate primitive operation. After-exit correction is explicitly an external-accounting handoff, not a fabricated payroll write.
- [ ] Multiple employer liabilities and explicit allocations demonstrate partial outstanding and full closure. All snapshots have complete reference closure and money assertions; do not make the fixture pass by hand-editing exported JSON.
- [ ] UI derives employee/month context from each stage; no hardcoded E101/November totals for a multi-month flow. Original canonical JSON remains expandable; key1–key10 preview uses corrected keys. Preserve chronological append ordering and bounded readable layout.
- [ ] Update canonical definitions, row map, diagrams and handbook mirrors from final actual structures. Remove obsolete pending warnings only where executable evidence proves the fix.
- [ ] Verify full SQLite suite, decoder checks, UI build, fresh proof catalogue and source hashes. Browser compare every displayed stage/row to actual snapshots, desktop/mobile layout and controls. Retain final evidence separately from historical runs.
- [ ] One aggregate review against all eight findings and this plan. Resolve real defects, update existing Lab/Core PR descriptions, commit/push. No merge or production-readiness claim.

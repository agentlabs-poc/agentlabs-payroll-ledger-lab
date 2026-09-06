# Local implementation reconciled with the Layer-1 handbook

Reviewed 2026-09-06 at the user's request. **Retain three fixes directly; reshape
three before integration. The local branch is not ready to merge as a unit.**
This is a source-backed disposition of existing work, not a production change,
new organizational policy, or claim that every Core contract has been audited.

## Baseline and why the implementation needs reconciliation

| Evidence | Pinned revision and meaning |
|---|---|
| Core remote main | `3a87931ea536c8b617e6e391c14affd03ade9f65`, rechecked through GitHub during this pass; already contains the merged payroll Layer 1 |
| Local Core candidate | `fix/payroll-ledger-schema` at `01268e541011db15f448b9e9020f3191779c2125`; last code change `5bc0b1a115295ce1c7ecd01b845702610d209f75`; unpushed and unmerged |
| Layered handbook used for comparison | `e4c8d3a`, particularly [Layer-1 contracts](layer-1-contracts.md), [HRMS payroll policy](hrms-payroll-policy.md) and [PAY-ARCH-006 rationale](payroll-policy-boundary.md) |
| Original findings | [PAY-DB-001–006](database-table-review.md), describing Core; the browser demo's PAY-GAP register is a separate comparison |

The implementation began with six actual database/behavior findings against
Core main. It then implemented more than table corrections: contribution
production, settlement APIs, employee review/finalization, batch transaction
handling, authorization wiring and tests. The resulting difference is 45 files,
7,564 insertions and 71 deletions, with migrations 92–95 and six new tables.

The earlier design treated reconciliation and a specific approval workflow as
mandatory. PAY-ARCH-006 subsequently located those choices in organizational
policy. That distinction changes the disposition of some working code; passing
the earlier tests does not resolve it. Existing code safeguards remain in force
until reviewed replacements are implemented. PAY-Q-020 remains superseded.

## Disposition of the six original findings

“Retain” means the change still has a sound contract and rationale. It does not
mean it has been merged or that later integration needs no verification.

| Finding | Disposition | What fits, and what must change |
|---|---|---|
| PAY-DB-001 — employer-liability register | **Retain structure; reshape classification** | Separate immutable obligations, proof-bearing remittances and explicit allocations represent partial settlement correctly. Keep exact posted authority, one liability per represented contribution pair and bounded allocations. The new SQL/Go hardcodes PF/ESI/PT/TDS and PT state selection; isolate that country mapping from the generic register contract. |
| PAY-DB-002 — employer contribution in gross | **Retain outcome and integrity; reshape production** | The agreed earning/deduction pair gives gross 51,000 and net 50,000 for salary 50,000 plus contribution 1,000. Keep balanced pair validation, reports and one liability basis. Make pair creation an explicit producer proposal or declared mechanical operation; the current automatic conversion from component classification embeds the production choice. |
| PAY-DB-003 — instruction identity length | **Retain** | Source keys allow 160 characters while application storage allowed 100. Widening the application column preserves source identity without truncation; this is a concrete compatibility fix independent of approval/freshness policy. |
| PAY-DB-004 — redundant indexes | **Retain** | Remove the two indexes only when catalog comparison proves equivalence to retained unique-constraint indexes. Keep the constraints and drift refusal. This reduces duplicate structures; it is not a measured performance claim. |
| PAY-DB-005 — employee-level finalization | **Retain transaction mechanics; reshape controls** | Independent exact employee commits, durable receipts and truthful batch outcomes fit the contract. Mandatory current-source reconciliation and one approval workflow do not cover the layered policy model. Add protected hold/release and make applicable controls policy-aware at the protected commit boundary. |
| PAY-DB-006 — monthly instruction application | **Retain** | Enforce one ordinary recurring application per logical instruction, tenant, employee and payroll month across runs/versions. Keep source eligibility aligned with the database guard. This protects application integrity under either freshness policy; it does not infer duplicated business intent. |

## What reshaping means in the actual code

Paths below are relative to the pinned local Core candidate. Its Core design
and test documents describe the historical implementation; this reconciliation
supersedes their readiness implications, without rewriting that evidence.

### Employee controls and finalization

`internal/modules/payroll/employee_finalization.go`, especially `fresh` and
`FinalizeEmployee`, always resolves current inputs before a new commit.
`migrations/000095_payroll_employee_finalization.up.sql`, in
`payroll_finalize_employee_candidate`, independently requires both exact approval
and current-source matching. Removing only the Go comparison would therefore
neither implement draft-authority policy nor provide a complete control design.

Retain exact candidate/content identities, tenant and capability checks,
serializable atomic posting, application effects and receipt-first retry.
Retain the batch HTTP coordination in `http_idempotency.go`: its individual
employee transactions allow an eligible selection to finish independently.

Reshape current-source matching into a precondition of the selected policy.
Application-consumption checks must remain unconditional integrity checks.
An arbitrary caller-supplied flag must not disable applicable approval, hold
or freshness controls. The trusted policy binding, control evidence and public
interface need an implementation design; this report does not choose an enum,
policy storage table or optional-approval API.

The new employee operations offer proposal/approval, refresh and finalization,
but no protected hold/release. Excluding an employee from one request is not a
hold: a different request can still target that employee. Implement an
authorized hold that the commit gateway honors, retaining approval history and
making concurrent hold/commit outcomes consistent. Assess uncommitted
cancellation against the same contract. The changed-source refresh operation
is not general evidence that hold or unchanged-draft cancellation is supported.
No mandatory approval-withdrawal workflow is reintroduced.

The current SQL marks the whole run completed only when no member remains
unfinalized. Preserve that truth: a successful selection of 99 does not complete
the held hundredth employee. Keep employee receipts and batch selection results
distinct from whole-run completion. Existing whole-run entry points and
coordination restrictions also need coverage when controls change; do not
create a bypass through an older route.

### Contribution production

`internal/modules/payroll/employer_contribution.go` implements
`materializeContributionPair`. Both ledger preparation and candidate batches
invoke it automatically for employer-contribution entries. In
`candidate_batch_repository.go`, a fresh amended candidate also converts
retained legacy `none` contributions into pairs. Historical fixed revisions,
posted entries and replay bytes are preserved; this is not a rewrite of posted
money. It nevertheless adds monetary representation during a new proposal.

The handbook retains the user's CTC treatment. The recommended boundary is
that the producer explicitly supplies or requests that representation and Core
validates its completeness, amount/currency equality and linkage. A named Core
helper may perform mechanical expansion if that intent is explicit and the
complete result is fixed for review. Component classification alone should not
silently select an organizational production rule in a generic operation.

Keep pair integrity, atomic reversal linkage where applicable, derived
payroll/report totals, and the single obligation basis. Preserve historical
compatibility. Correction mechanics still need to respect the handbook's
subsequent-month and after-exit scope; their existence does not select policy.

### Liability classification and settlement

`migrations/000094_payroll_liability_register.up.sql` adds:

- `payroll_statutory_obligations`: authority arising from an exact posted entry.
- `payroll_statutory_remittances`: actual payment and retained proof.
- `payroll_statutory_allocations`: supplied links and amounts settling obligations.

These three records have distinct identities and histories; combining them
into one mutable challan row loses partial-payment evidence. Keep their tenant
relationships, immutability, replay protection and allocation balance checks.
No five-table or minimum-table-count target follows from the five domain ledgers.

However, table checks allow only `pf`, `esi`, `pt`, and `tds`.
`payroll_liability_type` maps reporting tags to those categories;
`payroll_liability_state` derives PT jurisdiction from employee work state.
`internal/modules/payroll/liability_register.go` repeats the category/state
validation. These are concrete country mappings, not merely storage mechanics.

Reshape those mappings behind explicit governed metadata or a country adapter,
while keeping Core's proof that obligation amount, currency and authority match
the committed representation. Do not replace validation with arbitrary labels
or allow an invented obligation. The exact adapter/schema is later engineering
work. This does not reopen statutory formulas or move the register to accounting.

The candidate's signed correction credits preserve original payment proof.
That encoding remains an implementation choice requiring review; retain the
no-rewrite/no-automatic-offset outcome. Do not infer refunds, automatic
settlement order or reallocation of previous payments from a negative balance.
Historical backfill must preserve the actual original amounts and authority.

## Additional gaps and evidence limits

| Item | Current evidence | Required next proof |
|---|---|---|
| Instruction-version API adapter | `payroll_instruction_authority_repository.go`, `CreateInstructionVersion`, has 18 SQL placeholders with 17 arguments and shifted casts; the protected function accepts 17. This defect also exists on main and remains unfixed. | Correct the adapter and exercise version creation through the granted public API/CLI journey. Existing replacement tests used the protected gateway for this step. |
| Hold and policy variants | Neither a protected hold nor draft-authority commit is implemented by the local employee path. | Same source-change facts under both policies; held draft cannot commit through any supported path; release/history and concurrent controls are consistent. |
| Public delivery | New settlement and employee-finalization APIs have no corresponding new CLI commands in this candidate. | Extend the required authenticated API/CLI acceptance, with exact Core identity, tenant/permission denials, retries and atomic failure evidence. |
| Schema suitability | Review is source-based; no deployed catalog or production workload was measured. | Validate migration compatibility against the intended baseline and realistic data before deployment. Do not describe the schema as globally optimal. |

Recorded validation at code `5bc0b1a` includes the full PostgreSQL 16 payroll
suite (95.531 seconds), repository-wide short tests and server/CLI builds.
Those are historical results for the earlier implementation, not freshly run
checks of this documentation pass or proof of the new controls. Test fixtures
and the local PostgreSQL helper can remain useful; tests enforcing universal
freshness must become policy-specific while integrity assertions remain shared.

This comparison covers the six implemented findings and their supporting
changes. It is not a certification of all unchanged Core behavior, browser-demo
runtime gaps, annual issuance, employer policy completeness or hub closure.

## Dependencies and review checkpoints

| Existing package | Dependency and next review boundary |
|---|---|
| Migration 92 and source eligibility | Bundles key width, index cleanup and recurring application uniqueness. Retain the intent; check existing duplicate data without deleting history, and preserve rollback refusal when keys exceed the old width. |
| Migration 93 and contribution code/projections | Pair representation spans Go preparation, SQL validation/posting and reports. Reshape them together so all derive the same money. |
| Migration 94 and liability APIs | Classification relies on contribution effects from 93, including the one-obligation rule and historical compatibility. Review the adapter boundary and backfill together. |
| Migration 95 and employee APIs/HTTP handling | Uses pair validation and application structures; posting invokes liability registration installed earlier. Policy/hold changes must cover Go, SQL, permissions, both commit paths and replay. |

Supporting server registration, routes, authorization manifests and database
gateway inventories belong with the operations they expose; retain their
scope checks and update them with the redesigned controls. Migration down
scripts require the same compatibility review as the forward scripts. Existing
test infrastructure and unrelated fixture repairs are supporting changes, not
new payroll policy. The Core implementation plans remain historical evidence.

The candidate cannot be treated as six independent cherry-picks. Preserve it
as evidence and prepare reviewed changes against then-current main. Do not
rewrite already merged migration history or assume the unshipped 92–95 package
is already a deployed contract.

Recommended checkpoints when implementation resumes:

1. **Small integrity fixes:** retain PAY-DB-003/004/006 and fix the existing
   instruction-version adapter. Prove key boundaries, duplicate application
   refusal, next-period eligibility and the actual public version-creation path.
2. **Review the control and producer boundaries before coding them:** define
   trusted policy selection, exact-draft approval/hold/cancellation behavior,
   explicit pair intent and liability metadata. These are engineering designs
   implementing the agreed concepts, not a new generic employer questionnaire.
3. **Integrate contributions and liabilities:** prove salary 50,000 plus
   contribution 1,000 gives gross 51,000, deductions 1,000, net 50,000 and one
   obligation; 10,000 paid by 6,000 then 4,000 retains both proofs and closes
   only through valid allocations. Preserve old posted/replay history.
4. **Integrate employee controls and acceptance:** a 5,000-to-6,000 source change
   blocks the old draft under policy A, but policy B may commit its fixed 5,000
   subject to other controls. Both reject duplicate instruction applications.
   Hold one of 100, commit the other 99 and keep one outstanding. Prove exact
   approval, no approval transfer, tenant/currency checks, hold/commit races,
   atomic failure and durable replay through the public API/CLI.

These checkpoints recommend the next work; they do not resume it. This pass
changes only handbook Markdown. Core code and its branch head, database contents,
runtime, hub tickets and remote repositories remain unchanged.

## Implementation plan derived from this reconciliation

The [compatibility plan](superpowers/plans/2026-09-06-payroll-handbook-compatibility.md)
turns these dispositions into source/application, contribution/liability,
draft-control and annual/public-acceptance packages. It also verifies unchanged
Core contracts before claiming whole-handbook compatibility. The user selected
Sol at medium reasoning for coding subagents. Proposed schema/API details in
the plan are engineering choices for review; this report's historical evidence
and the handbook's approved concepts remain distinct.

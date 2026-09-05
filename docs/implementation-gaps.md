# Payroll handbook — implementation gap register

This register compares agreed handbook concepts with inspected source behavior.
It does not claim a complete implementation audit or authorize code changes.
See [core concepts](core-concepts.md) for definitions and rationale, and
[the decision log](decision-log.md) for agreement status.

Evidence revision: lab `737465d5e27888518018e9b1f28f75fcfcac0139`,
[source](https://github.com/agentlabs-poc/agentlabs-payroll-ledger-lab/blob/737465d5e27888518018e9b1f28f75fcfcac0139/src/main.ts).

## PAY-GAP-001 — standing-instruction expiry

**Status: open, source-inspected. Requirements: PAY-CORE-002 / PAY-Q-004 and
PAY-CORE-005 / PAY-Q-007.**

Agreed behavior: standing instructions accommodate a finite effective lifetime
and expiry. A five-month repayment instruction must not continue applying
beyond its applicable lifetime. Its historical posted effects remain intact.
Evaluate that lifetime against the payroll period being processed, rather than
the current processing date, while preserving other payroll controls.

Observed source behavior:

- `PayrollInputEntry` declares optional `effectiveUntil` metadata.
- `appendPayrollInput` hardcodes the starting month and exposes no expiry
  parameter; it does not populate `effectiveUntil`.
- `preparePayrollReport` selects fixed demo instruction keys without checking
  effective start/end values. The UI can display an end value but that does not
  enforce applicability.

Consequence: expiry is not implemented end to end in the guided demo. The
existence of a field does not prove that an expired instruction is excluded.

Dependent decisions: how expiry is represented and evaluated, including period
boundaries and the distinction between elapsed months and successful
installments. Do not infer a catch-up or renewal policy from the loan example.

Closure evidence, after those semantics are agreed and implementation is
authorized: show instruction creation retaining the agreed lifetime, selection
including applicable periods and excluding expired ones, and historical posted
entries remaining unchanged. Verify the boundary and a repeated preparation
case, rather than only the presence of the expiry field. Include an eligible
earlier period processed after expiry and an ineligible later period processed
before expiry, proving that applicability follows the target payroll period.
Neither case bypasses prior-application or other payroll controls.

## PAY-GAP-002 — one-time consumption across drafts

**Status: open, source-inspected. Requirement: PAY-CORE-003 / PAY-Q-005.**

Agreed behavior: consumption occurs at commit and links the instruction to the
committed result. Preparing or abandoning a draft does not consume it; another
ordinary payroll cannot reuse it after consumption.

Observed source behavior: `commitDraft` sets `consumedBy` for referenced one-time
inputs and returns early on repeat commit of the same draft. However,
`appendDraft` accepts a source reference without checking consumption, and
`commitDraft` does not reject a different draft applying an already consumed
instruction. It can overwrite the original consumption reference.

Consequence: same-draft retry handling does not establish single application
across distinct drafts. This is a gap against the agreed concept, not a reason
to weaken it. No code has been changed for this register.

Closure evidence when implementation is authorized: verify that an abandoned
draft leaves the instruction available; a successful commit records one effect
and its reference; a retry creates no second effect; and a distinct competing
draft cannot apply the consumed instruction or replace its consumption link.
Where concurrent writers are supported, verify the competing-commit case too.
Partial application and reversal behavior require their own agreed semantics.

## PAY-GAP-003 — monthly application across drafts

**Status: open, source-inspected. Requirement: PAY-CORE-004 / PAY-Q-006.**

Agreed behavior: a monthly standing instruction has one ordinary committed
application per employee and applicable payroll month. It remains eligible for
later months within its lifetime. Abandoned drafts do not count as applications.

Observed source behavior: posted entries retain source references and draft
lineage, but `commitDraft` does not check whether a standing instruction was
already applied for that employee/month. Its consumption loop concerns only
one-time inputs. Same-draft retry handling cannot prevent another distinct
draft from applying the same monthly instruction to the same month.

Consequence: the guided demo's single preparation does not enforce monthly
application uniqueness across payrolls. Lifetime expiry and monthly application
are separate requirements; enforcing one alone would not establish the other.

Closure evidence when implementation is authorized: the first ordinary commit
applies the instruction for the employee/month; a competing draft cannot repeat
that application; a retry creates no duplicate; an abandoned draft does not
consume the monthly opportunity; the next eligible month can apply it again.
Include competing commits where concurrent writers are supported. Exact
instruction-version identity and correction effects remain dependent decisions.

## PAY-GAP-004 — draft and source freeze lifecycle

**Status: superseded design requirement; preserved as history.**
PAY-Q-010 approved PAY-CORE-006-C in place of the long-lived source freeze.
The original findings below concern PAY-CORE-006-B. Do not implement that
superseded freeze. Current complete-draft and reconciliation obligations are
tracked in PAY-GAP-005. Supersession is not evidence that the earlier code gap
was implemented or passed verification.

Historical requirement and findings follow.

Agreed behavior: create a complete draft with fixed monetary content from a
consistently frozen source set. Protect relevant additions, edits, and removals
through commit or cancellation. Successful commit records posted money and
instruction applications before releasing the source freeze. Cancellation
invalidates the draft before release; correction requires rebuilding.

Observed source behavior: `createDraft` publishes an empty open draft;
`appendDraft` permits later monetary additions while open. `fireDraftPayroll`
copies a previously prepared preview without a source-freeze mechanism.
`commitDraft` has no freeze ownership or release transition. `abandonDraft`
allows only open/sealed status and has no protection to release. The lab has no
durable recovery state across refresh or process failure.

Consequence: the agreed freeze lifecycle is not implemented. In particular,
frozen-after-sealing is weaker than frozen monetary content from creation.
The historical diagram in core-concepts.md describes code, not conformance.

Closure evidence when implementation is authorized: complete creation excludes
interleaving source changes; applicable additions/updates/removals and monetary
draft edits are blocked during review; successful commit and application
records precede release; cancellation prevents any later commit; retries,
competing writers, and recovery cannot unlock an active committable stale draft.
Verify unaffected scope remains usable where isolation is claimed. Define
shared dependencies, cancellation/recovery authority, and overlapping ownership
before claiming full coverage. This historical gap predates PAY-CORE-007, which
now includes sealing in complete creation; the source freeze remains superseded.

## PAY-GAP-005 — immutable-source capture and protected reconciliation

**Status: open, source-inspected. Requirements: PAY-SOURCE-001 and
PAY-CORE-006-C / PAY-Q-010.**

Agreed behavior: preserve immutable source history and a complete fixed draft
with sufficient basis for validation. PAY-CORE-010 removes mandatory source
tracing; per-entry source references are not a closure requirement. Source expiry/replacement can proceed during
review. Reconcile the full target-period input set and instruction applications
as part of protected posting; changes block commit and require rebuilding and
fresh review. Preserve one-time and monthly application guarantees.

Observed lab behavior at the evidence revision above:

- Source records and references exist, but there is no general immutable
  expiry/replacement history and resolution workflow.
- `createDraft` exposes an empty open draft, and `appendDraft` allows later
  monetary additions. `fireDraftPayroll` copies preview rows without validating
  a complete consistent source snapshot.
- `refreshHash` covers head, amount, and source text. It does not identify or
  compare the full applicable source set, its versions, or all dependencies.
- `commitDraft` checks status and posts entries without reconciling additions,
  expiry/replacement, or competing instruction applications. Its in-memory
  procedure does not provide the required durable concurrent commit boundary.
- `abandonDraft` accepts only open/sealed drafts, so an approved but uncommitted
  stale draft cannot be cancelled through this operation. The agreed rebuild
  path also needs to cover that case; cancellation authority remains unspecified.

Consequence: immutable-source history, complete fixed-draft creation, and
protected reconciliation are not established end to end by this lab. Existing
hashes, reference fields, and same-draft retry behavior are insufficient proof.

Closure evidence when implementation is authorized: a complete draft supports
validation of its applicable basis; source replacement preserves history; monetary draft
edits are rejected; relevant additions, replacements, expiry, and competing
applications block stale commits. Unrelated future-period changes do not
invalidate a draft whose basis remains applicable. Prove that validation,
posting, and application recording cannot be separated by a conflicting write,
including newly eligible sources. Rebuilds require fresh review; retries cannot
substitute unreviewed amounts or duplicate effects. Exact dependency inventory,
identity representation, and concurrency mechanisms remain parked decisions.

## PAY-GAP-006 — subsequent-month correction through governed payroll

**Status: open, source-inspected. Requirements: PAY-CORE-001/011 and PAY-ARCH-001.**

At the lab revision above, `carryAdjustmentToNextMonth` preserves the original
posted entry and appends a recovery under another reference. It directly marks
the correction committed, uses a synthetic draft ID, and does not validate that
the supplied ledger date belongs to a subsequent payroll month.

Required behavior: the prior generated payroll stays final. Within payroll
scope, the supplied adjustment is included in a subsequent month's governed draft/approval/commit
flow. PAY-CORE-013 excludes after-exit corrections, which belong in accounting.
The function's name and default October date do not enforce these boundaries.

Closure evidence when implementation is authorized: a correction cannot change
the original committed amount or be committed as an earlier/same-month correction;
it must pass the subsequent payroll's governed lifecycle. A retry must not
post the adjustment twice. No automatic source reuse or mandatory source tracing
is implied. Exact adjustment representation remains an implementation choice.

## PAY-GAP-007 — liability matching and remittance evidence

**Status: open, source-inspected. Basis: PAY-CORE-012 and PAY-ARCH-004.**

`matchReconciliation` rejects a match exceeding the payroll credit's remaining
amount. It does not generally validate positive match amounts, available
settlement-debit balance, or matching employer/tag/period on the two records.
`payAndReconcileChallans` supplies compatible synthetic data in the guided demo,
but its generated reference strings are not recorded real remittance evidence.

Consequence: the demo illustrates liability closure but does not establish a
general boundary for closing the corresponding obligation against a remittance
with proof. A company-wide sum cannot substitute for correspondence.

Closure evidence when implementation is authorized: the corresponding liability
is reduced only by a valid recorded settlement allocation backed by retained
proof; the same deposit amount cannot discharge unrelated obligations or be
reused beyond its available amount. Wrong-scope, invalid-amount, and duplicate
allocations must not create false closure. This expresses the agreed closure
meaning; exact record formats and partial-allocation policy remain open.

## PAY-GAP-008 — annual employee and period aggregation

**Status: source-inspected limitation of the annual example.** The Form 16
information basis is described in the output chapter; no complete production
issuance design has been approved by the handbook discussion.

`createForm16` sums all stored TDS credits and matches, chooses the first credit's
payroll reference, and uses that reference's payslip gross. It does not select
and aggregate the complete annual payroll for an employee/employer/year. It
explicitly returns an incomplete package and synthetic references.

Consequence: this function demonstrates an information dependency, not complete
annual reporting or certificate issuance. Full salary coverage and correctly
scoped deduction/deposit information cannot be inferred from its global totals.

When annual implementation is authorized, evidence must establish the correct
reporting scope and complete relevant salary/deduction/deposit data, followed by
the applicable statutory issuance process. Exact period/form applicability and
interfaces require their own review; this register does not supply new legal
rules or treat a balanced internal total as an official certificate.

## Agreement-to-evidence coverage

This map records the scope of the source review, not test results or production
conformance. Detailed open findings remain in the numbered entries above.

| Current agreement | Inspected support and remaining limitation |
|---|---|
| Five stores, final posted history, subsequent-month correction: PAY-CORE-001/002/011 | Types and ordinary flow exist; correction direct-posting/later-date checks are incomplete (GAP-006) |
| Source history, applicability, fixed drafts, protected reconciliation: PAY-SOURCE-001, PAY-CORE-005/006-C/009 | Fields and references exist; general effective selection, immutable-source workflow, fixed creation, and protected validation are missing (GAP-001/005) |
| One-time and monthly applications: PAY-CORE-003/004 | One-time marking and same-draft early return exist; cross-draft guards are absent (GAP-002/003) |
| Calculation/source scope: PAY-ARCH-001, PAY-CORE-008/010 | Higher-order demo calculation exists; business duplicate inference and mandatory source provenance are not adopted requirements |
| Employee-month association, draft, and batch: PAY-CORE-015, PAY-ARCH-002 | Reference owner/period and shared draft/posted reference exist; counter-generated numbers are demo behavior, not a prescribed generator. Exact production association mapping and multi-employee batch coordination are not established |
| Scoped authority: PAY-ARCH-003 | Lifecycle-state gates exist; actor/scope authorization is not implemented in the browser lab |
| Employer register and remittance closure: PAY-ARCH-004, PAY-CORE-012 | Register and synthetic matches exist; general matching and actual remittance evidence are not established (GAP-007) |
| After-exit corrections excluded: PAY-CORE-013 | Lab has only an active employee demo and no exit-scope enforcement; after-exit payroll adjustment is not a requirement to implement |
| Annual information basis | Readiness routine exists; complete annual selection/aggregation and issuance are not established (GAP-008) |
| Employer contributions: PAY-CORE-014 | Generic earning/deduction heads and tagged-deduction liabilities can represent the clarified flow; the lab has no complete employer-contribution pair example or business pairing enforcement |
| Separate sealing | PAY-CORE-007 includes sealing in complete draft creation; the lab still exposes empty creation, append, and a separate seal step |

## Coverage

Current entries cover expiry (PAY-GAP-001), one-time and monthly applications
(PAY-GAP-002/003), and immutable sources with fixed drafts and reconciliation
(PAY-GAP-005), plus subsequent-month correction enforcement (PAY-GAP-006).
PAY-GAP-007 adds matching/remittance integrity findings; PAY-GAP-008 identifies
the annual aggregation limitation. PAY-GAP-004 is superseded history. The broader source baseline
retains additional limitations; the register is not a complete audit.
PAY-ARCH-001's calculation boundary is agreed. Its source evidence is recorded
in [the calculation chapter](calculation-boundary.md); a full conformance audit
remains open. PAY-ARCH-002's ownership/batch boundary is also agreed: individual
drafts exist, but the inspected lab does not implement batch coordination or
durable protected commit. See [ownership evidence](ledger-ownership.md).
PAY-ARCH-003's authority boundary is agreed. The [authority chapter](authority-and-review.md)
records lifecycle checks but no authenticated actor/scope enforcement in the lab;
a complete authorization conformance audit remains open. PAY-CORE-007's inclusion of sealing in
complete creation is agreed but not implemented in the lab. The [core checkpoint](core-coverage.md)
records resolved scope clarifications. PAY-ARCH-004 now places the employer
register inside payroll and accounting outside. Existing liability/readiness
code supports that shape but does not demonstrate complete settlement or annual
issuance. PAY-CORE-012 establishes remittance-with-proof closure; the lab creates
synthetic challan references and matches, which are not observed remittance
evidence. The [output chapter](payroll-outputs.md) records the limits.

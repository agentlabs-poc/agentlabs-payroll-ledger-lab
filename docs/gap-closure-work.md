# Working through the remaining payroll gaps

Started 2026-09-06 following the [gap-resolution audit](gap-resolution-audit.md)
and the user's direction to work on the gaps. This pass develops handbook
specifications and acceptance evidence. It does not implement runtime changes
or mark a code gap fixed because its expected behavior is now explicit.

The [operation contracts](payroll-operation-contracts.md) now specify required
information, preconditions, outcomes, rejection/recovery behavior, liability
balances, and annual data-selection cases. PAY-Q-018 is approved as PAY-ARCH-005;
the [annual package](annual-payroll-package.md) now specifies the selected scope.

**Current status:** the layered conceptual handbook is reviewed; code remains paused.
[Baseline reconciliation](baseline-reconciliation.md) separates Core main and
local fixes from the browser-lab gaps below. The recorded contracts already
describe the ordinary cases; PAY-Q-020 is closed as superseded by
[PAY-ARCH-006](payroll-policy-boundary.md). The reconciliation/approval cases
below describe that policy, not mandatory workflow for every organization.
The [HRMS payroll policy](hrms-payroll-policy.md) and
[layered review cases](handbook-review.md#layered-walkthrough-results) also cover
draft authority and holding one employee while the other selected drafts proceed.

## Remaining-item classification

This pass separates implementation choices from matters still needing a payroll
behavior decision. Classification does not mark an unimplemented control fixed.

| Item | Treatment from the agreed model | Remaining decision or work |
|---|---|---|
| Skipped loan installments and changed repayment schedules | Business calculation/manager input under PAY-ARCH-001; payroll respects the supplied lifetime | No automatic extension is implied; a revised business arrangement enters through the existing instruction flow |
| Partial instruction application and restoration | The ordinary full-application/consumption rules are agreed | Not implicitly supported; a concrete partial-application scenario would require a behavior decision before adding that feature |
| Cancellation/recovery role assignment | Deployment authorization policy supplies the appropriate scoped capability; no fixed job titles are required | Implement the chosen mapping and preserve the already specified cancellation/recovery outcomes |
| Withdrawal of approval with unchanged draft amounts | Organizational Layer-2 policy under PAY-ARCH-006 | PAY-Q-020 closed as superseded; Layer 1 does not mandate either withdrawal alternative |
| Expiry encoding, application keys, reconciliation representation, concurrency and retries | Engineering choices constrained by the operation contracts | No canonical ID generator or business-source tracing requirement is introduced |
| Remittance allocation and proof interfaces | The supplied allocation must match the obligation and cannot exceed valid balances; proof is retained | Concrete interfaces/verification belong to integration work; no automatic allocation order selected |
| Excess remittance and unused deposit treatment | Excess cannot falsely close unrelated obligations | Detailed unused-money/refund treatment is not selected; retain as a distinct scoped follow-up, not a hidden liability rule |
| Annual package and complete issuance | PAY-ARCH-005 selects the package/handoff; statutory procedures are separate | Package aggregation is specified; code implementation remains open |

The [database-table review](database-table-review.md) adds source-backed HRMS
Core findings to this work. Its database findings are not new user decisions
and are separate from the browser-lab gap register.

## Work sequence and checkpoints

| Work group | Current treatment | Checkpoint |
|---|---|---|
| GAP-001/002/003: instruction lifetime and application | Eligibility/application contract and acceptance cases recorded | Ordinary expected outcomes specified; exact encoding and implementation proof remain |
| GAP-005/006: draft, commit, and correction | Preconditions, protected commit sequence, recovery outcomes, and correction contract recorded | Observable behavior specified; storage/concurrency and authorization mapping still need implementation evidence |
| GAP-007: liability settlement | PAY-Q-017 approved as PAY-CORE-016: the unpaid remainder stays a liability | Partial and final settlement example and acceptance case recorded; allocation/interfaces and implementation remain open |
| GAP-008: annual reporting | PAY-Q-018 approved as PAY-ARCH-005; annual package contents, selection, balances, missing inputs, and issuance handoff specified | Selected handbook scope documented; aggregation implementation remains open. Statutory procedures are a separate chapter |

GAP-004 is superseded history. Employee-month association is settled as
PAY-CORE-015 and is not a new question in this sequence. Supplemental-run
eligibility, exceptional installment behavior, role composition, and annual
issuance remain explicitly deferred; they are not prerequisites for restating
the ordinary rules below.

## Acceptance cases from existing agreements

These describe required outcomes for a later implementation review. They are
not executed tests, new state names, API contracts, or newly approved rules.

| Case | Given and action | Required observation | Basis |
|---|---|---|---|
| AC-01: finite lifetime | A recovery instruction applies September through January; prepare January and February payroll | January can include the instruction subject to the other controls; February cannot extend its lifetime automatically | GAP-001, PAY-CORE-002/005 |
| AC-02: processing date | Process the eligible January payroll in February | Processing later does not remove January eligibility; prior applications still prevent reuse | GAP-001, PAY-CORE-005 |
| AC-03: abandoned one-time proposal | Create then cancel an uncommitted draft containing a bonus | No posted bonus or consumption from that draft; any later use must still pass applicability and application checks | GAP-002, PAY-CORE-003 |
| AC-04: competing one-time applications | Two drafts attempt to apply the same eligible bonus; the first commits | The second cannot consume it again or replace the first consumption record; repeating the successful commit does not duplicate it | GAP-002, PAY-CORE-003 |
| AC-05: recurring application | Commit a monthly instruction in September, retry through another September draft, then prepare October within its lifetime | No second ordinary September application; October remains eligible | GAP-003, PAY-CORE-004 |
| AC-06: complete creation and exact approval | Create a complete draft and approve it; attempt to append or alter its monetary content | Creation includes sealing; the reviewed proposal stays fixed. Different amounts require cancellation/rebuild and fresh approval | GAP-005, PAY-CORE-006-C/007, PAY-ARCH-002 |
| AC-07: changed applicable basis | After approval, add or replace an applicable instruction, expire one, or commit a competing application | Protected reconciliation rejects the stale draft. Cancellation must work before commit even when that draft was approved | GAP-005, PAY-CORE-006-C |
| AC-08: unchanged total or unrelated change | Compare a changed applicable set with equal totals, and a separate change confined to a future period | Equal totals do not prove an unchanged basis; a future-only change does not invalidate an otherwise applicable basis | GAP-005, PAY-CORE-005/006-C |
| AC-09: protected posting and recovery | A competing write or lost response occurs around commit | Establish the commit outcome without duplicate money/applications or substitution of unreviewed amounts. Validation and posting must not admit an intervening conflicting write | GAP-002/003/005, existing commit invariants |
| AC-10: later correction | Supply a correction after generation while employee remains in payroll scope | Original stays final; adjustment goes through a subsequent month's create/approve/commit flow. Same-month or earlier correction posting and direct-posting bypass do not meet the agreement | GAP-006, PAY-CORE-011, PAY-ARCH-001 |
| AC-11: correction after exit | A correction arises after employee exit | External accounting handles it; payroll does not change the prior result or create the rejected former-employee adjustment flow | GAP-006, PAY-CORE-013 |
| AC-12: corresponding full settlement | A liability has a corresponding full remittance with retained proof | Close that obligation while preserving history; unrelated or duplicate allocations cannot falsely close another liability or reuse the same remitted amount | GAP-007, PAY-CORE-012, PAY-ARCH-004 |
| AC-13: partial then final settlement | Against INR 10,000 owed, record INR 6,000 remitted with proof, then the remaining INR 4,000 with its proof | First show INR 6,000 settled and INR 4,000 outstanding; then INR 10,000 settled and zero outstanding. Close only after the balance is settled; retain both remittances and original obligation | GAP-007, PAY-CORE-016 |
| AC-14: one stale employee in a batch | 100 exact employee drafts are approved; one employee's basis changes | The other 99 may commit after their own checks. The stale draft cannot commit and needs rebuild/fresh approval; batch status retains the outstanding outcome | PAY-ARCH-002 |
| AC-15: employee-month association | Two payroll results belong to the same employee/month; another belongs to a different employee or month | Preserve the correct association without merging draft identities, transferring approval, or bypassing application guards; no prescribed number generator | PAY-CORE-015 |
| AC-16: employer contribution | Salary 50,000 and employer contribution 1,000 are supplied | Draft and posted gross 51,000, deductions 1,000, net 50,000; one corresponding 1,000 employer obligation follows payroll, not two | PAY-CORE-014 |
| AC-17: authority and exact review | A caller can maintain inputs but lacks draft approval or commit capability | Input acceptance grants neither payroll approval nor posting. A granted commit still requires the exact draft's approval and protected reconciliation | PAY-ARCH-003 |

Rationale: these cases make existing decisions reviewable without selecting a
storage schema, identifier generator, database lock strategy, or source-origin
trace graph. A source reference field or a same-draft early return alone is
insufficient evidence of these outcomes. The [gap register](implementation-gaps.md)
retains the exact inspected limitations.

For a later implementation to close a gap, it must identify its representation
and demonstrate the applicable cases against the actual implementation boundary.
Browser-only demonstrations cannot establish durable concurrent enforcement.
This does not require a new domain discussion for routine engineering choices.

---

## PAY-Q-017 — representing a partial employer remittance

**Status: approved as PAY-CORE-016.** The user confirmed the proposal and
emphasized that the remainder stays a liability.

An INR 10,000 liability with a corresponding INR 6,000 remittance and proof
records INR 6,000 settled and INR 4,000 outstanding. The obligation fully closes
only when its remaining balance is settled with corresponding proof. Keep each
settlement and the original obligation as history.

Rationale: the register represents both money already remitted and money still
owed. A partial remittance does not erase the unpaid liability or hide the
amount already settled. This refines PAY-CORE-012's remittance/proof lifecycle.

The alternative was to record settlement only once the full obligation was
paid, requiring another way to retain the interim remittance. The user approved
recording the actual partial settlement and remaining balance instead.

The decision concerns internal representation of an actual remittance. It does
not determine statutory acceptability, allocation across multiple liabilities,
allocation ordering, excess deposits, accounting treatment, or proof-verification
interfaces. See [the successive balances](payroll-outputs.md#pay-core-016--partial-remittance-leaves-the-unpaid-liability-outstanding).

**PAY-Q-017 — approved:** the paid portion is settled; the unpaid balance remains
an outstanding liability. This resolves the basic partial-remittance rule, not
the entire GAP-007 implementation.

---

## PAY-Q-020 — withdrawing approval without changing draft amounts

**Closed as superseded by PAY-ARCH-006, 2026-09-06.** The user clarified that
this is an organizational policy decision in Layer 2, then explicitly requested
closure as superseded. It is not a remaining Layer-1 decision.

The original question offered two alternatives: retain an unchanged draft and
require fresh approval, or cancel/rebuild it after approval withdrawal. Neither
is adopted as a universal core rule. Proposed PAY-CORE-017 is superseded as a
core proposal; an organization may select that behavior in its payroll policy.

**Rationale:** Layer 1 owns records, authorized transitions, exact posting and
immutable history. Layer 2 owns the organization's approval, hold, selection
and source-reconciliation workflow. One organization may reconcile before
commit; another may accept the fixed draft as final authority. A held draft
can be excluded while the other selected drafts proceed, without being marked
committed itself. These choices need not change the core ledger guarantees.

See [the full boundary and supersession rationale](payroll-policy-boundary.md).
The earlier reconcile/rebuild rule is retained as a policy example, with its
universal Layer-1 placement superseded. No fresh-approval or hold representation
is silently made mandatory by closing this ticket.

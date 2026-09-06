# Working through the remaining payroll gaps

Started 2026-09-06 following the [gap-resolution audit](gap-resolution-audit.md)
and the user's direction to work on the gaps. This pass develops handbook
specifications and acceptance evidence. It does not implement runtime changes
or mark a code gap fixed because its expected behavior is now explicit.

The [operation contracts](payroll-operation-contracts.md) now specify required
information, preconditions, outcomes, rejection/recovery behavior, liability
balances, and annual data-selection cases. PAY-Q-018 is approved as PAY-ARCH-005;
the [annual package](annual-payroll-package.md) now specifies the selected scope.

## Remaining-item classification

This pass separates implementation choices from matters still needing a payroll
behavior decision. Classification does not mark an unimplemented control fixed.

| Item | Treatment from the agreed model | Remaining decision or work |
|---|---|---|
| Skipped loan installments and changed repayment schedules | Business calculation/manager input under PAY-ARCH-001; payroll respects the supplied lifetime | No automatic extension is implied; a revised business arrangement enters through the existing instruction flow |
| Partial instruction application and restoration | The ordinary full-application/consumption rules are agreed | Not implicitly supported; a concrete partial-application scenario would require a behavior decision before adding that feature |
| Cancellation/recovery role assignment | Deployment authorization policy supplies the appropriate scoped capability; no fixed job titles are required | Implement the chosen mapping and preserve the already specified cancellation/recovery outcomes |
| Withdrawal of approval with unchanged draft amounts | A distinct uncommitted lifecycle case, separate from source changes | PAY-Q-020 below proposes withdrawing approval without rebuilding unchanged monetary content |
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

**Status: proposed as PAY-CORE-017; awaiting the user's answer.**
An authorized reviewer wishes to withdraw approval before commit, while the
monetary proposal remains unchanged. Existing rules require cancellation and
rebuilding for a changed proposal/basis; they do not select this separate case.

Proposal: retain the same fixed draft, withdraw its current approval, and block
commit until fresh approval is granted. Preserve the approval/withdrawal history.
If the applicable basis changes, the existing cancellation/rebuild/fresh-review
rule still applies. Committed payroll remains final and cannot enter this path.

Rationale: withdrawing acceptance need not recreate unchanged monetary content.
The alternative is cancellation and rebuilding even when only the review
judgment changed; that reuses the cancellation path but creates a replacement
proposal unnecessarily. No approver/job-title mapping is prescribed by either
alternative; the action still requires the applicable authority.

**Question:** Should the same fixed draft return for fresh approval, with commit
blocked until approval is granted again?

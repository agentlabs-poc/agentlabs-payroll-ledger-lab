# Handbook review and remaining work

Review date: 2026-09-06. This records an editorial and conceptual consistency
review of the current working edition. It is not a production conformance test,
statutory certification, or a new set of approved payroll rules.

## Edition checkpoints

**Conceptual edition 1, closed 2026-09-06.** This is an editorial closure of the
agreed conceptual model after the user directed the final walkthrough and
checkpoint pass. It does not claim employer-specific operating validation or
completion of every topic in the broader pinned charter. No new payroll rule
is adopted by closing this edition.

| Checkpoint | Result | Closure evidence |
|---|---|---|
| CP-01: core concepts | Complete for this edition | Ledgers, instruction lifetime/application, immutable sources, fixed draft, creation including sealing, approval, and commit are agreed and recorded |
| CP-02: responsibility boundaries | Complete for this edition | Manager intake, calculation, scoped capabilities, employee-month association, payroll finality, employer register, and external accounting are explained |
| CP-03: representative walkthrough | Complete for this edition | The final review below traces ordinary payroll, changed inputs, commit, correction, liability closure, and annual information; existing decisions determine the illustrated outcomes |
| CP-04: documentation closure | Complete for this edition | Current explanations and diagram aligned with PAY-CORE-007; rationale/history retained, source gaps visible, and deferred work classified |

**At edition closure, no named proposal awaited an answer.** PAY-Q-009 is
approved. The subsequent [gap-closure pass](gap-closure-work.md) now opens
PAY-Q-017 on partial remittances; it is now approved as PAY-CORE-016. No named
core-rule proposal currently awaits an answer. PAY-Q-018 is approved as
PAY-ARCH-005, and the [annual package](annual-payroll-package.md) is specified.
PAY-Q-019 remains open on completion scope. The
[gap-resolution audit](gap-resolution-audit.md)
clarifies the limit: six numbered gaps have agreed core behavior, one is
superseded, and the annual scope was then partly specified. PAY-ARCH-005 now
selects the payroll package/handoff and separates statutory procedures. Seven
active code gaps/limitations remain; scope approval does not implement them.

## Final walkthrough results

Basis: the [continuous example](payroll-scenarios.md#end-to-end-payroll-and-liability-walkthrough),
[lifecycle](payroll-lifecycle.md), [source reconciliation](source-reconciliation.md),
[authority](authority-and-review.md), and [extended journeys](employee-and-annual-journeys.md).
This is a review of handbook semantics and arithmetic, not an executed payroll.
Amounts are supplied calculation outputs; no contribution or tax formula is
inferred from the example.

| Step or branch | Responsibility and event | Determinate result from existing decisions |
|---|---|---|
| Intake and preparation | HR/payroll manager consolidates applicable facts through APIs; higher-order calculation supplies seven components | September gross INR 57,500, deductions INR 4,000, net INR 53,500; employer contribution is an earning/deduction pair |
| Creation and approval | Preparation capability creates the complete draft including sealing; approval capability accepts that exact proposal | Monetary content is fixed; neither preparation nor approval consumes instructions or generates final payroll |
| Unchanged basis | Commit capability invokes protected reconciliation and posting | Seven final rows; one-time bonus consumed and monthly applications recorded for September; net INR 53,500 is final |
| Changed-basis alternative before commit | The applicable bonus changes from INR 5,000 to INR 6,000 after approval; calculation supplies the other six amounts unchanged for this illustration | Old draft stays INR 53,500 net and cannot commit. Cancel/rebuild with fresh approval: new gross INR 58,500, deductions INR 4,000, net INR 54,500. Only the replacement commits |
| Retry or abandoned draft | Recovery establishes whether a commit occurred; an uncommitted cancellation produces no payroll | No duplicate result/application from retry; no consumption by cancellation. Exact recovery and cancellation authority remain deferred |
| Employer liabilities | Payroll records obligations following committed payroll; employer remits to the respective authorities and records proof | Contribution liability INR 1,000 and tax liability INR 2,000 each close against corresponding remittance/proof. The ordinary recovery is not a government liability in this example |
| Later correction within scope | Manager supplies a subsequent-month INR 500 recovery through the governed payroll flow | September remains unchanged; the later month includes INR -500. No automatic undo of earlier instruction applications |
| Correction after exit | The correction arises after the employee has exited | External accounting handles it; payroll history stays final |
| Annual information | Annual workflow uses relevant committed payroll, employer obligations/remittances, and required calculation/official records | September is one contribution to annual information. Neither this example nor liability closure alone constitutes certificate issuance |

The unchanged and changed-basis rows are alternative branches, not two ordinary
commits of the same instructions. All payroll within either employee-month is
associated; approval still belongs to the exact draft. Identifier generation
remains unspecified. Rebuilding includes calculation from the applicable basis.

Additional cases already incorporated cover joining, supplied partial-period
amounts, supplied exit components, future salary changes, finite expiry, late
processing of an eligible period, and a stale employee draft within a batch.
They use the same core operations. The reviewed scenarios expose no additional
core decision; they do not select broader exception policies.

Rationale for closure: the existing decisions explain the selected records,
responsibilities, and outcomes. The remaining uncertainties can be named and
deferred without changing those illustrative outcomes. The lab still lacks
several required controls, including approved-stale-draft cancellation and
protected reconciliation; the gap register preserves those findings.

## Incorporated coverage

| Area | Current coverage | Evidence or rationale |
|---|---|---|
| Five employee payroll stores | Definitions, relationships, and agreed core flow incorporated | [Core concepts](core-concepts.md#agreed-core-model) |
| Intake and calculation | Manager/API handoff; business calculation and source intent outside the core ledger responsibility | [Handbook flow](handbook.md#from-manager-inputs-to-generated-payroll) |
| Lifecycle operations and outcomes | Preparation, fixed draft, exact approval, stale-draft cancellation, commit, and retry guarantees consolidated | [Lifecycle](payroll-lifecycle.md) |
| Source changes and draft finality | Immutable source history, fixed draft, protected reconciliation, cancel/rebuild/fresh review | [Reconciliation model](source-reconciliation.md) |
| Instruction lifetime/application | Expiry, once-per-period monthly applications, one-time consumption on commit, and late processing | [Instruction rules](handbook.md#instruction-lifetime-and-application) |
| Ownership and authority | Employee-month association without a canonical ID generator, employee-period draft/commit unit, batch outcomes, and distinct scoped capabilities | [Ownership](ledger-ownership.md), [authority](authority-and-review.md) |
| Changes and exceptions | Salary change, expiry, abandoned/stale drafts, batch exception, and subsequent-month adjustment examples | [Scenarios](payroll-scenarios.md) |
| Joining, partial periods, and exit | Supplied calculation amounts use the governed flow; after-exit corrections excluded to accounting | [Extended journeys](employee-and-annual-journeys.md) |
| Employer contribution and liability | CTC contribution earning/deduction pair precedes employer register; remittance/proof closes the corresponding liability | [Contribution flow](payroll-outputs.md#pay-core-014--employer-contributions-through-payroll) |
| Annual information and reporting | Data flow, preparation/review sequence, allocation examples, and distinction from issuance | [Reporting and reconciliation](reporting-and-reconciliation.md) |
| Full illustrative monthly cycle | Seven payroll components, commit/application, employer liabilities, proof-backed closure, later correction, and annual use | [Continuous walkthrough](payroll-scenarios.md#end-to-end-payroll-and-liability-walkthrough) |
| Decision rationale/history | Current agreements and source facts distinguished from rejected or parked proposals | [Decision log](decision-log.md) |
| Code comparison | Current agreement groups mapped to inspected support and gaps; source revisions and limits retained | [Evidence coverage](implementation-gaps.md#agreement-to-evidence-coverage) |

The major conceptual coverage is incorporated. This does not imply every
formula, API, operational policy, or issuance integration is specified.

## Consistency points reviewed

- All payroll for an employee/month is tied together. No canonical ID-generation
  method is selected; grouping does not transfer exact-draft approval or permit
  duplicate applications.
- Employer contributions increase gross and deductions equally, leaving net
  unchanged by the pair. They enter committed payroll before the employer
  register and represent one corresponding obligation.
- The employer-liability register is inside payroll. General accounting and
  corrections arising after employee exit are outside payroll.
- Generated payroll is final. Corresponding government remittance and proof
  close the employer obligation; these are distinct finality events.
- Relevant source changes require rebuilding the fixed draft before commit.
  Historical source tracing and business overlap inference are not mandatory
  payroll-core responsibilities.
- Monthly application, one-time consumption, and expiry remain distinct. The
  examples do not silently restore instructions or extend repayment schedules.
- Old freeze and direct-contribution alternatives remain history, rather than
  active requirements. PAY-CORE-007 now includes sealing in complete draft creation.
- Annual readiness is not issuance; a global TDS total plus one payslip does
  not establish a complete employee/year result. Code limitations are recorded.

## What remains, and where it belongs

| Remaining item | Why it remains | Next treatment |
|---|---|---|
| Employer-specific operating procedures | Actual employer/jurisdiction/workforce context, calendars, cutoffs, manual work, and escalation/revocation procedures have not been established | A later operating edition; retain the pinned charter and avoid presenting illustrative practices as observed reality |
| Additional exception policies | Same-period supplemental runs, partial applications, allocation of remittances across multiple obligations, and wider payment-failure procedures are not fully selected | Address a concrete scenario when that scope is developed; preserve finality, instruction guards, and accounting boundaries |
| Expiry and validation representation | Dates/period encoding, immutable-source lifecycle metadata, and validation evidence are not selected | Implementation specification; no reopening of applicability or source-tracing decisions |
| Exceptional installment/application behavior | Automatic extension, splitting, and restoration have not been adopted | Apply the supplied policy where it fits existing rules; ask if a core behavior change is proposed |
| Concurrency, retries, and recovery | Durable storage and coordination are not implemented in the demo | Implement against the already stated invariants when authorized |
| Detailed role assignments and integrations | Capabilities and system boundaries are settled, concrete mappings are not | Deployment/operating specification rather than invented job-title rules |
| Complete annual issuance | PAY-ARCH-005 selects the payroll annual package/handoff for this handbook; complete issuance is a separate chapter | Develop the statutory procedure for the applicable jurisdiction/year when that chapter is scoped; it does not block the approved package specification |
| Detailed business calculations | Proration, contribution amounts, and annual tax formulas belong to higher-order policy | Do not turn them into new core ledger primitives or infer policy from demo arithmetic |

These items should not all be presented as unanswered foundational questions.
Some are implementation choices; others belong to the producing/consuming layer.
PAY-Q-009 is now settled as PAY-CORE-007. If a future scenario exposes a material
choice within payroll scope, identify that choice and ask before adopting it.

## Review checks

This pass checks local Markdown links and heading anchors, fence balance,
consistency of recorded decision status, example arithmetic, preservation of the
pinned charter, and separation of runtime code from documentation changes.
The walkthrough covers gross/deductions/net and liability amounts explicitly.
Source-inspected implementation gaps remain open; no runtime execution or
completed software behavior is claimed by this review.

The conceptual edition is closed with the above deferrals. Full deployment,
employer-specific operations, and period-specific compliance procedures remain
outside what this review proves. This is the stopping point for the current
conceptual edition. Subsequent refinements are tracked in the active gap-closure
worksheet without treating the earlier edition as an implementation release.

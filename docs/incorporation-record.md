# What was incorporated into the handbook

This is an editorial change record, not a new domain decision. It implements
the user's request to incorporate established material first and show what was
incorporated. The discussion snapshot was committed and pushed first as
`6a30db5ced58dff013bb2caa436b15733d832d87`.

## Change in the reading experience

Previously, the handbook's resume section mostly listed approvals in discussion
order and sent the reader to separate chapters. The revised
[handbook](handbook.md#reading-path) explains the model in subject order:
ledgers, manager handoff, payroll generation, instruction application, a monthly
example and correction, ownership/authority, and existing-code evidence.

The pinned charter and completion criteria are retained. The decision log,
specialist chapters, rationale, alternatives, and superseded history remain
available; the narrative does not replace their evidence.

## Incorporated from agreements and user clarifications

| Material | Existing basis | Where the reader finds it |
|---|---|---|
| Five ledgers and their different meanings | PAY-CORE-001/002 and the reviewed model | [The five ledgers](handbook.md#the-five-ledgers) |
| Manager/API handoff, applicable facts, calculation/core split, fixed draft, and protected commit | PAY-INTAKE-001, PAY-CORE-006-C/008/009/010, PAY-ARCH-001 | [From manager inputs to generated payroll](handbook.md#from-manager-inputs-to-generated-payroll) |
| Expiry, one-time consumption, monthly application, and payroll-period applicability | PAY-CORE-002/003/004/005 | [Instruction lifetime and application](handbook.md#instruction-lifetime-and-application) |
| Ordinary payroll and subsequent-month correction, with generated payroll treated as final | PAY-CORE-001/003/004/011; existing illustrative amounts | [One monthly payroll, then a correction](handbook.md#one-monthly-payroll-then-a-correction) |
| Employee-period unit, batch outcomes, and scoped capabilities | PAY-ARCH-002/003 | [Ownership, batches, and authority](handbook.md#ownership-batches-and-authority) |

These sections state the agreed outcomes and rationale directly. They do not
ask for the same approval again. The examples apply existing rules rather than
selecting new exception, calculation, or recovery policies.

## Incorporated as existing-code descriptions only

The [existing lab section](handbook.md#what-the-existing-lab-additionally-describes)
incorporates seven already described concepts: preparation preview,
component/head, proof attachment, payroll reference, payslip snapshot/PDF,
employer-liability records, and the incomplete annual readiness package.

Evidence: lab revision `737465d5e27888518018e9b1f28f75fcfcac0139`,
[main.ts](../src/main.ts), as recorded in [the baseline](operating-baseline.md)
and [core-concept chapter](core-concepts.md). Each row includes its limitation.
Code descriptions do not become approved requirements merely by being included.

## What remained undecided at this incorporation

- PAY-Q-014 / PAY-ARCH-004: the proposed downstream responsibility boundary.
- PAY-Q-009 / PAY-CORE-007: the parked separate-sealing question.
- Detailed exceptions, source/validation representations, role assignments,
  wider journeys, and integration policies identified in the roadmap.

No new payroll rules, source-tracing requirement, automatic instruction reuse,
or same-month correction policy is introduced. No runtime code is changed.
The handbook's coverage estimate is not automatically increased by reorganizing
existing content; complete scenario coverage and publication review remain work.

Later update: the user subsequently answered PAY-Q-014 with a corrected
boundary: employer liabilities inside payroll, accounting outside. See the
[updated chapter](payroll-outputs.md). This was a separate user clarification,
not an approval inferred during the incorporation pass.

## Scenario incorporation — 2026-09-06

After confirming the liability lifecycle, the next pass added
[payroll scenarios](payroll-scenarios.md): nine outcome cases derived from prior
agreements, a three-month salary/expiry illustration, and an explanation of the
two reconciliation purposes. Each case identifies its established decision
basis; none introduces a new domain decision.

The grouped-challan example is explicitly source-described behavior from
`payAndReconcileChallans` and `matchReconciliation`, not adoption of production
allocation rules. Joining/exit, partial-period calculation, and full annual
issuance remain incomplete. This adds worked scenario coverage but is not an
implementation test or a claim that all handbook journeys are now complete.

## Extended journeys — 2026-09-06

[Joining, partial periods, exit, and annual reporting](employee-and-annual-journeys.md)
now describe how supplied facts and calculation outputs use the agreed payroll
lifecycle. Examples assume component amounts rather than choosing new formulas.
The settlement source description is pinned to the previously inspected HRMS
Core revision; the annual description retains the lab's incomplete status.

PAY-Q-015 raised one new material question about a former employee’s later
adjustment. The user answered during this pass: handle it in external accounting,
outside payroll. PAY-CORE-013 records the boundary and withdraws the proposed
payroll exception. This is a user decision, not inferred from incorporation.
Complete annual issuance and exception/calculation policies remain further work.

## Reconciliation and consistency pass — 2026-09-06

[Reporting and reconciliation](reporting-and-reconciliation.md) now distinguishes
employee payroll finality, liability closure, annual readiness, and issuance.
It adds supplied-allocation and annual-data examples, while GAP-007/008 record
missing matching validation and annual aggregation in the inspected code.

The consistency pass updates earlier wording in the source-input, calculation,
core-concept, ownership, and operating-baseline chapters to reflect later
agreements. The gap register now maps agreement groups to inspected support.
Historical alternatives remain reconstructable; settled concepts are not
reopened because code enforcement is missing.

PAY-Q-016 initially asked about employer-only contributions with no effect on
gross. The user subsequently corrected that premise: CTC contribution earning
and matching deduction enter payroll first, followed by employer liability.
PAY-CORE-014 now records that flow, with gross increasing and net unchanged by
the pair. The earlier proposal is withdrawn; the revised material derives from
the user’s clarification, not from the reporting examples.

## Integrated walkthrough and review — 2026-09-06

The [continuous payroll/liability walkthrough](payroll-scenarios.md#end-to-end-payroll-and-liability-walkthrough)
combines the established contribution earning/deduction pair with salary,
monthly/one-time instructions, commit, and corresponding remittances with proof.
The [review record](handbook-review.md) maps coverage and classifies remaining
implementation details separately from policy questions. This consolidates
existing concepts; it does not claim runtime implementation or complete statutory
issuance procedures.

During this pass, the user clarified PAY-CORE-015: all payroll for an employee
and month is tied together, and no canonical ID-generation method is established.
The ownership chapter and handbook now state this association without inventing
an identifier format, new ledger, or automatic transfer of draft approval.

## Verification

Review this change against the discussion snapshot above. Verify all local
Markdown links and heading anchors, fence balance, the example's arithmetic,
and that the pending decisions remain labeled open/parked. Runtime tests do not
validate this editorial change; no software behavior is modified.

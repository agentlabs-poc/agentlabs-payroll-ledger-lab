# HRMS Payroll Handbook — discussion roadmap

This working navigation follows the [pinned goal](handbook.md). It organizes
future investigation; it does not imply agreement on payroll rules.
See the [decision log](decision-log.md) for recorded user directions and the
[operating baseline](operating-baseline.md) for source findings.

## Resume here

**Current: established scenario coverage incorporated under PAY-PROCESS-009.**

Read [payroll scenarios](payroll-scenarios.md) for the nine agreed-outcome cases
and the separately labeled grouped-challan code example. No new policy approval
is inferred from these examples. Joining/exit, partial-period situations, and
complete annual workflows remain the next coverage areas; ask only when their
explanation requires a material decision.

The user requested that established material be incorporated first, with a clear
account of what changed. The existing handbook snapshot was committed and pushed
as `6a30db5`; the [incorporation record](incorporation-record.md) maps the
subsequent editorial changes to their existing basis. Read the
[handbook narrative](handbook.md#reading-path) to see the incorporated result.
The user later clarified PAY-Q-014 / PAY-ARCH-004: employer liabilities belong
in payroll; accounting is external. The [updated output chapter](payroll-outputs.md)
records that boundary and the verified, partial basis for Form 16. PAY-CORE-012
also establishes closure on the employer’s government remittance with proof
such as the challan number.

The user approved PAY-ARCH-003, then clarified that broader questions are
relevant once the core concepts are clear. PAY-PROCESS-006 still calls for
horizontal breadth: apply it to unresolved core semantics before further role,
payment, and downstream design.

PAY-CORE-001 through PAY-CORE-005 and PAY-CORE-006-C remain agreed, together with
PAY-ARCH-001 (calculation boundary), PAY-ARCH-002 (employee draft/batch scope),
and PAY-ARCH-003 (distinct scoped capabilities). Approval of these boundaries
is not a claim that the core model or implementation is complete.

---

Read the [updated core checkpoint](core-coverage.md). PAY-CORE-008 places
business source-overlap detection outside payroll core; PAY-CORE-009 uses the
applicable facts when payroll runs; PAY-CORE-010 removes mandatory source tracing.
PAY-CORE-011 settles corrections: generated/committed payroll is as good as
paid; adjustments belong to a subsequent payroll month. The four-item core
checkpoint is resolved at the intended scope. Do not reopen these concepts as
questions; preserve the distinction between agreements and implementation gaps.

The [core model is consolidated](core-concepts.md#agreed-core-model), including
the ordinary-payroll example and subsequent-month correction.

---

The [output boundary](payroll-outputs.md) is now clarified. Detailed liability
and annual reporting workflows remain later work; employee payroll finality
is unchanged.

## Horizontal coverage map

| Area | Current position | High-impact question to establish |
|---|---|---|
| Core semantics | Agreements consolidated, including PAY-CORE-008/009/010/011 | Applicable facts, source-scope limits, fixed drafts, committed finality, and subsequent-month adjustments. |
| Calculation versus core | PAY-ARCH-001 agreed under PAY-Q-011; mechanics open | Who produces business amounts and who controls their monetary lifecycle? |
| Ownership and unit of work | PAY-ARCH-002 agreed under PAY-Q-012; mechanics open | Whose ledger is this, and what employee/period or batch does an approval and commit cover? |
| Authority and review | PAY-ARCH-003 agreed under PAY-Q-013; further detail deferred | Which responsibilities can prepare, approve, commit, correct, and record payment? |
| Payroll liabilities and external accounting | PAY-ARCH-004 ownership clarified under PAY-Q-014 | How do payslips, employee payment, employer/statutory liabilities, and accounting use posted payroll? |
| Corrections | PAY-CORE-001/011 establish preserved history and subsequent-month adjustment; scenario incorporated | Implementation and downstream projections remain later work; correction timing is settled. |
| Reports and reconciliation | Pre-commit consistency agreed; PAY-CORE-012 establishes liability closure with remittance proof | Which outputs are projections, which are authoritative records, and what closes a settlement? |

## Parked details and return points

- PAY-Q-009 / PAY-CORE-007: whether sealing is included in complete draft creation.
- Expiry encoding, installment counts, skipped-period recovery, and applicability history.
- Reconciliation/application validation representation; mandatory source tracing
  and business overlap inference were removed from core scope.
- Concurrency implementation, retries, cancellation authority, and recovery mechanics.
- Partial-application mechanics; correction timing is settled by PAY-CORE-011.
  No automatic restoration of instruction availability has been adopted.
- Calculator interfaces, rule-version evidence, and calculation assurance.
- Exact tenant/employment identity and batch action/retry mechanics following PAY-Q-012.
- Role composition, source-acceptance policy, separation of duties, delegation,
  revocation, approval evidence, and automated execution after PAY-Q-013.

PAY-Q-002's attendance-payload question remains withdrawn from the current
sequence. Source-to-manager intake remains recorded in PAY-INTAKE-001; it is
supporting context, not a prerequisite interview for the horizontal pass.

## Discussion tree

| Stage | Branches to examine | Evidence needed to close the stage |
|---|---|---|
| 1. Existing core model — current | Salary earnings; monthly and one-time instructions; draft and posted ledgers; relationships and operations. | A source-backed explanation of the model and resulting flow, followed by discussion confirming its meaning. |
| 2. Confirm and refine | Applicability; recurrence and consumption; owner and dates; references; amount semantics; draft lifecycle; correction lineage. | Definitions and rules tested with examples and counterexamples; improvements discussed explicitly. |
| 3. Journeys and exceptions | Preparation; approval; posting; payslips; liabilities; corrections; joining, changes, exit, and annual work within the model. | Worked scenarios tracing records, responsibility, failures, and recovery; scope-specific exclusions made explicit. |
| 4. Rules and controls | Authority; validation; approvals; change over time; duplicate processing; traceability; reconciliation. | Discussed and agreed rules with rationale and unresolved dependencies preserved. |
| 5. Reconciliation and publication | Cross-chapter consistency; scenario coverage; implementation comparison; deferred work. | A coherent handbook meeting the pinned completion criteria and an evidence-backed gap register. |

When a question opens another branch, record the return point before moving.
Do not mark a whole stage complete because one example or sidebar is settled.

## How to record each discussion

Start with a concrete question and preserve its stable `PAY-Q-NNN` identifier.
Explain the current interpretation, examine an example and counterexample,
and compare alternatives where they affect the outcome. Record user decisions
in the log; put the substantive explanation in the relevant chapter.

Label source behavior, observed practice, proposals, and agreements separately.
An open question may be answered, explicitly deferred, or superseded with a
reason. It must not disappear when the conversation changes direction.

## Completion status

The charter is pinned, initial code findings and a conceptual reconstruction
are recorded, and the manager's input handoff is established through the user's
account. Established material is now incorporated into the handbook narrative;
the employer-liability clarification and agreed scenario outcomes are recorded.
Joining/exit, partial-period situations, and complete annual workflows remain
later coverage.
Further rules, complete scenario coverage, and an implementation gap register
against agreed requirements remain ongoing work. The
[initial gap register](implementation-gaps.md) records missing expiry enforcement;
it is not a complete implementation audit.

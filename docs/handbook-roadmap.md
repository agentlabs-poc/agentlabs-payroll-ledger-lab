# HRMS Payroll Handbook — discussion roadmap

This working navigation follows the [pinned goal](handbook.md). It organizes
future investigation; it does not imply agreement on payroll rules.
See the [decision log](decision-log.md) for recorded user directions and the
[operating baseline](operating-baseline.md) for source findings.

## Resume here

**Current: layered conceptual handbook reviewed; implementation proceeding through checkpoint PRs.** The
[review record](handbook-review.md#current-consolidated-review) records the current
gate. PAY-Q-020 is closed as superseded by the user’s
[Layer-1/Layer-2 clarification](payroll-policy-boundary.md). Approval withdrawal
and source freshness are organizational policy choices.

The [baseline reconciliation](baseline-reconciliation.md) establishes that
payroll Layer 1 is already merged into Core main `3a87931`. It maps the hub's
architecture and later handbook decisions without reviving the old integration
branch or deferred Layer-2 work. The local database-fix branch is preserved;
it is not handbook approval or a merged delivery.

This pass completed the [Layer-1 contracts](layer-1-contracts.md), separate
[HRMS payroll policy](hrms-payroll-policy.md), both freshness variants, hold/batch
examples and consolidated review. PAY-Q-020 requires no further answer.

The [implementation reconciliation](implementation-reconciliation.md) now maps
the six local findings to these contracts: three retained directly and three
to reshape. It records code evidence, missing protected hold/policy support,
dependencies and review checkpoints. Implementation has resumed: CP-0 through
CP-2 are reviewed and merged into the draft hub; CP-3 controls and CP-4 annual
reporting are underway. See the [checkpoint status](handbook-review.md#implementation-checkpoint-status)
for exact commits and evidence boundaries. Organizational workflow choices
remain outside universal Layer-1 rules.

The [operation contracts](payroll-operation-contracts.md) and
[annual package](annual-payroll-package.md) specify the agreed outcomes.
The [classification](gap-closure-work.md#remaining-item-classification) separates
material behavior choices from engineering, deployment and future policy work.
Browser-lab gaps and local Core findings have separate evidence and must not be
used as a percentage of handbook completion.

## Proposed implementation plan

The [handbook compatibility plan](superpowers/plans/2026-09-06-payroll-handbook-compatibility.md)
now defines CP-0 through CP-5, four implementation packages, repository scope,
file ownership and acceptance evidence. Coding is assigned to `gpt-5.6-sol` at
medium reasoning, with primary-agent integration/review. The user has now authorized execution through
[Core hub PR #172](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/172)
and separate checkpoint PRs. Compatibility is not complete until their
implementation and acceptance evidence close the gates.

## Incorporated coverage

- [Main handbook](handbook.md#reading-path): five ledgers, manager handoff,
  calculation, fixed drafts, protected commit, authority, finality, and corrections.
- [Payroll scenarios](payroll-scenarios.md): nine existing-agreement cases,
  salary/expiry across months, and a labeled grouped-challan code example.
- [Extended journeys](employee-and-annual-journeys.md): joining, supplied
  partial-period amounts, exit components, and annual information flow.
- [Payroll outputs](payroll-outputs.md): employer register inside payroll,
  accounting outside, remittance/proof closure, and the Form 16 information basis.
- [Reporting and reconciliation](reporting-and-reconciliation.md): annual
  preparation, the distinct closure meanings, and scoped data examples.
- [Implementation gaps](implementation-gaps.md#agreement-to-evidence-coverage):
  current agreements mapped to inspected support and limitations.

The [incorporation record](incorporation-record.md) shows each pass and its basis.
Source descriptions are not automatically adopted requirements. The latest
consistency pass removes older wording that still presented settled boundaries
as open; superseded alternatives remain labeled in the decision history.

---

Settled boundaries are not new questions: payroll uses applicable facts; business
source intent belongs upstream; source tracing is not mandatory; generated
payroll is final; corrections are subsequent-month adjustments within payroll
scope; after-exit corrections belong in accounting; employer liabilities remain
inside payroll and close on corresponding remittance with proof.

## Horizontal coverage map

| Area | Current position | High-impact question to establish |
|---|---|---|
| Core semantics | Agreements consolidated, including PAY-CORE-008/009/010/011 | Applicable facts, source-scope limits, fixed drafts, committed finality, and subsequent-month adjustments. |
| Calculation versus core | PAY-ARCH-001 agreed under PAY-Q-011; mechanics open | Who produces business amounts and who controls their monetary lifecycle? |
| Ownership and unit of work | PAY-ARCH-002 and PAY-CORE-015 establish employee-month association, draft/commit unit, and batch coordination | Identifier generation is not canonical; implementation mapping remains open. |
| Authority and review | PAY-ARCH-003 agreed under PAY-Q-013; further detail deferred | Which responsibilities can prepare, approve, commit, correct, and record payment? |
| Payroll liabilities and external accounting | PAY-ARCH-004 ownership clarified under PAY-Q-014 | How do payslips, employee payment, employer/statutory liabilities, and accounting use posted payroll? |
| Corrections | PAY-CORE-001/011/013 settle finality, subsequent-month adjustment, and after-exit accounting scope | Enforcement and specific external reporting treatment remain separate from the settled payroll rule. |
| Reports and reconciliation | Annual preparation and closure meanings incorporated; GAP-007/008 recorded | Complete issuance integration and detailed validation remain later work. |
| Employer contributions | PAY-CORE-014 earning/deduction flow clarified under PAY-Q-016 | CTC contribution enters Payroll Ledger first and employer register next; gross includes it and matching deduction balances net. |

## Parked details and return points

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
| 1. Existing core model — incorporated | Salary earnings; monthly and one-time instructions; draft and posted ledgers; relationships and operations. | A source-backed explanation of the model and resulting flow, followed by discussion confirming its meaning. |
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

All four [edition checkpoints](handbook-review.md#edition-checkpoints) are complete
for the conceptual edition. The final scenario review found no additional core
decision. Deferred work remains explicit below and in the review record.

The core model, ordinary changes/exceptions, joining/partial-period/exit ledger
flows, liability lifecycle, and annual information/review sequence are explained.
The code comparison includes matching and annual aggregation gaps. This is an
expanded working edition, not a claim that those workflows are implemented.

The [working-edition review](handbook-review.md) records the scope actually
covered and the continuous example. PAY-Q-016 is answered, and PAY-CORE-015 is
incorporated. Lifecycle outcomes are consolidated; PAY-Q-009 is approved as
PAY-CORE-007, including sealing in complete draft creation.
Concrete expiry/validation representations, detailed exception policies, role
assignments, and complete statutory issuance integration remain tracked work.
A production compliance guide would also need the applicable period/form scope;
this conceptual handbook does not adopt the demo's dated statutory examples as
universal rules.

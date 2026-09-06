# Handbook, payroll hub and Core baseline

Reviewed 2026-09-06. This records which evidence informs the handbook and where
later discussion refines it. It is a documentation reconciliation, not a new
payroll policy or a release approval.

## Which source answers which question

| Source | Authority and limit |
|---|---|
| [Recorded user decisions](decision-log.md) | Define the agreed handbook behavior, including later clarifications. Implementation choices and older designs do not silently override them. |
| [Canonical layered architecture](https://github.com/agentlabs-poc/agentlabs-hrms-design/blob/9762e25add7cb0991d35b958e3b28f15b2b46054/doc/design/payroll-layered-architecture.md) and [S03C ticket](https://github.com/agentlabs-poc/agentlabs-hrms-design/issues/34) | Establish the delivered Layer-1 boundary and its acceptance requirements. The older hub overview is historical where later decisions supersede it. |
| Core main `3a87931ea536c8b617e6e391c14affd03ade9f65` | Current remote baseline verified in this review. Includes the payroll promotion; it is the basis for future implementation comparisons. Source presence does not prove every later handbook decision is implemented. |
| Browser lab `737465d5e27888518018e9b1f28f75fcfcac0139` | The original conceptual experiment. PAY-GAP-001–008 describe this revision; they are not findings that Core main lacks all those controls. |
| Local Core branch `fix/payroll-ledger-schema`, code `5bc0b1a`, documentation `01268e5` | A tested local implementation candidate for PAY-DB-001–006. It has not been pushed or merged. Its tests and design choices do not close the handbook or approve new rules. Implementation is paused at the user's direction. |

The five named stores are domain concepts, not a requirement for five physical
SQL tables. Core's compensation, fact/instruction, calculation/candidate and
posted-ledger structures must be assessed by their behavior and relationships.
Do not rebuild accepted Core functionality just because its names differ from
the browser lab.

## What to carry forward from the hub

Business calculation supplies proposed amounts through granted APIs. Payroll
owns approved inputs, fixed reviewable money, protected posting and immutable
history. Every producer uses the same authority boundary. Lua, managed pipelines,
country formulas and a particular calculation engine are not prerequisites.

Retain exact approval, tenant and principal checks, exact-decimal amounts,
idempotent operations, non-writing simulation, correction history and
ledger-backed reports. Retain public CLI coverage and authenticated acceptance
against the exact Core commit being reviewed. Those requirements are grounded
in the [S03C acceptance gate](https://github.com/agentlabs-poc/agentlabs-hrms-design/issues/34),
not invented by this handbook pass.

## Reconciliation with later handbook decisions

| Area | Agreed handbook outcome | Relationship to baseline and later review |
|---|---|---|
| Manager intake and calculation | HR/payroll manager consolidates inputs through APIs; calculation supplies business amounts | Compatible with the hub's producer-neutral APIs. This does not authorize automatic attendance-to-payroll transitions or put business formulas into Core. |
| Draft creation | A usable complete draft is already fixed and sealed; visible ordinary flow is create → approve → commit | Existing API preparation, batch, validation and seal operations must map to that user-facing meaning. A low-level endpoint name does not create an extra approved business step. |
| Sources and commit | Immutable source content; expiry/replacement changes applicability; reconcile the complete relevant basis within commit | Preserve validation and instruction-application evidence. PAY-CORE-010 removes mandatory business-origin tracing, not authority checks or application identity. |
| Employee and batch | Exact employee-period draft is the approval/commit unit; a batch records independent outcomes | PAY-ARCH-002 resolves granularity left open in the older hub. Employee-month association needs no prescribed ID generator and does not authorize duplicate applications. |
| Authority | Input maintenance, preparation, approval and commit are distinct scoped capabilities | Core currently requires a different human actor and effective executor for approval. PAY-ARCH-003 does not require four people or direct removal of existing safeguards. Role-policy configurability has not been established. |
| Generated payroll and payment | Generated payroll is final; payment evidence does not reopen it | “As good as paid” describes payroll finality, not proof of a bank transfer. Corrections use a subsequent payroll month; corrections after exit belong to accounting. Existing correction APIs still need conformance review against these later scope rules. |
| Employer contribution and liability | Contribution earning and matching deduction enter payroll first; gross includes the contribution; one obligation follows | For salary 50,000 and contribution 1,000: gross 51,000, deductions 1,000, net 50,000; liability basis 1,000. Supplied remittance allocations settle only the paid amount with proof. Accounting and automatic allocation policy remain outside this rule. |
| Annual information | Payroll supplies the employee/employer/year package and settlement evidence; issuance consumes it | PAY-ARCH-005 adds the agreed package/handoff scope. Country formulas and statutory certificate issuance remain outside the generic ledger; the hub's deferred statutory work is not silently readmitted. |

The local candidate's signed liability credits, database layout, expiry encoding,
API names and transaction strategy are implementation choices. They must be
reviewed against these contracts later; their presence does not make them new
approved handbook concepts. In particular, credit presentation must preserve
payment proof and must not invent a refund or silently settle another obligation.

## Actual delivery and remaining hub work

- [Core PR #162](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/162)
  merged payroll Layer 1 on 2026-09-02 as `1362184`; current main `3a87931`
  includes it. Our local fix branch is based on that current main.
- [E2E PR #56](https://github.com/agentlabs-poc/agentlabs-hrms-e2e/pull/56)
  merged the initial CLI acceptance proof. Fresh post-merge proof is still
  pending in [E2E PR #57](https://github.com/agentlabs-poc/agentlabs-hrms-e2e/pull/57);
  its recorded live-proof blocker is local keyring unlock.
- Deferred Layer-2 source is preserved in draft
  [Core PR #163](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/163).
  GitHub marked historical #131 merged because its head is an ancestor of the
  extraction result; #163 explains why that did not restore Layer 2 to main.
- [Task #40](https://github.com/agentlabs-poc/agentlabs-hrms-design/issues/40)
  remains open for the residual/E2E work; [task #41](https://github.com/agentlabs-poc/agentlabs-hrms-design/issues/41)
  remains open for truthful closure of the S03 family and reduced hub. S04–S09
  are intended for deferred/out-of-scope closure, not delivery claims.
- [Design PR #44](https://github.com/agentlabs-poc/agentlabs-hrms-design/pull/44)
  is an open proposal for a later operator experience and product proof. Its
  admission follows reduced-hub closure and a new hub. This handbook review
  does not merge or implement that proposal.

Hub closure, handbook closure and release readiness are different checkpoints.
Historical proof of the merged baseline does not qualify the new local fixes.
The new settlement and employee-finalization APIs have no corresponding new CLI
commands in the local candidate; live acceptance for them and the separate
instruction-version API adapter defect remain implementation work. See the
[database review](database-table-review.md) for exact local evidence and limits.

## Current handbook gate

The agreed concepts, examples and later scope clarifications govern the
handbook. PAY-Q-020 remains the one recorded unresolved lifecycle proposal;
it is not approved by this reconciliation. Implementation remains paused while
that material decision and the consolidated handbook review are completed.
The [current review record](handbook-review.md#current-consolidated-review)
is the single place to check this edition's readiness.

# Joining, partial periods, exit, and annual reporting

**Policy scope under PAY-ARCH-006:** examples requiring approval and current-source
reconciliation describe [policy A](hrms-payroll-policy.md#policy-a-reconcile-current-inputs-before-commit).
Organizations may select [draft authority](hrms-payroll-policy.md#policy-b-the-fixed-draft-is-monetary-authority).
The [Layer-1 contracts](layer-1-contracts.md) preserve exact records and posting
under either workflow; the examples below do not mandate policy A universally.

Status: incorporation of existing agreements and source descriptions, with the
user-confirmed accounting boundary under PAY-Q-015. This chapter extends the
[ordinary payroll scenarios](payroll-scenarios.md). Illustrative amounts are
assumed calculation outputs, not payroll formulas or legal entitlements.

## Joining and the first payroll

**Derived from existing agreements:** PAY-INTAKE-001, PAY-CORE-002/009,
PAY-ARCH-001/002/003, and PAY-CORE-006-C.

The HR/payroll manager supplies the applicable employee salary facts and payroll
instructions through the established handoff. Calculation determines the
amounts appropriate to the employee and period, including any supplied joining
date or period information it needs. Payroll creates a fixed employee-period
draft, obtains approval, reconciles its basis, and commits the result.

Joining itself does not post salary. Salary entitlement is a fact used by
calculation; the first committed payroll amount is the result. Any applicable
one-time instruction is consumed at that commit, and monthly applications are
recorded under the existing rules.

**Lab evidence:** `joinDemoEmployee` creates one active employee with a fixed
joining date; `createDemoPayroll` creates salary and instruction entries.
Preparation occurs later. The inspected lab does not implement a general
joining-date selection or partial-month calculation policy.

## A partial-month payroll

**Derived from the calculation boundary, PAY-ARCH-001.** A shorter payable
period changes calculation inputs and amounts; it does not require a different
draft or committed-ledger primitive. The applicable business policy determines
which days and components count and how amounts are calculated.

For example, assume an employee's full monthly entitlement is INR 50,000 and
the producing calculation supplies INR 25,000 for the joining month. The salary
fact remains distinct from the INR 25,000 proposed earning. That amount enters
the fixed draft and, after approval/reconciliation, the committed payroll.
This example deliberately assumes the result; it does not select a day-count
divisor, rounding policy, or treatment of recurring instructions.

If the applicable facts change before commit, the draft is rebuilt and reviewed
under PAY-CORE-006-C. If a correction is required after generation, the adjustment
belongs to a subsequent month under PAY-CORE-011.

Why: business calculation can accommodate partial periods while the core keeps
the same stable proposal, approval, application, and finality rules.

## Exit and amounts supplied for settlement

**Existing-model consequence:** the producing layer determines the applicable
salary amount and any additional earnings or recoveries associated with exit.
The HR/payroll-manager handoff remains in place. Monetary proposals must pass
through the core's governed lifecycle under PAY-ARCH-001; describing an amount
as a settlement does not authorize direct posting or editing an earlier result.

Illustrative calculation output for the selected payroll period:

| Supplied component | Amount (INR) |
|---|---:|
| Applicable salary earning | 20,000 |
| Additional settlement earning | 5,000 |
| Recovery | -2,000 |
| Combined effect of these components | 23,000 |

This shows how supplied components fit a draft. It does not specify the legal
entitlement to any component, the calculation formula, the settlement deadline,
or whether a separate same-period run is permitted. Existing instruction-use
controls still apply, and previously generated payroll remains final.

**Source evidence:** at HRMS Core revision
`13621844165b31346facc53c4b45bbd8d9437816`,
[settlement.go](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/13621844165b31346facc53c4b45bbd8d9437816/internal/modules/payroll/settlement.go)
describes `FullFinalSettlement` as a historical projection and states that
governed calculations must create ledger entries before settlement views.
`GenerateSettlement` returns a pipeline-not-configured error for a valid employee
ID. This is evidence of an intended separation and an implementation limitation,
not a delivered settlement generator or a new adopted API.

## PAY-CORE-013 — a correction after employment has ended

**User-confirmed scope under PAY-Q-015.** Corrections arising after employee
exit are outside payroll and handled in accounting. The user rejected the
proposal to support a subsequent-month adjustment payroll for a former employee.

Example: an employee exits in September and September payroll is generated.
In October, a correction requires an additional INR 1,000. Handle that correction
in the external accounting process. Payroll does not create a new adjustment
run for the former employee, reactivate employment, or change September's
committed result.

Rationale: the former employee's later financial correction belongs to the
external accounting responsibility already established under PAY-ARCH-004.
Payroll does not need to add an after-exit eligibility exception or another
settlement path for that correction.

PAY-CORE-011's subsequent-month payroll adjustment rule applies within payroll's
scope. PAY-CORE-013 supplies the explicit after-exit boundary: the later correction
is handled outside payroll, while historical payroll remains final. The
employment-end components supplied for the exit payroll above are distinct from
this subsequent correction; their business calculations are not selected here.

**PAY-Q-015 — answered:** the user stated this should be out of scope and
corrected in accounting. The assistant's earlier recommendation to allow a
later payroll adjustment without employment reactivation is withdrawn. Detailed
accounting correction mechanics are outside this handbook's payroll scope.

## Annual reporting from payroll and the employer register

**Incorporated from PAY-ARCH-004/PAY-CORE-012 and the earlier source review.** The
employee payroll history provides recorded monthly earnings and deductions.
The employer-liability register provides obligations, remittances, and retained
proof such as challan references. The annual workflow brings these together with
the applicable annual tax details and official statement/certificate records.

| Information needed by the annual workflow | Existing basis |
|---|---|
| Employee's recorded payroll for the relevant year | Committed employee-period entries, including adjustments in the months where committed |
| Relevant employer obligations and their discharge | Payroll's employer-liability register and remittance/proof records |
| Annual salary/tax computation details | Higher-order calculation and the appropriate supplied annual facts |
| Official statement/certificate records | Applicable external statutory records, used by payroll's annual workflow |

This is a data-flow explanation, not a ruling on tax-year attribution of an
adjustment. Ledger posting month and statutory reporting treatment must not be
silently equated across every case.

For the Form 16 relationship, the [verified output chapter](payroll-outputs.md#form-16-a-supporting-basis-not-the-only-basis)
records the official sources and their scope. An internally reconciled liability
register supplies part of the basis; it is not by itself a complete certificate.
This chapter introduces no new filing dates, rates, or certificate rules.

**Lab evidence:** `createForm16` reads TDS liability/match records and salary
information from a payslip, then creates an explicitly incomplete readiness
package. It uses the first payroll reference for salary totals and cannot be
treated as a complete employee/year aggregation implementation. Its initial
data checks and missing-requirements list are source behavior, not a complete
production issuance workflow. See [main.ts](../src/main.ts) at lab revision
`737465d5e27888518018e9b1f28f75fcfcac0139`.

The [reporting and reconciliation chapter](reporting-and-reconciliation.md)
extends this data flow into a review sequence and worked examples, with the
matching/annual aggregation limitations recorded as PAY-GAP-007/008.

## Remaining coverage

PAY-Q-015 is resolved: after-exit corrections are handled in external accounting.
Detailed partial-period formulas remain with calculation policy. Complete
annual input selection, reconciliation, statutory attribution, and issuance
integration remain further handbook/implementation work. The scenarios above
do not imply that the lab implements any of these complete journeys.

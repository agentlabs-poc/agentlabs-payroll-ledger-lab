# Annual payroll package and issuance handoff

**PAY-ARCH-005 / PAY-Q-018 — approved.** The user agreed that this handbook
specifies the payroll-side annual package and its information handoff to the
certificate-issuance process. Detailed statutory issuance procedures belong in
a separate chapter for the applicable jurisdiction and financial year.

This specifies information and observable outcomes, not endpoint names or
canonical field/identifier formats. It extends the established payroll and
employer-register model without adding a source-origin tracing requirement.

## Package scope and contents

| Information | What the package must explain |
|---|---|
| Reporting scope | Which employer, employee, and reporting year/period the package describes, plus the cutoff at which its data was assembled |
| Payroll coverage | Which employee-month payroll results are included and which expected periods/results are missing or not yet established |
| Monetary detail and totals | Relevant committed earning/deduction entries and their month/component totals; gross, deductions, and net can be reconciled to those entries |
| Employer liabilities | The employee-related obligations arising from the included payroll, their settled amounts, and outstanding balances |
| Remittances and proof | Corresponding settlement allocations and retained proof, including partial settlements |
| Additional annual information | Supplied annual calculation facts and official records needed by the downstream issuance process; missing inputs stay identified |
| Handoff outcome | What data is provided to issuance, what remains incomplete, and which responsibility must supply or resolve it |

The reporting cutoff makes the package's balances interpretable. A later
remittance can change a later package's settlement view without rewriting the
earlier committed payroll. The exact cutoff representation and package identity
are implementation choices, not new canonical ID-generation methods.

Expected payroll coverage comes from the employee's relevant employment/reporting
context. Twelve months are not automatically expected for every employee. If
expected coverage is unavailable, the package must not claim verified annual
completeness merely because it contains some rows. Missing data is not silently
converted into a zero amount.

## Assembly and reconciliation

1. Establish the requested employer, employee, reporting period, and data cutoff.
2. Select the relevant committed payroll results. Keep all payroll belonging to
   an employee/month associated under PAY-CORE-015. Count each included committed
   monetary entry once; a payslip summary is not an additional monetary entry.
3. Reconcile component/month sums to the package's gross, deductions, and net.
   Include employer-contribution earnings and matching deductions as recorded
   under PAY-CORE-014; do not reinterpret payroll gross as taxable income.
4. Select corresponding liability and settlement records. Where a remittance
   covers multiple employees, use this employee's supplied allocations rather
   than the entire remittance amount. Retain proof and the remaining balances.
5. Check coverage and identify missing/inconsistent inputs. Current salary
   sources cannot replace historical committed payroll. Report problems to the
   responsible layer without changing finalized payroll to fit a desired total.
6. Hand the assembled information and its identified omissions to the applicable
   issuance process. A generated package or PDF does not itself establish that
   an official certificate has been issued.

Payroll posting period, settlement date, and statutory reporting attribution
are distinct. A remittance linked to an included liability is not automatically
irrelevant because its payment date is after that liability's payroll month;
the package must apply its declared scope/cutoff and retain correspondence.
Statutory attribution of cross-year corrections is supplied by the applicable
reporting/calculation layer, not invented by this aggregation contract.

## Worked balances and isolation

Assume supplied committed payroll for employee A at employer X in reporting
year Y contains twelve monthly gross amounts of INR 50,000. Assume the related
tax liabilities total INR 12,000, with INR 10,000 settled through corresponding
remittances/proof at the selected cutoff. These are illustrative records, not
a tax calculation or filing rule.

| Package observation | Correct result |
|---|---|
| A's annual recorded gross | INR 600,000, not the first payslip's INR 50,000 |
| A's related tax obligation | INR 12,000 |
| A's recorded settled amount | INR 10,000 with corresponding proof |
| A's outstanding liability | INR 2,000 remains outstanding under PAY-CORE-016 |
| Employee B's separate INR 720,000 annual gross | Excluded from A's package |
| A's prior-year INR 480,000 gross | Excluded from the current requested payroll scope |
| Repeated report reference to an already included entry | Does not increase monetary totals |

An additional INR 2,000 remittance with proof, included at a later cutoff,
brings the related outstanding balance to zero. A's recorded annual payroll
gross remains INR 600,000. Neither version of the package establishes statutory
issuance solely through its balances.

## Handoff responsibilities and acceptance

Payroll supplies committed monetary history and the employer register's
obligation/settlement evidence. Higher-order calculation and the relevant data
providers supply annual business/tax information. The applicable issuance
process consumes this information and applies its own jurisdiction/period
requirements. PAY-Q-018 does not move the employer register outside payroll or
select a new service architecture.

Acceptance evidence for the package must cover distinct employees, employers,
and reporting periods; multiple results in an employee/month; exact-once entry
aggregation; partial and later full settlement; missing expected coverage; and
an explicit distinction between package preparation and issuance. Existing
annual cases in [the operation contracts](payroll-operation-contracts.md#annual-package-established-contract-and-approved-scope)
provide the corresponding review checklist.

GAP-008 remains an implementation gap: the lab currently sums global TDS data
and takes one payslip's gross. Closing this handbook scope requires the package
contract and handoff above; closing the code gap requires verified implementation
of them. Complete statutory issuance is a separately scoped follow-on chapter,
not a hidden prerequisite for this approved payroll package.

Rationale: the annual package should faithfully assemble the records payroll
owns and expose what the issuance process still needs. The alternative was to
specify the full statutory procedure in this same pass. The user chose the
payroll package/handoff first, with statutory procedures addressed separately.

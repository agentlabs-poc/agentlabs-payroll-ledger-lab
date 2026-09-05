# Reporting and reconciliation across payroll records

Status: explanation of existing agreements and inspected code. The employer-only
contribution question PAY-Q-016 is separately proposed in the
[output chapter](payroll-outputs.md#pay-core-014--employer-only-contributions).
No new statutory formulas, deadlines, or certificate formats are selected here.

## Four results that answer different questions

| Result | What it establishes | What it does not establish |
|---|---|---|
| Committed employee payroll | Final employee-period money, as good as paid for payroll-core finality | That the employer has remitted every related government obligation |
| Settled employer liability | The corresponding obligation has been discharged by recorded remittance with proof | That every other liability or every annual reporting input is complete |
| Prepared annual report or readiness package | The data selected for the annual workflow and any identified omissions | That an official certificate has been issued |
| Issued statutory certificate | The output of the applicable issuance process | Permission to rewrite the committed payroll records it describes |

These distinctions follow PAY-CORE-001/011/012, PAY-ARCH-004, and the inspected
lab's explicit separation of a readiness package from issuance. The
[Form 16 explanation](payroll-outputs.md#form-16-a-supporting-basis-not-the-only-basis)
provides the official source basis for that certificate example.

## Reviewing the employer-liability register

The register explains the outstanding obligation and how the employer discharged
it. Read the obligation alongside its recorded remittance, amount, and proof
such as the challan reference. The correspondence is the important part of
PAY-CORE-012: the remittance closes the liability it actually settles.

Consider two employee-related liabilities for the same authority and reporting
period: INR 1,000 and INR 2,000. A remittance of INR 3,000 is recorded, with its
proof and the allocation supplied for those two liabilities. The two records
can each show their corresponding settled amount. The total of INR 3,000 alone
would not identify which obligations were discharged.

The lab illustrates this allocation shape with a grouped simulated deposit and
individual matches. This example does not choose an automatic allocation order
or a partial-payment policy; it uses a supplied, complete allocation. Concrete
validation and record representation remain implementation work.

## Preparing the annual information

This is a reading/review sequence derived from already described information
needs, not a newly mandated set of application states or APIs.

1. Identify the employee, employer, and reporting year for the output.
2. Assemble the relevant committed payroll entries and recorded component
   totals, preserving the months in which payroll actually committed them.
3. Assemble the relevant employer-liability, remittance, and proof records.
   Retain their correspondence rather than substituting a company-wide total
   for an employee's allocated information.
4. Bring in the annual tax/calculation information and official statement or
   certificate records required by the applicable reporting process.
5. Identify missing or inconsistent information in the preparation result.
   Resolve it in the responsible layer; do not silently alter finalized payroll
   to make an annual total look consistent.
6. Use the applicable issuance process once its requirements are satisfied.
   A locally generated preview/PDF remains a preview if issuance is incomplete.

The reporting treatment of a cross-year adjustment belongs to the applicable
tax/reporting rules. Its payroll posting month does not silently determine every
statutory attribution. Corrections after employee exit remain in accounting
under PAY-CORE-013; annual reporting does not create an exception to that scope.

## Example: totals that look complete but are not sufficient

Assume an employee has twelve committed monthly gross amounts of INR 50,000.
Their recorded gross for those entries totals INR 600,000. Separately, assume
the supplied TDS liabilities total INR 12,000 and are covered by recorded
remittances with proof. These are illustrative facts, not a tax calculation.

The annual workflow has payroll and TDS/deposit information for this example.
It must still account for the other annual information and official records
described in the applicable certificate process. It cannot infer that a
complete certificate exists just because those two totals are available.

Likewise, one month's INR 50,000 salary snapshot cannot represent the annual
INR 600,000 merely because the TDS total was summed across the year.

## Existing lab limitations

Evidence: [main.ts](../src/main.ts), lab revision
`737465d5e27888518018e9b1f28f75fcfcac0139`.

- `matchReconciliation` checks a payroll liability's already-matched total
  against its credit, but does not generally validate positive match amounts,
  available deposit balance, or compatible owner/tag/period across both sides.
  The guided demo supplies compatible full matches; the helper is not a
  complete general matching boundary.
- `createForm16` sums all stored income-tax-tagged credits and matches, then
  takes the first credit's payroll reference and that reference's payslip gross.
  It is not a complete employee/employer/year selection and aggregation routine.
- Its result is explicitly incomplete, and the example references are synthetic.
  Neither a balanced match total nor its generated PDF demonstrates verified
  remittance or completed official issuance.

See [PAY-GAP-007 and PAY-GAP-008](implementation-gaps.md#pay-gap-007--liability-matching-and-remittance-evidence)
for the implications. The observations are about the inspected demo and do not
claim the current production APIs behave the same way.

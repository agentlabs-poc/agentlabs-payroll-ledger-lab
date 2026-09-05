# Committed payroll and downstream records

**PAY-ARCH-004 / PAY-Q-014 — proposed; not approved.** This horizontal branch
starts from the consolidated [core model](core-concepts.md#agreed-core-model).
Generated/committed payroll is already final and as good as paid under
PAY-CORE-011. This proposal does not add another payroll-finality gate.

## Existing code

Source: lab revision `737465d5e27888518018e9b1f28f75fcfcac0139`,
[main.ts](../src/main.ts), especially `createPayslipSnapshot`, `downloadPayslip`,
`createStatutoryLiabilities`, and `matchReconciliation`.

The payslip snapshot selects posted entry IDs and computes totals for a payroll
reference. PDF generation renders those recorded amounts rather than calculating
salary again from current sources.

The liability routine selects tagged committed deductions and creates entries
owned by a demo legal entity, with references to the payroll entries. Separate
simulated settlement and matching records track those liability entries. The
code demonstrates distinct employee-payroll and employer-liability records; it
does not establish a complete production settlement or accounting system.
Its statutory examples are code evidence, not validated legal rules.

## Proposed responsibility boundary

| Consumer | Responsibility |
|---|---|
| Payslip | Present the employee's committed earnings, deductions, and net for the payroll reference. A PDF is a rendering of that result. |
| Payroll reports | Summarize committed entries for the selected employees and periods. Current salary or instruction sources do not recalculate historical payroll. |
| Employer-liability and accounting processes | Consume applicable committed components and maintain their own obligation, posting, or settlement records. Their own lifecycle does not reopen employee payroll. |

Payslips and reports describe payroll money. A liability ledger instead records
an obligation with its own balance and settlement events. It is not merely
another payslip layout, even where the opening amount comes from payroll.
Accounting and liability interpretation belong to the corresponding consuming
layer, rather than expanding payroll's salary/instruction primitives.

Identifying the committed payroll result being presented or consumed does not
require tracing that result back to upstream sources. PAY-CORE-010 remains in
force. Exact snapshot/reference formats, integration topology, retries, and
role assignments are not selected by this boundary.

## Rationale and example

Suppose September's committed payroll includes a deduction of INR 1,000 that
the consuming layer classifies as an employer remittance obligation. The
payslip presents the INR 1,000 deduction. The employer-liability process records
the corresponding obligation and later records its settlement. Those records
answer different questions while using the same committed payroll amount.

Employee payroll remains final throughout. The employer-liability settlement
does not establish or withdraw payroll finality. No new employee-payment status
is introduced into the core by this example.

If a later correction is required, its monetary adjustment belongs in a
subsequent month's payroll under PAY-CORE-011. Each downstream process then
interprets that later committed adjustment under its own rules; September's
payroll and payslip amounts stay unchanged. Exact legal/accounting treatment is
outside this conceptual decision.

Counterexamples: rebuilding a historical payslip using today's salary sources;
editing employee payroll to make a liability balance match a settlement; or
calling every downstream obligation settled merely because payroll was committed.

Keeping these responsibilities separate preserves a single authoritative payroll
result while allowing an obligation's own records to describe what happened
after generation. Folding settlement state into payroll finality would conflict
with the already agreed as-good-as-paid convention.

## Question and parked details

**PAY-Q-014:** Should payslips and payroll reports present committed payroll,
while employer-liability and accounting processes consume that result and
maintain their own records without changing finalized employee payroll?

Delivery/retry mechanisms, liability calculation rules, accounting mappings,
settlement evidence, annual outputs, and downstream correction handling remain
later topics. Approval of this boundary would not approve the demo formulas or
declare those integrations implemented.

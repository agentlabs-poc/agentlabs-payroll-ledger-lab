# Payroll scenarios from the established model

Status: incorporation of existing agreements and clearly described lab behavior.
These are handbook examples, not executed software tests or new domain rules.
The [main handbook](handbook.md) defines the concepts; this chapter applies them
across ordinary changes and exceptions without reopening settled questions.

## Agreed outcomes across scenarios

Amounts below are illustrative. Calculation determines applicable business
amounts; payroll does not detect business duplicates or require source tracing.

| Scenario | Starting facts and event | Expected payroll outcome | Established basis |
|---|---|---|---|
| Ordinary monthly payroll | Applicable salary is INR 50,000; a monthly allowance adds INR 1,500; a one-time bonus adds INR 5,000; a monthly deduction is INR 1,000 | Fixed draft gross is INR 56,500 and net INR 55,500. Commit records the final entries and instruction applications | PAY-CORE-001/003/004, PAY-ARCH-001 |
| Salary changes for a future month | September salary fact is INR 50,000; its replacement applies from October at INR 55,000 | October calculation uses its applicable facts. September's committed result is preserved. A change applicable only to October does not invalidate a still-valid September draft | PAY-SOURCE-001, PAY-CORE-001/006-C/009 |
| A finite instruction reaches expiry | Monthly INR 2,000 recovery is applicable September through January | Each eligible month can have its ordinary application. February cannot acquire an ordinary application outside that lifetime | PAY-CORE-002/004/005 |
| An eligible month is processed late | January remains unprocessed and the same instruction expired after January | Processing January in February does not itself exclude January's eligible application, subject to all other controls | PAY-CORE-004/005 |
| A draft containing a one-time bonus is abandoned | An uncommitted draft includes INR 5,000 bonus | Abandonment creates no posted bonus and consumes no instruction. A replacement draft can use it if still applicable | PAY-CORE-003 |
| Applicable facts change during review | Reviewed draft includes INR 5,000 bonus; applicable facts change to INR 6,000 before commit | The old draft's amounts stay fixed. Reconciliation blocks its commit; cancellation/rebuild and fresh review produce the new proposal | PAY-CORE-006-C/009 |
| One employee's draft is stale in a batch | A batch has 100 reviewed drafts and one fails reconciliation | The other 99 may commit if valid. The batch retains the outstanding result; a rebuilt draft requires fresh approval | PAY-ARCH-002/003 |
| A correction arrives after payroll generation, while still within payroll scope | September committed a bonus of INR 5,000; a subsequent correction requires INR 500 recovery | September stays final. A subsequent month's governed payroll includes INR -500; prior instruction consumption is not automatically undone | PAY-CORE-001/011 |
| Employer remits the government liability | Payroll's employer register has INR 1,000 outstanding; employer remits INR 1,000 with a challan reference | Record the remittance and proof against the corresponding liability, closing the settled obligation while retaining history | PAY-CORE-012, PAY-ARCH-004 |

PAY-CORE-013 places corrections after employee exit outside payroll, in
accounting; the subsequent-month payroll adjustment row above does not override
that boundary.

## Worked change over three months

This illustration concerns one salary component and one finite instruction;
other components are omitted so it does not imply a complete real payslip.
Assume the ordinary monthly calculations produce the full illustrative salary
amount and an INR 2,000 recovery instruction applies only in September/October.

| Payroll month | Applicable salary amount | Instruction effect | Combined illustrated effect |
|---|---:|---:|---:|
| September | INR 50,000 | INR -2,000 | INR 48,000 |
| October, after salary replacement | INR 55,000 | INR -2,000 | INR 53,000 |
| November, after instruction expiry | INR 55,000 | None | INR 55,000 |

Each month has its own fixed draft and commit. October uses the replacement
salary facts rather than rewriting September; November excludes the expired
instruction rather than removing its September/October history. The example
does not select an installment-extension or catch-up policy.

Why this matters: changes in current facts affect applicable future payroll,
while final past payroll remains stable. A temporary recovery expires without
altering salary entitlement.

## Reconciliation before commit and reconciliation of liabilities

These are two different checks within payroll, each already established:

| Check | Question it answers | Consequence |
|---|---|---|
| Before employee payroll commit | Is the approved draft still valid against the applicable facts and instruction applications? | Commit the reviewed amounts if valid; otherwise rebuild and review |
| Employer-liability settlement | Which outstanding obligation has the employer discharged through the recorded government remittance and proof? | Close the corresponding settled liability and retain its history |

The second check does not reopen or defer the first result. Employee payroll
is already as good as paid for core finality; the employer register records the
separate obligation to the authority. Accounting remains external.

## One deposit covering several employee liabilities: existing lab behavior

**Code description only.** At lab revision
`737465d5e27888518018e9b1f28f75fcfcac0139`,
[main.ts](../src/main.ts), `payAndReconcileChallans` groups liability credits by
statutory tag, creates a simulated deposit for the total, and matches each
credit to that deposit. `matchReconciliation` retains each matched amount.

For an illustrative INR 1,000 credit and INR 2,000 credit with the same tag,
this code shape produces an INR 3,000 simulated deposit and two matches. It
demonstrates a grouped deposit with individual allocations, rather than
requiring a different challan for every employee.

The demo creates synthetic references and assumes its guided dataset. It does
not establish production allocation rules across employers/periods, partial
payments, sufficient deposit-balance checks, or verified remittance evidence.
Those details are not adopted by incorporating this description. The user-
confirmed rule remains closure of the corresponding liability when remittance
and proof are recorded.

## Coverage that remains to develop

The [extended journeys](employee-and-annual-journeys.md) now explain joining,
supplied partial-period amounts, exit-related components, and annual data flows
within the established model. PAY-CORE-013 places after-exit corrections in
external accounting, resolving PAY-Q-015. Complete calculation policies and annual issuance
remain further work, rather than behavior selected by these examples.

The [implementation gaps](implementation-gaps.md) remain applicable: in
particular the demo does not fully enforce effective selection, cross-draft
instruction usage, immutable drafts, or protected reconciliation. These
scenario outcomes describe the agreed handbook model, not delivered behavior.

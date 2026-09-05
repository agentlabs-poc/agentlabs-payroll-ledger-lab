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

## Employer contribution through payroll

**Agreed under PAY-CORE-014.** An employer contribution included in CTC is an
earning plus a matching deduction. With INR 50,000 other earnings and an
INR 1,000 contribution, gross is INR 51,000 and total deductions are INR 1,000,
leaving INR 50,000 net. Both entries pass through the governed Payroll Ledger;
the corresponding INR 1,000 employer obligation follows in the liability
register. Remittance with proof then closes that liability.

This is not a direct liability entry that bypasses payroll or leaves gross
unchanged. See [the rationale and code comparison](payroll-outputs.md#pay-core-014--employer-contributions-through-payroll).

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

## End-to-end payroll and liability walkthrough

**Illustration of existing agreements**, including PAY-CORE-014. Assume the
producing layer supplies all amounts below for one employee's September
payroll. The employer contribution and tax deduction in this example are both
payable to their respective government authorities. No contribution/tax rate
or offer-letter parsing rule is being selected.

| Proposed payroll component | Kind | Amount (INR) |
|---|---|---:|
| Other salary entitlement components | Earning | 50,000 |
| Employer contribution included in CTC | Earning | 1,000 |
| Monthly allowance instruction | Earning | 1,500 |
| One-time bonus instruction | Earning | 5,000 |
| Monthly recovery instruction | Deduction | -1,000 |
| Matching employer-contribution deduction | Deduction | -1,000 |
| Supplied tax deduction | Deduction | -2,000 |
| Gross | Summary of earnings | 57,500 |
| Total deductions | Summary of deductions | 4,000 |
| Net | Gross less deductions | 53,500 |

All seven components belong to the same employee-month payroll association
under PAY-CORE-015. No canonical ID format is required by this walkthrough;
the grouping remains distinct from individual draft and entry identifiers.

### Preparation and review

The manager consolidates the applicable facts/instructions through the payroll
APIs. Calculation produces these amounts. The fixed employee-period draft
includes sealing under PAY-CORE-007 and contains the seven monetary components;
summary rows are not extra monetary
entries. The contribution appears in both gross and deductions, so it is
represented without changing net by itself.

Approval accepts the exact draft. If the applicable basis changes before
commit, protected reconciliation blocks that draft and it is rebuilt for fresh
review. For this walkthrough, assume reconciliation succeeds.

### Commit and employee result

Commit records the seven components in the Payroll Ledger and records the
instruction applications. The one-time bonus is consumed; the applicable
monthly instructions record their September applications. Their future
eligibility follows their existing expiry and application rules.

September's payroll is generated and final, with INR 53,500 net. The payroll
result and its payslip presentation retain the INR 57,500 gross, including the
employer-contribution earning. No new employee-payment confirmation gate is
introduced by the rest of this walkthrough.

### Employer register and remittance

The corresponding employer liabilities follow the committed payroll entries.
The contribution's earning and matching deduction represent a single INR 1,000
obligation. They do not create two INR 1,000 liabilities.

| Liability represented in this example | Amount (INR) | Recorded settlement |
|---|---:|---|
| Employer contribution to its authority | 1,000 | INR 1,000 remittance with the corresponding contribution challan/proof |
| Tax deduction to its authority | 2,000 | INR 2,000 remittance with the corresponding tax challan/proof |
| Combined illustrated obligations | 3,000 | Separate proof/allocation retained for each corresponding obligation |

Each liability closes when its corresponding remittance and proof are recorded.
The different obligations do not substitute for one another merely because the
combined remittance total is INR 3,000. The ordinary recovery line does not
become a government liability merely because it is a payroll deduction.

This example specifies complete corresponding remittances; it does not choose
a partial-payment allocation policy or a bank-integration mechanism. Proof
references are illustrative record descriptions, not actual challans.

### Later correction and annual use

If the employee remains within payroll scope and the September bonus requires
INR 500 recovery, a subsequent month's governed payroll includes INR -500.
September stays unchanged. If the correction arises after exit, external
accounting handles it under PAY-CORE-013.

For annual work, use the relevant committed monthly information and the employer
register's corresponding remittance/proof records, together with the required
annual calculation and official records. Do not reconstruct September from
current salary sources or treat this one month as a complete annual record.
The [reporting chapter](reporting-and-reconciliation.md) separates those inputs
from certificate issuance and records the inspected lab's aggregation limits.

### Why this walkthrough closes the conceptual loop

The offer-letter contribution, employee gross/deductions/net, employer
obligation, and remittance closure are successive uses of the same monetary
model. They require no direct-to-liability contribution bypass and no reopening
of generated payroll. General accounting remains outside payroll; the
employer-liability register remains inside it.

This is a handbook walkthrough, not an executed end-to-end software test. The
[implementation gaps](implementation-gaps.md) identify where the lab only
illustrates or fails to enforce the agreed behavior.

The [final checkpoint review](handbook-review.md#final-walkthrough-results) follows
this same employee through both unchanged and changed-basis branches and records
the resulting amounts, responsibilities, and remaining limits.

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

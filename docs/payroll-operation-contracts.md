# Payroll operation contracts

Status: specification of observable behavior derived from recorded agreements.
This extends the [gap-closure acceptance cases](gap-closure-work.md). It does
not select canonical identifiers, endpoint names, tables, legal calculation
rules, or a new role policy. Implementation gaps remain open until actual
behavior is implemented and verified.

## Information required by the operations

These are meanings the implementation must preserve, not prescribed field names.

| Information | Required meaning | Existing basis |
|---|---|---|
| Payroll scope | The employer/tenant, employee, and target payroll month to which the operation applies | PAY-ARCH-002/003, PAY-CORE-015 |
| Draft identity | The exact fixed proposal being approved, cancelled, or committed; distinct from employee-month grouping | PAY-ARCH-002, PAY-CORE-007/015 |
| Proposed entries | Complete earning/deduction components supplied by calculation, retaining their fixed reviewed amounts | PAY-ARCH-001, PAY-CORE-001/006-C |
| Applicable basis | Enough validation evidence to determine whether all relevant inputs and dependencies still apply at commit | PAY-CORE-006-C/010; no mandatory per-entry source-origin graph |
| Instruction applications | Which one-time or monthly instructions the commit applies, in the correct scope/period | PAY-CORE-003/004; representation is distinct from business-source tracing |
| Approval | Acceptance of the exact draft by an actor with the applicable capability | PAY-ARCH-003 |
| Correction relation | The prior final payroll result being adjusted, and the later payroll month in which the supplied adjustment is committed | PAY-CORE-001/011/013 |
| Liability settlement correspondence | The obligation, remitted amount, proof, and amount applied to that obligation | PAY-CORE-012/016, PAY-ARCH-004 |

Recognizing application of the same instruction does not authorize payroll to
infer whether two different instructions are the same business request.
The manager/producing layer supplies business intent under PAY-CORE-008.
Likewise, choosing a storage key for these operations does not create a
canonical ID-generation requirement.

## Instruction eligibility and application

For a target employee/month, calculation uses applicable salary facts and
eligible instructions. A standing instruction has its supplied lifetime; a
one-time instruction has its applicable scope and unconsumed status. Source
expiry/replacement preserves history. Evaluation uses the target payroll period,
not the date on which the operator presses a button.

The September-through-January loan example establishes those five eligible
months. It does not require counting five successful deductions and extending
the end date after a skipped month. If the business needs a changed repayment
arrangement, that belongs to the producing layer and must enter payroll through
the existing instruction flow. No automatic extension is specified by this
contract. Concrete date encoding must faithfully preserve the supplied lifetime.

| Point in lifecycle | One-time instruction | Monthly standing instruction |
|---|---|---|
| Preparation or draft creation | No committed consumption | No committed monthly application |
| Approval | No committed consumption | No committed monthly application |
| Cancellation before commit | This draft consumes nothing | This draft records no application |
| Successful commit | Record consumption by the committed result | Record one ordinary application for that employee/month |
| Repeat/competing commit | No second consumption or overwrite of the first | No second ordinary application in the same employee/month |
| Another eligible month | Already-consumed one-time instruction stays consumed | The instruction can apply again within its lifetime |

Availability after cancellation remains subject to current applicability and
other commits. Partial application, restoration, and skipped-period recovery
are not implied by a cancelled draft or an unprocessed month.

## Create, approve, cancel, and commit

| Operation | Preconditions and input | Successful outcome | Rejection or recovery outcome |
|---|---|---|---|
| Create complete draft | Preparation capability; selected payroll scope; complete calculated proposal with a consistently established basis | One fixed draft, including sealing, ready for review | An incomplete/inconsistent proposal cannot be exposed as a complete reviewable draft; no final payroll or application follows from preparation failure |
| Approve | Approval capability for that scope; exact uncommitted draft | Approval belongs to the fixed proposal | Another draft, changed amounts, or batch membership cannot inherit this approval |
| Cancel uncommitted draft | Applicable cancellation authority; draft has not committed | Draft cannot later commit; monetary proposal is preserved as cancelled history; no consumption by cancellation | A committed result cannot be cancelled through this operation. An uncertain commit must be resolved before treating it as uncommitted |
| Commit | Commit capability; approval of the exact draft; full basis/applications valid within the protected posting boundary | Final entries and instruction applications recorded for that draft, with corresponding payroll outputs | Changed/invalid basis blocks posting and requires rebuild/fresh review; retry cannot duplicate the result |

Cancellation authority is supplied by operating authorization policy. The
capability separation decision does not assign it to a particular job title or
automatically grant it to every preparer. This contract specifies the outcome
once the operation is authorized; no new role assignment is adopted.

### Protected commit sequence

The following is the observable consistency contract, independent of transaction
technology:

1. Establish the draft's existing outcome. If already committed, preserve and
   report that result; do not create another one.
2. Check the exact draft, applicable authority, and approval. A cancelled draft
   cannot become committed through a retry.
3. Validate the full relevant basis for the same employee/period, including
   applicable additions, replacement/expiry, and instruction applications.
4. Publish the final monetary result and applications under the same protected
   boundary, preventing conflicting changes between validation and posting.
5. Make the outcome discoverable for retries/recovery. A lost response is not
   evidence of failure; recovery must establish whether the result exists.

These steps describe one consistency boundary, not separately exposed API calls.
A checksum over the proposed amounts alone cannot establish step 3. Historical
source IDs alone cannot detect a newly applicable instruction. Validation must
cover what can change the relevant basis while allowing unrelated changes to
continue. The exact validation representation and concurrency technology remain
implementation choices subject to these outcomes.

If the basis changes, commit does not recalculate or replace reviewed amounts.
Cancel the old uncommitted draft, calculate from the applicable basis, create
the replacement including sealing, and obtain fresh approval. This also applies
when the stale draft was already approved. Sources are not frozen throughout
the review window.

Batch coordination records each employee draft's actual outcome. An exception
for one employee does not authorize rewriting another employee's committed
result or presenting a partially completed batch as complete.

## Corrections

The manager/producing layer supplies the adjustment amount and relevant prior
payroll relation. Within payroll scope, the adjustment enters a subsequent
month's ordinary governed lifecycle. Generated payroll remains unchanged;
approval, reconciliation, and application controls still apply. After-exit
corrections belong in accounting under PAY-CORE-013.

The correction relation identifies the final result being adjusted. It is not
a mandatory trace to attendance, an external service, or another business-source
origin. No automatic restoration of prior instruction eligibility follows from
posting a correction.

## Liability settlement and balances

The original liability comes from committed payroll. A supplied settlement
identifies the corresponding remittance, proof, obligation, and applied amount.
The register must retain that correspondence and its history.

For each obligation, the settled amount is the sum of its valid recorded
settlement allocations. The outstanding liability is the original obligation
less that settled amount. Under PAY-CORE-016, a positive remaining balance stays
outstanding; full settlement closes the obligation. Employee payroll remains
final before and after either event.

For a remittance covering several obligations, recording supplied allocations
must not use more than the remitted amount or more than an obligation's unpaid
amount. Nonpositive, duplicate, incompatible, or excess allocations cannot
produce false closure. These controls implement correspondence; they do not
choose which employee should be settled first.

An allocation's scope must correspond to the actual employer and obligation.
Compatibility for a particular authority/reporting period follows the supplied
remittance evidence and applicable integration rules. The lab's hardcoded
same-tag/period demo is not a universal cross-period payment rule.

Worked supplied allocations: obligations A and B are INR 10,000 and INR 5,000.
An INR 9,000 remittance is accompanied by allocations of INR 6,000 to A and
INR 3,000 to B. A remains INR 4,000 outstanding; B remains INR 2,000 outstanding.
Total outstanding is INR 6,000, and the remittance has no unused amount to apply
again. This example uses an explicit split; it does not select an automatic
allocation policy. Excess deposits and external accounting treatment are not
invented by the balance equation.

## Annual package: established contract and approved scope

The current information contract identifies an employer, employee, and reporting
period; assembles the relevant committed payroll and corresponding liability,
remittance, and proof data; and reports missing annual calculation/official
inputs. Multiple payroll results belonging to an employee/month must remain
associated, with each committed monetary entry counted once. Merely summing
every stored TDS record or using the first payslip cannot satisfy this contract.

The following are review cases for the known aggregation limitation:

- Two employees with different annual gross must receive distinct totals;
  neither receives the other employee's payroll or remittance allocation.
- The same employee's records for different employers/reporting years must
  be selected within the requested scope.
- Several relevant payroll results for one month contribute their own entries;
  their shared association or repeated inclusion in a report must not count an
  entry twice.
- Twelve supplied monthly gross amounts of INR 50,000 total INR 600,000. A
  first-payslip gross of INR 50,000 is not the annual total.
- A partial remittance retains the settled amount, proof, and unpaid liability;
  the package does not report that obligation as fully settled.
- Missing annual or official inputs remain identified as missing. A package
  containing payroll totals is not itself evidence of certificate issuance.

These cases specify payroll data selection and truthful representation. Legal
tax-year attribution, statutory calculations, and complete issuance require the
applicable reporting process. PAY-Q-018 is approved as PAY-ARCH-005: this
handbook specifies the payroll annual package and issuance handoff. Detailed
statutory procedures are a separate jurisdiction/year chapter. See the
[package specification](annual-payroll-package.md) for scope, coverage, balances,
and acceptance evidence.

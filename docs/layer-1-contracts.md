# Layer-1 payroll records and contracts

**Current conceptual contract under PAY-ARCH-006.** This chapter defines what
the payroll core owns. The [HRMS payroll policy](hrms-payroll-policy.md) defines
how an organization uses these capabilities. These are semantic contracts,
not a claim that current Core or the local fix branch implements every operation.

## Records and their meaning

| Record | Layer-1 meaning |
|---|---|
| Salary entitlement | Effective employee earning entitlement, distinct from money committed for a payroll month |
| Standing instruction | A recurring payroll direction with a declared applicability period and expiry; it may generate an earning or deduction |
| One-time instruction | A direction with a single-use application contract; preparing a draft does not consume it |
| Fixed draft | A complete, identifiable monetary proposal for one employee and payroll period; creation includes sealing its content |
| Draft controls and evidence | Authorized approval, hold or other supported workflow records associated with the exact draft, with retained history |
| Payroll Ledger | Immutable committed entries recording the actual payroll result |
| Instruction application | Evidence of an instruction's effect in committed payroll; recorded atomically with that effect |
| Employer-liability register | Obligations arising from payroll, actual remittances with proof and corresponding settlement allocations |
| Employee-month association | All payroll for the same employee/month within its employer/tenant context belongs together; no canonical number generator is prescribed |

These are concepts rather than a prescribed SQL table count. Sources, fixed
drafts and posted money answer different questions and must not be confused.
Source expiry/replacement preserves old content; it does not rewrite a draft
or committed money. Different drafts retain their own identities even when
they belong to the same employee-month association.

## Monetary and authority guarantees

1. A usable complete draft has fixed content. A changed monetary proposal is a
   new draft/revision, not an invisible edit under the old identity.
2. Approval evidence, when used, identifies the exact draft. Approval of one
   draft does not silently approve replacement amounts or other batch members.
3. Mutations require the appropriate tenant/employee scope and granted
   capability. An agent, manager or calculator receives no posting bypass.
4. Commit posts the exact selected draft. Its monetary entries and instruction
   applications succeed together or do not post. A lost response or retry must
   not create another result.
5. Active holds and applicable approval requirements are honored. The upper
   layer selects the policy through authorized controls; an arbitrary commit
   request cannot simply claim those controls do not apply.
6. Posted history is immutable. Corrections are additional linked records;
   reports and payslips derive values from committed entries, not new formulas.
7. Money and currency are represented exactly. Gross, deductions and net derive
   from the actual entries, including both halves of a represented contribution
   pair; supplied totals do not override the ledger.

The scope and enforcement of the existing single-use/monthly instruction
contracts remain in force. Making a draft authoritative for its monetary
amounts does not permit applying an already consumed one-time instruction or
recording a second ordinary monthly application. Conversely, checking those
application constraints is not a requirement to compare every current source
with the source set used to produce the draft.

## Draft operations are capabilities, not one mandatory workflow

| Capability | Core result | What organizational policy chooses |
|---|---|---|
| Create a complete draft | Fix the proposal and give it an exact identity | Producer, calculation rules, input cutoff and readiness workflow |
| Record approval | Retain authorized acceptance of that draft | Whether approval is required, approvers and separation-of-duty policy |
| Hold or release a draft | Retain the control and its authorized history; a held draft is unavailable for commit | Reasons, who may act, and conditions for release |
| Cancel an uncommitted draft | Prevent later commit and preserve its history; cancellation consumes nothing | When to cancel rather than hold or retain the proposal |
| Inspect/reconcile | Expose the fixed draft and relevant records so the selected policy can assess them | Whether current-source comparison is required and how to respond to differences |
| Commit selected draft | Apply the applicable controls and record the exact result atomically | Which eligible drafts to select and when to commit |

Approval and hold need not be a single mutually exclusive field. Separate
approval evidence and hold status can preserve both facts, but the exact state
representation and public interfaces are implementation design. This handbook
does not choose a database enum or claim a hold endpoint already exists.

Likewise, optional approval is a policy capability of the conceptual model,
not a claim that current Core supports approval-free commits. Existing Core
requires separate maker/checker identities. Changing that behavior requires
subsequent implementation design and review; no safeguard is disabled here.

## Sources and freshness

Layer 1 preserves immutable source history, the fixed draft and the evidence
needed by its operations. Layer 2 chooses whether the current applicable
sources must still match at commit.

- Under a **reconcile-before-commit policy**, relevant changes block or hold
  the draft. If its amounts must change, the workflow creates a replacement
  and applies its review policy again. Any claimed freshness check must be
  effective at the commit boundary; an earlier report alone cannot guarantee it.
- Under a **draft-authoritative policy**, the fixed draft is the selected
  monetary authority. A later source change does not by itself force a rebuild.
  Exact content, authorization, holds, required approval, instruction application
  constraints, atomic posting and history remain protected.

Neither policy requires a day-long source freeze. Neither makes business-origin
tracing or inference of duplicate business requests a core responsibility.
PAY-CORE-010 removes that origin-tracing requirement; it does not remove draft
identity, approval history, application records or authorization evidence.

## Batches and finality

The employee-period draft is the unit of monetary commit. A batch selects and
coordinates drafts and reports each outcome. Holding or excluding employee B
must not change employee A's committed result. If 99 selected drafts commit and
one remains held, the records show those exact outcomes. A completed selection
of 99 is not evidence that the held employee's payroll is complete.

Commit makes payroll final. “As good as paid” describes that finality; it is
not proof that a bank transfer occurred. The handbook's chosen correction policy
uses a subsequent payroll month while the employee is within payroll scope;
after-exit corrections belong to accounting. See the policy chapter for that
retained organizational boundary. No workflow may rewrite posted history.

## Liabilities and outputs

Employer liabilities remain inside payroll; general accounting remains outside.
A corresponding obligation follows the posted payroll entries. A represented
employer-contribution earning/deduction pair has one liability basis, not two.

A supplied allocation settles only its amount against the corresponding
obligation and proof-bearing remittance. It cannot overdraw either balance,
reuse paid money, or settle an unrelated obligation. Partial payment leaves the
unpaid amount outstanding. The core preserves both the original obligation and
settlement history. Policy/integration supplies the allocation and proof; the
core does not choose an automatic settlement order or invent refunds.

The [annual package](annual-payroll-package.md) assembles scoped committed money,
liabilities, settlement evidence and missing-input information. Business/tax
calculation and official certificate issuance remain outside the generic ledger.
A report or PDF does not become a new monetary authority.

## How to review implementation later

Use current Core main as the baseline. Compare each contract with actual
API/CLI behavior and exact-version acceptance evidence. Keep the browser-lab
findings and local fix candidate separate. Neither an existing endpoint nor a
passing local test selects an organization's workflow.

The existing hub requires a granted public API/CLI journey, exact candidate and
server identity, tenant/permission denials, replay, atomic failures and immutable
history proof. Later work must extend that evidence to any newly introduced
controls. This chapter does not restart implementation or approve a release.

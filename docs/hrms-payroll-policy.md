# HRMS payroll policy — organizational ground rules

**Layer 2 under PAY-ARCH-006.** This chapter explains the workflow choices an
organization can publish as its HRMS payroll policy. It preserves the user's
operating account and earlier examples without making every choice a universal
Layer-1 requirement. The [Layer-1 contracts](layer-1-contracts.md) define the
records and guarantees both policy variants use.

No employer-specific approver list, cutoff calendar or legal calculation is
invented here. A published organization policy must state its selected behavior;
examples below do not silently select one variant for every organization.

## Policy subjects and retained ground rules

| Subject | Organizational policy and current handbook position |
|---|---|
| Manager intake | In the supplied operating account, source information reaches an HR/payroll manager who consolidates inputs through APIs. Attendance does not directly advance payroll internally. |
| Calculation | The producing layer supplies applicable business amounts and maintains its calculation rules. Core sums and protects the resulting records. |
| Instructions | The manager/business layer supplies intent, cadence, amount and lifetime. The five-month loan example has finite applicability; no automatic recovery extension is implied. Core preserves the declared instruction/application semantics. |
| Preparation | Decide when inputs are ready and create the complete fixed employee-period proposal. A calculation preview alone is not a payroll result. |
| Approval | Specify whether approval is required, who may give it, and organizational separation of duties. Required approval must identify the exact draft; role composition is not universal. |
| Approval withdrawal | Choose the effect on an uncommitted draft: hold it, retain it for fresh approval, or cancel/rebuild. PAY-Q-020 is superseded as a core question; this chapter does not mandate one alternative. |
| Hold and release | Specify who may hold/release and how the organization resolves the reason. An active hold excludes the draft from commit; history remains available. |
| Current-source freshness | Select whether to reconcile current inputs before commit or accept the fixed draft as monetary authority. Both are described below. |
| Batch selection | Select eligible drafts and decide how to follow up exclusions. Held drafts remain outstanding even when the selected drafts have committed. |
| Corrections | Retain the user's selected rule: adjustments in a subsequent payroll month within payroll scope; corrections arising after exit go to accounting. Layer 1 protects the original committed history. |
| Employer contribution | Retain the user's CTC treatment: earning plus matching deduction, gross including the contribution, unchanged net effect, one corresponding employer obligation. |
| Remittances | Supply actual paid amounts, proof and explicit allocation to the corresponding liabilities. The unpaid remainder stays outstanding; automatic allocation, overpayment/refund treatment and accounting are not selected here. |
| Annual handoff | Assemble the approved payroll-side package with declared employee/employer/year/cutoff scope and missing inputs; detailed statutory issuance remains separate. |

Retained user decisions remain the handbook's chosen examples and boundaries;
this layer distinction does not silently replace them with different correction,
contribution, repayment or accounting policies.

## Policy A: reconcile current inputs before commit

This is the earlier PAY-CORE-006-C flow, now correctly located as a policy.
Assume this organization requires approval of its exact draft.

1. The manager consolidates applicable inputs; calculation produces the amounts.
2. Create the complete fixed draft and obtain the policy's required approval.
3. Reconcile the relevant applicable basis and instruction applications as part
   of the protected commit boundary.
4. If it still matches and the draft is eligible, commit the exact draft.
5. If it differs, block/hold that draft. If the money must change, cancel or
   supersede the uncommitted proposal, create the replacement, and obtain the
   required approval of that replacement.

A report reviewed hours before commit is not sufficient if the policy promises
current-source freshness at commit. Layer 1 must supply an operation capable
of honoring the policy's check at that boundary. How the requirement is encoded
and enforced is later implementation design.

**Example:** a September draft includes a 5,000 bonus. Before commit the
applicable source becomes 6,000. Under this policy the old draft cannot proceed
on its earlier basis; the replacement includes the supplied 6,000 and receives
fresh approval. The original draft's amounts and review history are preserved.

Rationale: this policy favors incorporating relevant latest facts before money
becomes final. Its cost is held drafts and repeated review when inputs change.

## Policy B: the fixed draft is monetary authority

Assume another organization uses its prepared/reviewed draft as the monetary
cutoff. Approval, if required by its policy, still belongs to that exact draft.

1. Consolidate inputs and create the complete fixed draft.
2. Complete whatever review/approval that organization requires.
3. Hold any draft that the authorized workflow decides should not proceed.
4. Select unheld eligible drafts and commit their exact content. A later source
   change alone does not invalidate the selected monetary authority.

**Same example:** the fixed September draft contains a 5,000 bonus, and the
source later becomes 6,000. This policy can commit the unchanged 5,000 draft
if its other controls pass. It does not silently insert 6,000. Under the
handbook's subsequent-month correction rule, a required later adjustment is
supplied through that later month's governed flow.

Rationale: this policy makes the reviewed draft a stable cutoff. Its cost is
that later facts may need a later adjustment. It does not permit a held draft,
unauthorized posting, a duplicate instruction application or alteration of
committed money. It is not a claim that current Core already supports this mode.

## Hold and approval examples

A manager prepares 100 employee drafts. One requires clarification and is held.
The upper-layer workflow excludes it and selects the other 99. If their own
controls pass they can commit. The held draft retains its fixed content and
history, and remains outstanding; it is not counted as generated payroll.

An approved draft may subsequently be held. Retaining both approval evidence
and the hold makes the reason for non-posting visible without erasing history.
On release, the organization's policy may require fresh approval or allow the
existing exact approval to remain sufficient. This is precisely why PAY-Q-020
has no mandatory answer in Layer 1.

If money changes, it is a replacement proposal and old approval does not
transfer. If the original already committed, neither release nor withdrawal
can turn it back into editable payroll. These are Layer-1 integrity boundaries,
independent of the organization's workflow preference.

## Applying the policy to liabilities and annual information

For salary 50,000 plus employer contribution 1,000, the selected treatment
produces gross 51,000, deductions 1,000 and net 50,000, with one 1,000 obligation.
Approval and freshness choices do not alter the arithmetic or create another
liability for the other half of the pair.

For an obligation of 10,000, an allocated remittance of 6,000 with proof settles
6,000 and leaves 4,000 outstanding. A later allocated remittance of 4,000 closes
that balance; both proofs remain. Policy supplies the allocation, not an
unsupported assertion that the whole liability was paid.

Annual information uses committed entries and corresponding settlement evidence
at the package cutoff. Later remittance may change a later package's balance
view without rewriting payroll. Organization workflow and reporting adapters
resolve missing inputs; the package does not fabricate zero amounts or official
certificate issuance.

## Policy and implementation are different records

This handbook publishes the policy subjects, two valid freshness variants and
worked outcomes. A deployment chooses and authorizes its policy; no universal
organization choice is pending before the Layer-1 model can be understood.
PAY-Q-020 is closed as superseded, with [rationale](payroll-policy-boundary.md).

Implementation design must establish how public operations record and enforce
the selected requirements. Existing Core maker/checker and reconciliation checks
remain unchanged until that later work is authorized and reviewed. The local
fix branch is evidence to reassess against these layers, not an approved policy.

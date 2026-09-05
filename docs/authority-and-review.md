# Authority and review

**PAY-ARCH-003 / PAY-Q-013 — agreed. User approved the explained boundary.** This horizontal branch
follows the agreed [employee draft and batch boundary](ledger-ownership.md).
It establishes distinct responsibilities before selecting role names or a
permission implementation.

## Existing code and operating context

Source: lab revision `737465d5e27888518018e9b1f28f75fcfcac0139`,
[main.ts](../src/main.ts): `approveInput`, `preparePayrollReport`,
`reviewPreparationReport`, `approveDraft`, and `commitDraft`.

The code distinguishes input approval, local preparation-report review, draft
approval, and commit. Preparation checks input approval; report review explicitly
logs that it is local workflow state rather than canonical approval. Draft
approval checks lifecycle state, and commit requires an approved draft.

These are lifecycle gates, not implemented actor authorization. The browser demo
exposes operations without authenticated actor/scope checks. Its hardcoded
`hr-admin` proof-review label does not establish an enforced role model or an
audit trail for draft approval.

The user established that an HR/payroll manager consolidates information into
payroll through APIs, with a role supporting that work (PAY-INTAKE-001).
Neither that handoff nor employee ledger ownership determines who may approve
or commit. Here ownership means whose payroll the records describe; it does not
automatically grant access or operational permissions to that employee.

## Agreed boundary

| Responsibility | Meaning |
|---|---|
| Maintain and accept inputs | Submit, expire/replace, and accept payroll sources under the relevant authority. Accepting an instruction does not approve the resulting payroll draft. |
| Prepare payroll | Request calculation and create the fixed employee-period draft from eligible sources. Preparation-report review does not substitute for draft approval. |
| Approve payroll | Accept the exact fixed draft and its review basis. Record who approved which draft; rebuilt drafts require fresh approval. |
| Commit payroll | Execute posting of an approved draft under commit authority, with protected reconciliation and instruction-application controls. Permission to commit cannot bypass those checks. |

Treat these as separately grantable capabilities scoped to the appropriate
employer/tenant and employees. Merely holding input-maintenance or preparation
authority does not confer approval or commit authority. A bulk action must obey
the same authority and exact-draft approval rules for each employee it covers.

Capabilities are distinct even if an organization's policy grants more than one
to the same person or role. This decision does not require four job titles or
decide whether preparer and approver must be different people. An automated
commit executor would also need appropriate authority and a valid approved
draft; automation is not itself approval.

## Rationale and example

Input acceptance answers whether an instruction may enter payroll preparation.
Draft approval accepts the resulting combination of salary, instructions, and
calculation outputs. Commit records that accepted result only if its basis
still passes reconciliation. Keeping these responsibilities explicit preserves
accountability as roles and deployment arrangements vary.

Example: a manager submits an accepted bonus instruction and prepares September
payroll. A payroll approver accepts the resulting fixed employee draft. An
authorized operator or executor commits it if reconciliation succeeds. Whether
one person may hold all these capabilities is a separate organizational policy.

Counterexamples: an accepted bonus automatically counts as approval of the
entire payroll; preparation authority alone permits posting; or a commit
permission allows changed amounts to replace the approved draft.

## Alternatives and return points

A single broad manager permission would be simpler to assign, but would bundle
input maintenance, acceptance of calculated money, and posting. Mandatory
different people for each responsibility would impose a staffing and review
policy the user has not specified. The agreed capability boundary keeps
the responsibilities explicit while leaving role composition to policy.

**PAY-Q-013 — approved:** Input maintenance, preparation, draft approval, and
commit are distinct scoped capabilities. Policy decides which may be held by
the same person or role; no mandatory separate-person rule was adopted.

---

The user directed a return to [core-concept clarity](core-coverage.md) before
further authority or downstream discussion (PAY-PROCESS-008). Role names,
source-acceptance policy, separation of duties, delegation, revocation, approval
evidence, and automated execution remain parked. Correction and payment-release
authority are not granted by this decision.

# Payroll lifecycle and operation outcomes

**Current interpretation — [PAY-ARCH-006](payroll-policy-boundary.md):** approval,
hold and reconciliation workflow belongs to organizational Layer-2 policy.
The reconciliation/rebuild examples below describe that policy. Layer 1
protects fixed draft content, authorized operations, exact posting and immutable
history; it does not mandate current-source reconciliation for every commit.

**Status: Layer-1 capabilities and Layer-2 workflow under PAY-ARCH-006.**
This chapter explains preparation, draft controls and posting; required approval
and current-source freshness depend on the organization’s policy. It does not select API
names, state encodings, retry algorithms, or a new approval policy. Under PAY-CORE-007, complete draft creation includes sealing; the visible
capabilities include create, approve, hold/release, cancel and commit.
These are not one mandatory sequence for every organization.

## Operations and their effects

| Operation or event | Result under the agreed model | Monetary/application effect | Basis |
|---|---|---|---|
| Prepare calculated amounts | Higher-order calculation supplies the employee-period proposal | A preparation preview is not generated payroll or canonical draft approval | PAY-ARCH-001; preview behavior is described in the lab |
| Create a complete draft, including sealing | Fix the proposed monetary content for review | No final payroll or committed instruction application yet | PAY-CORE-001, PAY-CORE-006-C/007 |
| Approve | Accept that exact fixed draft using the appropriate scoped capability | Approval does not post money or consume instructions | PAY-ARCH-002/003, PAY-CORE-003/004 |
| Replace or expire an applicable source during review | Preserve source history; the draft stays fixed | No day-long source freeze; policy A requires reconciliation, while policy B may retain draft authority | PAY-SOURCE-001, PAY-CORE-006-C/010 |
| Reconcile before commit, if selected | Policy A checks the current applicable basis within protected commit | Relevant source changes block under policy A; policy B may use the fixed draft as authority. Application constraints remain enforced under both | PAY-ARCH-006 |
| Hold/release draft | Record the authorized control; policy decides when and by whom | An active hold prevents commit; release does not rewrite money or erase earlier evidence | PAY-ARCH-006 |
| Cancel an uncommitted draft | Make it unavailable for later commit; rebuild and review again if needed | No instruction consumption from cancellation; no approval transfer to its replacement | PAY-CORE-003, PAY-CORE-006-C, PAY-ARCH-002 |
| Commit | Record the exact selected draft after applicable approval, hold and application controls | Payroll becomes final; one-time consumption and monthly application rules apply | PAY-CORE-001/003/004/011 |
| Repeat a commit request | Preserve the one committed result and application guarantees | Repetition must not create duplicate money or duplicate instruction applications | Existing commit/application invariants; retry mechanism remains unspecified |
| Correct generated payroll within payroll scope | Use a subsequent payroll month's adjustment; preserve the original | No editing or cancellation of the committed result | PAY-CORE-011; after-exit corrections belong to accounting under PAY-CORE-013 |

All payroll for an employee/month remains associated under PAY-CORE-015.
That association does not make different drafts interchangeable: approval
belongs to the exact draft, and a batch coordinates individual draft outcomes.
No canonical identifier generator is required by this association.

The corresponding employer liability follows the committed Payroll Ledger.
Government remittance with proof later closes that obligation; it does not make
employee payroll newly final. See [the output lifecycle](payroll-outputs.md).

## An approved draft can become stale

Under policy A, suppose a complete draft is reviewed and approved. Before commit, an applicable
standing instruction is expired and replaced. The draft retains its reviewed
amounts, but protected reconciliation finds that its basis has changed.
The approved draft cannot commit. Cancel it, calculate and create a replacement,
then obtain fresh review and approval. Approval of the old draft does not
authorize the new amounts.

This follows policy A’s freshness requirement. Under policy B, the later source
change alone need not block the fixed draft. Both retain exact content and
instruction-application safeguards. Approval
does not reserve source facts throughout the review window. No automatic
cancellation schedule or particular cancellation role is selected here; exact
authority and state representation remain implementation work.

Cancellation also does not guarantee that an instruction remains eligible for
every later attempt. It means this cancelled draft did not consume it. Another
committed draft or the target period's applicability can affect eligibility.

## Retries and an uncertain commit outcome

The semantic requirement is to preserve the final result and application
guarantees. A lost response alone does not establish that posting failed.
Recovery must establish the outcome before treating the work as uncommitted or
starting a replacement that could duplicate it. This is a consequence of the
existing invariants, not a selected recovery protocol.

The lab's `commitDraft` returns immediately for a draft already marked committed.
That demonstrates only a same-draft check in memory. It does not establish
durable recovery, atomic posting, concurrent exclusion, or cross-draft
instruction protection. Those remain [implementation gaps](implementation-gaps.md).

## Approval withdrawal with an unchanged draft

[PAY-Q-020](gap-closure-work.md#pay-q-020--withdrawing-approval-without-changing-draft-amounts)
is closed as superseded by [PAY-ARCH-006](payroll-policy-boundary.md). Keeping
the same draft or rebuilding it after withdrawal is an organizational Layer-2
choice. The lifecycle above describes the earlier approval/reconciliation policy;
Layer 1 does not universally require that policy. It protects exact draft
content, authorized operations and immutable committed history under either
workflow. Required approval and active holds must be honored under the selected
policy.

## Code comparison

Evidence: [main.ts](../src/main.ts) at
`737465d5e27888518018e9b1f28f75fcfcac0139`.

| Lab behavior | Difference from the agreed outcome |
|---|---|
| Create empty open draft, append rows, seal, approve, commit | Complete draft creation must include sealing; a separate user-visible seal operation is no longer part of the agreed lifecycle |
| Approve only sealed drafts | A lifecycle gate exists; actual actor/scope authorization is absent |
| Commit without full applicable-basis reconciliation | Stale-draft rejection and protected application guarantees are not established |
| Abandon only open or sealed drafts | An approved but uncommitted stale draft cannot follow the agreed cancellation/rebuild path |
| Return early when the same draft is already committed | Does not demonstrate durable or cross-draft retry safety |

These are source findings, not a runtime implementation delivered by the handbook.

---

## PAY-CORE-007 — creation includes sealing

**Status: agreed under PAY-Q-009.** The user answered “agreed” to including
sealing in complete draft creation. Creation includes sealing. The earlier **create → approve → commit** sequence
is the approval-policy example; PAY-ARCH-006 makes approval and hold workflow
organizational choices. Cancellation remains an uncommitted-draft capability.

Creation completes and seals the monetary content. Approval accepts that exact
fixed proposal; protected commit records the final money and instruction
applications after reconciliation. Internal validation and integrity work still
belong in the implementation, without a separate user-visible seal action.

Rationale: sealing ends monetary editing, and complete fixed-draft creation
already fulfills that purpose. A separate step would repeat that transition
without an additional agreed business decision. Approval and commit retain
their distinct meanings.

The alternative was to retain a separate seal operation for an additional
validation responsibility. No such distinct responsibility was established;
the user approved incorporating sealing into creation. The
[original proposal and alternative](draft-source-freeze.md#pay-core-007--does-sealing-remain-a-separate-operation)
remain in the history. The historical source-freeze model stays superseded;
this decision retains immutable sources and protected reconciliation.

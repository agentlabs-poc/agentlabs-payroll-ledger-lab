# Payroll lifecycle and operation outcomes

**Status: consolidation of existing agreements.** This chapter explains the
business outcomes of preparation, review, and posting. It does not select API
names, state encodings, retry algorithms, or a new approval policy. The separate
seal operation remains an unanswered proposal under PAY-Q-009.

## Operations and their effects

| Operation or event | Result under the agreed model | Monetary/application effect | Basis |
|---|---|---|---|
| Prepare calculated amounts | Higher-order calculation supplies the employee-period proposal | A preparation preview is not generated payroll or canonical draft approval | PAY-ARCH-001; preview behavior is described in the lab |
| Create a complete draft | Fix the proposed monetary content for review | No final payroll or committed instruction application yet | PAY-CORE-001, PAY-CORE-006-C |
| Approve | Accept that exact fixed draft using the appropriate scoped capability | Approval does not post money or consume instructions | PAY-ARCH-002/003, PAY-CORE-003/004 |
| Replace or expire an applicable source during review | Preserve source history; the draft stays fixed | No day-long source freeze; commit must reconcile the full applicable basis | PAY-SOURCE-001, PAY-CORE-006-C/010 |
| Reconcile before commit | Check the applicable basis and instruction applications within protected commit | A relevant change blocks posting; an unchanged basis permits the approved draft to proceed | PAY-CORE-006-C |
| Cancel an uncommitted draft | Make it unavailable for later commit; rebuild and review again if needed | No instruction consumption from cancellation; no approval transfer to its replacement | PAY-CORE-003, PAY-CORE-006-C, PAY-ARCH-002 |
| Commit | Record the approved payroll result and its instruction applications | Payroll becomes final; one-time consumption and monthly application rules apply | PAY-CORE-001/003/004/011 |
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

Suppose a complete draft is reviewed and approved. Before commit, an applicable
standing instruction is expired and replaced. The draft retains its reviewed
amounts, but protected reconciliation finds that its basis has changed.
The approved draft cannot commit. Cancel it, calculate and create a replacement,
then obtain fresh review and approval. Approval of the old draft does not
authorize the new amounts.

This follows the existing fixed-draft and reconciliation agreement. Approval
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

## Code comparison

Evidence: [main.ts](../src/main.ts) at
`737465d5e27888518018e9b1f28f75fcfcac0139`.

| Lab behavior | Difference from the agreed outcome |
|---|---|
| Create empty open draft, append rows, seal, approve, commit | Complete draft content must already be fixed from creation; whether sealing remains separately exposed is pending |
| Approve only sealed drafts | A lifecycle gate exists; actual actor/scope authorization is absent |
| Commit without full applicable-basis reconciliation | Stale-draft rejection and protected application guarantees are not established |
| Abandon only open or sealed drafts | An approved but uncommitted stale draft cannot follow the agreed cancellation/rebuild path |
| Return early when the same draft is already committed | Does not demonstrate durable or cross-draft retry safety |

These are source findings, not a runtime implementation delivered by the handbook.

---

## PAY-Q-009 — separate sealing remains a proposal

**Status: reopened after the horizontal pass; awaiting the user's answer.**
Draft monetary immutability from complete creation is already agreed.
The pending choice concerns whether the lab should expose a separate seal
operation or incorporate that work into complete draft creation.

Proposal: visible operations are create complete draft, approve, and commit,
with cancellation before commit. Creation includes content completion and
sealing. Approval and commit retain their distinct meanings.

Rationale: if sealing only ends monetary editing, that purpose is already
fulfilled by complete fixed-draft creation. A separate step needs an additional
meaning, such as a distinct validation responsibility, to justify exposing it.
No such additional responsibility has been agreed.

The [original proposal and alternative](draft-source-freeze.md#pay-core-007--does-sealing-remain-a-separate-operation)
remain in the history. The source-freeze model in that historical chapter is
superseded; returning to this question does not revive it.

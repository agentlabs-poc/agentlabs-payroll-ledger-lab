# Immutable sources and reconciliation before commit

**PAY-CORE-006-C / PAY-Q-010 — agreed; replaces the long-lived source freeze.**
The user answered "approved" and directed discussion to move horizontally
through high-impact areas first (PAY-PROCESS-006).
The user clarified that source records are immutable: an old record
expires and a new one is created. They suggested reconciling after draft review
and committing when nothing relevant has changed. The assistant recommends this
direction with the consistency requirements below, which the user approved.

PAY-SOURCE-001 records the user's immutable-source model. This is a clarification
of intended concepts, not evidence that every deployed source API enforces them.
PAY-CORE-006-B's long-lived source freeze is superseded;
the [freeze chapter](draft-source-freeze.md) preserves its earlier approval and
rationale. The draft's monetary immutability is retained in the current model.

## Later scope clarification — PAY-CORE-010

Source tracing is not a core requirement. The earlier wording required captured
source identities and provenance too broadly. The current requirement is to
validate that the relevant basis remains applicable at commit; it does not
mandate per-entry source links or a reconstructable business-origin graph.
The validation representation remains open. PAY-CORE-008 also places detection
of business overlap/duplicate intent in the producing layer. This chapter's
application guards concern repeated use of an instruction, not whether two
separate instructions represent the same business request.

## Immutable records, changing applicability

An old source record's monetary content and identity remain available as history.
A replacement is a new record; it does not overwrite what the earlier record
said. Expiry or supersession changes which records apply to payroll.

Thus, the historical source set can remain immutable while the currently
applicable set changes. Reconciliation must detect when the basis used to
prepare the fixed draft is no longer applicable, without imposing a mandatory
source-tracing representation.
The physical representation of expiry—such as a separate lifecycle record or
version metadata—is not selected here. The requirement is to preserve historical
content and respect applicability.

## Agreed flow

```text
Resolve applicable facts and establish the basis for validation
                         ↓
Create complete draft with fixed monetary entries, including sealing
                         ↓
Review and approve that draft
                         ↓
Reconcile target-period sources and instruction applications
             ├─ unchanged and valid → commit + record applications
             └─ changed or invalid → block commit → cancel/rebuild/review
```

The source ledgers may accept new or replacement records during review. There
is no day-long source freeze in this model. Reconciliation is a validation
of the draft's basis; it does not silently update its values or transfer its
approval to another proposal.

## What must be unchanged

Validate the applicable basis for the same tenant, employee/owner,
and payroll period. The check must establish:

- The facts used for preparation remain the applicable facts for that period.
  Exact source IDs on draft or posted entries are not prescribed.
- Their eligibility remains valid, including applicable expiry, supersession,
  approval, or withdrawal rules as those are defined.
- No newly applicable instruction or other source has changed the complete
  relevant set. Checking only the records already referenced cannot detect an
  additional instruction.
- One-time inputs remain unconsumed, and monthly applications have not already
  been committed for this employee and period by another payroll.
- Any other captured calculation dependencies needed to explain the reviewed
  result remain valid under their agreed version/applicability rules. Their
  precise inventory is still open.

Validate applicability and completeness, not merely gross or net totals.
An unchanged total alone does not establish that the applicable basis is unchanged. A change wholly outside the target owner/period should not invalidate
this draft if it cannot affect its input set or relevant dependencies.

## PAY-EX-006 — replacement during review

The draft uses salary source S-1 and instruction I-1 for a bonus of INR 5,000.
During review, I-1 is expired/superseded for the target period and I-2 is created
for INR 6,000. I-1 still exists as historical evidence. The draft remains a
INR 5,000 proposal. I-1/I-2 label the example facts; retaining these labels on
the monetary entry is not a core requirement.

At commit, reconciliation resolves I-2 as applicable and detects the mismatch.
It blocks the old draft. The manager cancels it and prepares and reviews a new
draft using I-2. By contrast, if I-2 affects only a later period and I-1 remains
the applicable source for this draft's period, that future change alone does
not establish a mismatch (PAY-CORE-005).

Counterexamples: accepting the old draft merely because I-1 still exists;
accepting it because net pay is unchanged despite a changed source set; or
ignoring a new same-period bonus instruction because it was absent from the
facts considered in preparation.

## Reconciliation and commit must form one protected operation

A pre-review or pre-commit report can show differences, but the authoritative
check must be consistent with posting and recording instruction applications.
No relevant writer may slip a change or competing application between that
check and commit without causing the operation to detect a conflict or fail.

Use a short, appropriately isolated transaction or equivalent coordinated
concurrency protocol for this final operation. Merely putting several reads
and writes inside a default transaction does not establish the guarantee.
PostgreSQL documents that Read Committed queries can observe different
snapshots within one transaction, and that Serializable transactions detect
serialization conflicts and may require a retry.
[PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html).
The required business behavior is a consistent validation and commit; the
database mechanism remains an implementation decision. All relevant writers
must participate in the protocol, including creation of newly eligible records.

A concurrency retry must repeat reconciliation and must not silently substitute
new values for the reviewed draft. A changed basis requires a new reviewed
proposal. Successful same-draft retries must preserve single application.

## Rationale and tradeoff

Immutable source history preserves earlier facts. Reconciliation
can determine whether the preparation basis still applies, so a long-lived edit freeze is
unnecessary if the final check and commit are properly coordinated. Source
maintenance can continue during a day of review without managing business locks,
unlock permissions, or orphaned long-lived freezes.

The cost moves to complete change detection and occasional rebuilds. Frequent
relevant changes can repeatedly invalidate a draft. A long-lived freeze avoids
some rebuilds by blocking writers; this alternative preserves writer progress
and blocks stale commits instead. Draft and posted immutability, expiry by
payroll period, and single-application rules remain in force.

## Source evidence and open decisions

The lab at `737465d5e27888518018e9b1f28f75fcfcac0139` retains source references,
but `commitDraft` does not reconcile the eligible source set. Its draft hash
covers head, amount, and source text; it is not a complete source-set comparison.
The demo also mutates approval/consumption metadata and does not implement a
general source expiry/replacement lifecycle. The user's clarified source model
must therefore remain distinct from verified implementation behavior.

Implementation work: choose validation evidence and expiry/supersession
representation, identify the relevant calculation dependencies, implement the
protected concurrency mechanism, and map cancellation authority. These choices
must preserve the full employee-period basis and changed-source outcomes already
specified above. They are not unanswered core questions about whether to
reconcile, freeze sources throughout review, or trace business origins. PAY-Q-009 is now
approved as PAY-CORE-007: [complete draft creation includes sealing](payroll-lifecycle.md#pay-core-007--creation-includes-sealing).

**PAY-Q-010 — approved:** Immutable source history plus a fixed draft and
protected reconciliation at commit replaces the long-lived source freeze.
A changed basis requires cancellation, rebuilding, and fresh review.

# Draft-to-commit source freeze — superseded model

**Superseded by approved [PAY-CORE-006-C / PAY-Q-010](source-reconciliation.md).**
Immutable source history and protected reconciliation at commit replace the
long-lived source freeze. The text below preserves the earlier approval,
rationale, and tradeoffs as history. Draft monetary immutability remains agreed;
source freezing throughout review is no longer a current requirement.

**PAY-CORE-006-B / PAY-Q-008 — historical approval, subsequently superseded.** The user answered "approved", including
the explicit question that draft monetary entries are frozen from creation and
corrections require cancellation and rebuilding.

The user suggested stopping mutation during draft and commit, potentially for
one day, then unlocking the respective ledgers when commit finishes. This is
the accepted alternative to the earlier [draft/source-change proposal](core-concepts.md#pay-core-006--source-changes-and-an-existing-draft),
which remains preserved as superseded reasoning.

## Intended boundary and rationale

Freeze the payroll source input set while a draft is reviewed and committed.
This prevents source changes from making the draft stale during that interval.
The motivation is understandable: the reviewed amounts and their underlying
directions remain stable until the result is committed.

The freeze covers the relevant salary earnings, monthly instructions, and
one-time inputs, tied to the active payroll draft. The draft's monetary entries
are also frozen from creation. Workflow transitions remain possible; they do
not authorize changing the proposed monetary content. To correct an amount,
cancel the draft, update the source, and create a new draft.

Creation must produce the complete monetary proposal before exposing a usable
draft. The internal construction of those rows is part of creation; the rule
does not mean publishing an empty draft that can never be populated. Exact
construction and transaction mechanics remain implementation work.

## Agreed lifecycle shape

1. **Scope the freeze.** Bind it to the payroll owner/employee set and target
   period. Block changes that can affect that input set, including relevant
   additions, changes of applicability, and removals. Unrelated employees or
   periods need not be frozen if isolation can be established.
2. **Capture consistently.** Establish the freeze before capturing the inputs
   used by the draft. If a preview already exists, verify it against the frozen
   source set or rebuild it. Freezing after a stale preview has been copied
   would preserve the wrong starting point.
3. **Maintain the freeze through review.** Every supported source-writing path
   must respect it. Conflicting drafts or changes affecting shared inputs must
   not bypass another active draft's freeze. Shared component definitions or
   calculation dependencies also need stable treatment if they can affect the
   result; the exact boundary is still to be decided.
4. **Commit, record application, then release.** Posting the approved result,
   recording one-time consumption and monthly applications, and releasing the
   draft's freeze need one consistent transition. Another writer must not see
   unlocked sources before the successful commit and application records exist.
5. **Provide an exit without commit.** An explicit authorized cancel/abandon
   action releases the freeze and makes that draft uncommittable. The manager
   can then correct sources and prepare a new draft. Do not leave sources
   locked indefinitely because the manager decides not to proceed.

```text
Editable payroll sources
          ↓ freeze and capture consistently
Complete draft created — draft money and relevant sources frozen
          ↓ review and approval; monetary content unchanged
Approved draft
          ├─ successful commit + application records → release source freeze
          └─ authorized cancellation → invalidate draft → release source freeze
```

Cancellation is also available before approval. Cancellation must make the
draft uncommittable before its source protection is released. Its authority and
exact state encoding remain open.

Release means releasing this draft's ownership of the freeze. If another valid
freeze covers a shared source, releasing one must not clear the other's
protection. The concurrency policy and exact lock granularity remain open.

## Example and counterexamples

A draft includes a one-time INR 5,000 bonus. During review, the manager discovers
it should be INR 6,000. Under the agreed rule, both source changes affecting the
draft and direct edits to its monetary content are blocked while it is active.
The manager cancels that draft, releases its
freeze, corrects the source, and prepares a replacement. Consumption has not
occurred because the earlier draft never committed (PAY-CORE-003).

If the draft commits normally, the posted result remains fixed under
PAY-CORE-001. Source editing can resume, but unlocking does not erase the
one-time consumption record or the month's standing-instruction application.
It also does not make posted payroll entries editable.

Counterexamples: blocking edits to existing source rows but permitting a new
instruction affecting the same frozen payroll; unlocking before application
records are written; or automatically unlocking after one day while leaving
the old approved draft eligible to commit. Each would undermine the intended
stability or single-application rules.

## A day-long freeze and recovery

A day can be the expected business review window. That does not make one day a
mandatory duration or an automatic unlock time. An explicit recovery rule is
needed for crashes, lost sessions, failed commits, and abandoned work. A timeout
must not leave an unfrozen, stale draft able to commit; recovery must establish
the commit outcome or invalidate the draft before releasing protection.

The tradeoff is that relevant source corrections wait until commit or
cancellation. Compared with allowing source changes and detecting stale drafts,
this shape simplifies source stability but can require cancellation and
re-preparation for an urgent correction.

Implement the review-window freeze as durable application state respected by
mutation paths, using short transactions for lifecycle changes. PostgreSQL
normally retains row locks until transaction end and advises against holding
transactions open while waiting for user input. A day-long review should not
be implemented by keeping a database transaction open throughout it.
[PostgreSQL locking documentation](https://www.postgresql.org/docs/current/explicit-locking.html)
supports this implementation distinction; the business freeze recommendation
is our design inference, not a rule prescribed by PostgreSQL.

## Source evidence and remaining decisions

The lab at `737465d5e27888518018e9b1f28f75fcfcac0139` creates an empty draft and
permits subsequent appends while open. It implements no source freeze.
`abandonDraft` accepts only open or sealed drafts. Complete creation, monetary
immutability from creation, and cancellation covering the agreed uncommitted
lifecycle are implementation gaps, tracked in
[PAY-GAP-004](implementation-gaps.md#pay-gap-004--draft-and-source-freeze-lifecycle).

The inspected HRMS Core revision `13621844165b31346facc53c4b45bbd8d9437816`
includes `payroll_lock_calculation_governed_sources` in
[migration 87](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/13621844165b31346facc53c4b45bbd8d9437816/migrations/000087_payroll_governed_source_lock.up.sql).
It acquires source locks within the caller's serializable transaction. That
function alone is not evidence of a durable freeze spanning a day of review.

Open decisions: exact freeze granularity and shared calculation dependencies,
cancellation authority and state encoding, recovery authority and timeout
behavior, and handling of overlapping drafts. The earlier proposal remains
preserved as superseded history. No source-code changes have been made.

## PAY-CORE-007 — does sealing remain a separate operation?

**Historical proposal, still unapproved.** PAY-Q-009 was parked during the
horizontal pass and has now been reopened in the
[current lifecycle chapter](payroll-lifecycle.md#pay-q-009--separate-sealing-remains-a-proposal).
The original explanation below does not restore the superseded source freeze.

In the existing code, an open draft accepts rows. `sealDraft` requires a
non-empty draft, changes its status, and refreshes its hash before approval.
Under PAY-CORE-006-B, complete creation already fixes the monetary content.

Proposal: perform content completion, integrity identification, and freezing as
part of draft creation, without a separate user-visible seal operation. Keep
approval and commit as distinct operations: approval accepts the fixed proposal;
commit posts its monetary result and records instruction applications.

Rationale: a lifecycle stage needs a distinct meaning. If sealing only ends
editing, that transition has moved to creation. Requiring a second manual step
with the same purpose adds no new business decision. Conversely, if sealing is
intended to certify some additional validation, preserve that meaning explicitly
before deciding whether it needs its own state or operation.

Proposed ordinary lifecycle: complete frozen draft → approved → committed,
with cancellation possible before commit. This does not remove validation or
change any agreed source-freeze, consumption, or posted-immutability rule.

**PAY-Q-009:** Should complete draft creation include sealing, leaving approval
and commit as the subsequent distinct operations?

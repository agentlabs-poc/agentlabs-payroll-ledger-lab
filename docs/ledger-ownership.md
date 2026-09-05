# Ledger ownership and the unit of work

**PAY-ARCH-002 / PAY-Q-012 — agreed. User approved the explained boundary.** This is the next
high-impact boundary after the agreed [calculation boundary](calculation-boundary.md).
Detailed batch APIs, identifiers, and retry algorithms remain parked.

## Existing code

Source: lab revision `737465d5e27888518018e9b1f28f75fcfcac0139`,
[main.ts](../src/main.ts), especially `LedgerReference`, `Draft`, `createDraft`,
`approveDraft`, `commitDraft`, and `createStatutoryLiabilities`.

`createDraft(employee, period)` creates a payroll reference and draft for one
employee and period. Entries inherit the draft owner. Approval and commit take
one draft ID; posted entries retain its reference and owner. The lab therefore
already expresses an individual employee draft as its lifecycle unit. Its
in-memory commit is not proof of durable atomic enforcement.

The statutory liability store separately uses a hardcoded legal-entity owner,
retaining employee and payroll-entry links. This shows that ledger ownership
depends on what the ledger records. It does not establish a complete employer,
tenant, or employment identity model. The inspected flow does not implement a
multi-employee batch lifecycle.

## Agreed boundary

- An employee's payroll records belong to that employee within the appropriate
  employer/tenant context. The manager acts on the ledger through authority;
  preparing payroll does not make the manager its owner.
- A fixed draft for one employee and payroll period is the unit approved and
  committed. Its payroll entries and instruction applications succeed together
  under the already agreed protected commit rule.
- A batch coordinates multiple employee drafts. Bulk review or approval must
  identify the exact drafts covered; a batch label alone cannot approve future
  replacement drafts.
- Employee commits can succeed independently. A batch must expose committed,
  blocked, and remaining drafts accurately; it cannot report full completion
  while selected employees remain uncommitted.

This does not impose one payroll reference per employee forever or settle
supplementary-run mechanics. PAY-CORE-011 settles that corrections to a generated
result belong to a subsequent payroll month while within payroll scope;
PAY-CORE-013 places after-exit corrections in accounting. Existing instruction-use
controls still apply across drafts. PAY-ARCH-004 and PAY-CORE-012 establish the employer
register inside payroll and closure on remittance with proof.

## Rationale and example

The employee draft already aligns its sources, proposed amounts, instruction
applications, and resulting payroll reference. Keeping that unit makes an
individual exception reviewable and recoverable without reopening every other
employee's accepted result.

For example, a batch contains 100 reviewed employee drafts. A new relevant
instruction invalidates one employee's draft. Under this agreement, the other
99 may commit if their own reconciliation succeeds. The changed draft is
blocked and rebuilt for fresh review. The batch remains partially completed
until the outstanding case is resolved under the eventual batch policy.

Counterexample: treating a batch as fully committed after 99 successes, or
allowing the replaced hundredth draft to inherit approval based only on its
membership in the same batch.

## Alternative and tradeoff

A batch-wide all-or-nothing commit could instead require every selected
employee draft to pass before any posts. That offers a single completion
boundary but couples all selected employees to any one changed or invalid
draft. It would also add a broader reconciliation and commit requirement beyond
the current individual-draft code.

The agreed individual commit boundary allows partial completion, so
accurate batch status and explicit handling of outstanding employees become
necessary. A later payment-release policy can have its own review boundary;
this decision does not authorize paying a partially completed batch.

## Question and return points

**PAY-Q-012 — approved:** One employee's draft for a payroll period is the unit
of approval and protected commit; batches coordinate those drafts and retain
individual outcomes.

---

The following branch, [authority and review](authority-and-review.md), is now
agreed under PAY-Q-013. Core clarification is recorded in the
[checkpoint](core-coverage.md); the [roadmap](handbook-roadmap.md) identifies
the current discussion.
Return later to
exact identity representation, batch selection and approval evidence,
retry/cancellation mechanics, and supplementary-run behavior.

# Layer-1 payroll contracts and Layer-2 policy

**PAY-ARCH-006 — user-confirmed boundary, 2026-09-06.** The user explained
that approval withdrawal and reconciliation choices belong above Layer 1 and
vary by organization, then directed that the rationale be recorded and
PAY-Q-020 closed as superseded.

## Responsibility and rationale

Layer 1 supplies payroll records and protected operations: identifiable fixed
drafts, authorized status changes with history, exact monetary posting,
idempotency, atomic ledger/application recording and immutable committed
history. An upper-layer producer or workflow does not gain a bypass around
those integrity guarantees.

Layer 2 defines the organization's HRMS payroll policy. It decides whether
approval is required, who exercises the granted capabilities, when a draft is
held or released, which drafts a batch selects, and whether current inputs must
be reconciled before commit. These are different valid operating policies,
not questions that must each have one universal Layer-1 answer.

An organization may reconcile current inputs and hold or rebuild a draft when
they differ. Another may treat the fixed draft as final monetary authority and
commit that exact content despite a later source change. Neither policy permits
silent changes to draft amounts, duplicate posting, unauthorized action or
rewriting committed payroll. Required approval or hold controls must be honored
under the selected policy; they are not a caller-controlled bypass.

Rationale: payroll record integrity is stable across organizations, while the
meaning of approval and the review workflow varies. Requiring the core to
choose one withdrawal or freshness policy would embed one organization's
workflow in the generic platform. The policy can be published separately as an
HRMS payroll policy, with Layer 1 supplying the records and operations it uses.
A Layer-2 policy does not require Lua, a managed pipeline or a separate service.

## Approval, hold and batch selection

Approval and hold are useful draft controls for the upper-layer workflow. For
example, 100 drafts exist and one is held: the workflow excludes it and proceeds
with the other 99. The held draft remains uncommitted and visible as outstanding;
exclusion does not make that employee's payroll complete.

Keeping approval evidence separate from a hold is a suggested representation:
an already approved draft can be held without erasing the earlier approval.
This records the rationale, not a selected enum, endpoint or database schema.
The organization's policy controls who can hold, release or reapprove; Layer 1
must preserve the applicable authority, current state and transition history.

## Supersession and history

PAY-Q-020 asked whether withdrawal of approval must retain the same draft or
require cancellation/rebuilding. **Closed as superseded:** neither alternative
is mandated universally by Layer 1. Former PAY-CORE-017 remains an unadopted
policy option, not an approved core rule.

This also supersedes the universal placement of the freshness/rebuild rule in
PAY-CORE-006-C. Its immutable draft and history rationale remains valid, and its
reconcile-before-commit flow remains a useful Layer-2 policy example. It is no
longer a requirement that every organization recheck current source applicability
before committing an unchanged fixed draft. PAY-ARCH-003's distinct capabilities
remain valid; mandatory organizational approval/withdrawal sequencing is policy.

Earlier chapters and acceptance cases describing reconciliation, rebuild and
fresh approval are to be read under that policy. They must not be used to
reject a draft-authoritative policy merely because current sources changed.
No local Core code or existing runtime safeguard is changed by this decision.

## Handbook follow-through

PAY-Q-020 is no longer an open question or closure blocker. The user also
approved expressing the handbook as [Layer-1 contracts](layer-1-contracts.md)
and a separate [HRMS payroll policy](hrms-payroll-policy.md). Both are now
documented, with current contracts, navigation and examples aligned. The
[review record](handbook-review.md#current-consolidated-review) closes this
conceptual documentation pass with its explicit limits. Implementation remains
paused; no current runtime or local candidate is certified by this closure.

# Gap discussion and resolution audit — historical checkpoint

Audit date: 2026-09-06, after conceptual edition 1 at `a1eb93a`.
**Historical snapshot:** the gap table and counts below describe that checkpoint
and the browser lab. For current handbook readiness use the
[consolidated review](handbook-review.md#current-consolidated-review). Partial
remittance and annual package scope were subsequently agreed; PAY-Q-020 is open.
Core main and the unmerged local fixes have [separate evidence](baseline-reconciliation.md).
The user asked whether every gap had been discussed and resolved, and specifically
revisited the employee-month association under PAY-CORE-015.

**Finding: every numbered gap is documented, but not every gap is resolved.**
Documentation, agreement on core behavior, specification of detailed policy,
and verified implementation are separate statuses. Deferral does not resolve a
choice, and an assistant's source finding is not automatically a user decision.

**Later work:** the user subsequently directed work on these gaps. The
[active worksheet](gap-closure-work.md) records acceptance cases and opens
PAY-Q-017 on partial remittances, subsequently approved as PAY-CORE-016.
That rule is now settled; the implementation gap remains open. The counts and no-pending-proposal statement
below describe the audit checkpoint, not this later discussion state.

## Numbered gaps

This audits all eight entries in the [gap register](implementation-gaps.md)
against the [decision log](decision-log.md). The six agreed behavior rows below
retain implementation or policy details; they are not complete implementation specs.

| Gap | Discussion and conceptual resolution | What remains | Implementation closure |
|---|---|---|---|
| PAY-GAP-001: expiry | PAY-CORE-002/005 settle finite standing-instruction lifetime and target-period applicability | Encoding and boundary representation; no automatic extension or catch-up policy selected | Open: creation/selection do not enforce expiry |
| PAY-GAP-002: one-time use | PAY-CORE-003 settles consumption at commit and no ordinary reuse; cancellation does not consume | Application identity representation; exceptional partial application/restoration not adopted | Open: another draft can reuse the instruction |
| PAY-GAP-003: monthly use | PAY-CORE-004 settles one ordinary application per employee/month and later eligible months | Instruction-version/application mapping; exceptional splitting or restoration not adopted | Open: no cross-draft monthly application guard |
| PAY-GAP-004: review-window source freeze | Discussed, then superseded by PAY-CORE-006-C | No work to implement the rejected freeze; current obligations belong to GAP-005 | Superseded, not implemented or verified closed |
| PAY-GAP-005: fixed draft and reconciliation | PAY-SOURCE-001, PAY-CORE-006-C/007/010 settle immutable source history, creation including sealing, protected reconciliation, and rebuild/fresh review | Validation representation/dependencies, concurrency/recovery mechanism, cancellation authority | Open: mutable creation, absent protected reconciliation, approved draft cannot be abandoned |
| PAY-GAP-006: corrections | PAY-CORE-011/013 and PAY-ARCH-001 settle subsequent-month governed payroll within scope and after-exit accounting | Adjustment representation and enforcement | Open: demo directly posts and does not enforce subsequent-month timing |
| PAY-GAP-007: employer liability closure | PAY-CORE-012 and PAY-ARCH-004 settle register ownership and corresponding remittance/proof closure | Detailed allocation/proof interfaces and partial-payment policy | Open: matching safeguards and actual remittance evidence are incomplete |
| PAY-GAP-008: annual reporting | Information dependencies and code limitations are described; a complete annual issuance design has not been agreed | Applicable reporting scope, complete aggregation, statutory attribution and issuance integration | Open limitation: global TDS data and one payslip cannot establish the complete annual result |

Count: six gaps have an agreed core behavior; one historical requirement is
superseded; one annual workflow is only partly specified. Seven numbered gaps
or limitations remain active. None has been closed through implementation work
in this documentation phase. These counts are not an exhaustive defect count.

## Employee-month association is already resolved

The user's clarification, PAY-CORE-015, means that all payroll for the same
employee and month is tied together, with no canonical method to generate its ID.

This establishes the association and deliberately leaves ID generation to the
implementation. There is no outstanding requirement to choose a UUID, prefix,
concatenation, or other canonical generator for the handbook. The user's return
to this point confirms the existing concept; it does not open a new question.

An implementation must preserve the employee-month association while retaining
the identity of the exact draft being approved. The demo's shared payroll
reference within a draft/posted result shows part of this shape, but its counter
does not establish a general association across separate results for the same
employee/month. That mapping is implementation work, not an unresolved business
meaning. No new ledger or identifier scheme is prescribed.

See [the agreed association and rationale](ledger-ownership.md#pay-core-015--all-payroll-for-an-employee-and-month-is-tied-together).
Association alone does not decide supplemental-run eligibility, which is a
separate deferred policy; the identifier question must not be used to reopen it.

## Coverage outside the eight numbered gaps

The register's coverage table and linked chapters also retain these findings:

| Area | Resolved concept | Remaining work |
|---|---|---|
| Authority | Input maintenance, preparation, approval, and commit are distinct scoped capabilities | Actual role assignments and enforcement; cancellation/revocation details |
| Employee-month grouping and batches | Association has no canonical generator; exact employee-period draft is the commit unit; batch retains individual outcomes | Storage/API mapping, batch coordination and recovery |
| Employer contribution | Earning plus matching deduction precede employer register; gross includes contribution and net is balanced by the deduction | Complete paired example/enforcement in the runtime |
| Calculation and manager intake | Manager consolidates through APIs; higher-order logic supplies amounts; core governs monetary lifecycle | Concrete interfaces and calculation policies |

These are documented outside the numbered entries, not silently resolved by
their absence from the eight-row list. Employer-specific operating practices
and complete annual procedures remain in the [deferred-work table](handbook-review.md#what-remains-and-where-it-belongs).

## Correction to the checkpoint wording

The earlier “zero known unanswered core decisions” meant zero named proposals
awaiting a user answer. That wording was too broad as a statement about all
remaining work. It must not imply that deferred policies were discussed to a
decision, that the implementation specification is complete, or that code gaps
have been fixed.

The editorial checkpoints remain completed for the selected conceptual examples.
The status at that historical checkpoint was: **the reviewed core rules were
agreed; no named proposal awaited an answer; explicit policy/specification
deferrals and code gaps remained.** PAY-Q-020 subsequently opened; this statement
must not be used as the current completion status.
There is no basis for a claim that every possible payroll gap has been found.

Evidence for this audit is the recorded decisions and the inspected lab source
at `737465d5e27888518018e9b1f28f75fcfcac0139`, unchanged during the handbook work.
The source review checks expiry selection, draft lifecycle/commit, correction,
liability matching, and annual aggregation against their existing findings.
No new statutory claim, runtime test result, or delivered fix is asserted.

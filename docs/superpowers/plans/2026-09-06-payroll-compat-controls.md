# Payroll compatibility C — draft controls and policy-aware commit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Coding agents must use `gpt-5.6-sol`, reasoning effort `medium`, as requested by the user.

**Goal:** Support exact-draft approval, protected hold/release/cancellation and both freshness policies without weakening ledger integrity.

**Architecture:** Bind authorized commit requirements to the exact candidate and retain append-only control history. Resolve controls under the same lock/transaction as posting. Keep current defaults for legacy callers and retain per-employee durable receipts.

**Tech Stack:** Existing HRMS Core Go services, PostgreSQL protected gateways and migrations, Cobra CLI, and repository acceptance tooling. No new framework or calculation engine.

**Spec:** [Layer-1 contracts](../../layer-1-contracts.md), [HRMS payroll policy](../../hrms-payroll-policy.md), [operation contracts](../../payroll-operation-contracts.md), [reconciliation](../../implementation-reconciliation.md).

## Global constraints

- “A usable complete draft has fixed content.”
- “An active hold excludes the draft from commit; history remains available.”
- “The employee-period draft is the unit of monetary commit.”
- “Posted history is immutable.”
- “Money and currency are represented exactly.”
- “No canonical number generator is prescribed.” Employee/month association does not replace exact draft identity.
- Preserve tenant/capability checks, atomic applications and durable replay under both freshness policies.
- Default existing callers to their current approval/freshness safeguards; policy changes require authorized, recorded controls.
- No direct attendance-to-payroll transition, business-origin deduplication, tax formulas, official certificate issuance, or general accounting.
- All paths below are relative to HRMS Core unless explicitly identified as handbook or E2E paths. New names and interfaces are proposed engineering choices, not previously approved handbook field names.
- Existing Core `AGENTS.md`: `VERSION` is authoritative; public API, migrations, CLI, authorization and configuration are compatibility surfaces.

---

## Files and proposed interfaces

Modify `internal/modules/payroll/employee_finalization.go`,
`employee_finalization_repository.go`, `http_idempotency.go`, `routes.go`,
`register.go`, `ledger_service.go`, and the protected whole-run posting gateway
identified by CP-0. Reshape candidate migration
`000095_payroll_employee_finalization.{up,down}.sql` and add the control migration
at the next sequence assigned by CP-0. Update `database_authority.go`, gateway
inventory tests, authorization manifests and `cmd/server/payroll_route_authority_test.go`.
Create `draft_controls.go`, `draft_controls_repository.go`,
`draft_controls_db_test.go`, and `draft_controls_http_test.go` in the payroll module.
Extend the existing employee finalization database/HTTP/cadence tests.

Proposed public control operations target calculation ID plus exact candidate
and content hashes. They also carry an idempotency key and expected control
version. Control requests can bind requirements, hold, release or cancel; the
commit request cannot supply a bypass boolean. Follow existing canonical ID,
principal and request-hash conventions.

```text
requirements:
  freshness = reconcile_current | fixed_draft
  approval = distinct_actor_and_executor | not_required
  policy_reference = supplied auditable reference
control command:
  exact candidate identity + expected_control_version + idempotency_key
  action = bind_requirements | hold | release | cancel
  reason/evidence + authenticated actor/executor
release command:
  approval_disposition = retain_exact_approval | require_new_approval
```

Use a tenant/candidate control record for locking/versioning and append-only
events for evidence. Bind requirements before first approval/posting, defaulting
existing candidates to their current strict requirements. Requirements are not
silently replaced after review. An intentional different binding requires an
explicit replacement preparation with preserved history. Keep monetary candidate
identity distinct from control version; commit verifies both applicable states.

Only an explicitly granted policy-binding capability can choose requirements;
normal commit authority does not imply that capability. Go and protected SQL
must obtain the stored binding themselves. Unknown modes fail closed. This is
a small declared-control contract, not a formula language or workflow engine.

## Task C1: add protected draft controls

- [ ] Add integration tests for unauthorized bind/hold/release/cancel, wrong tenant/hash, conflicting expected version, idempotent replay and cancellation after posting. Tests must exercise the application role and protected gateway, not only in-memory state.
- [ ] Implement exact-candidate control storage, read projection and append-only events. Require tenant relationships, authorized actor/executor evidence, request identity, and monotonic version. Prevent application-role update/delete/truncate of historical events.
- [ ] Apply the state transition contract:

```text
hold(uncommitted, current version) -> held; monetary bytes and approval history unchanged
release(held, current version) -> unheld; retain or require new approval as authorized
cancel(uncommitted, current version) -> terminal non-postable; consume nothing
hold/release/cancel(posted) -> conflict; preserve posted receipt and money
replay(same key, same request) -> original result; different request -> conflict
```

- [ ] Keep hold independent of approval evidence. Implement `require_new_approval` with an approval-validity boundary/version, preserving earlier approval records. This supplies a capability without mandating the superseded Q-020 workflow.
- [ ] Expose the controls with explicit permission mappings and inspectable state/history. Invalid release cannot erase a hold; new control requests on a cancelled draft cannot revive it.
- [ ] Run the control tests red then green, review both gateway authorization and monetary immutability, and commit the control unit.

## Task C2: use policy at the protected commit boundary

- [ ] Parameterize the changed-source finalization tests by freshness mode. For the same 5,000-to-6,000 source replacement, strict mode rejects the old draft while fixed-draft mode posts the original 5,000 if all other controls pass.
- [ ] Inventory every precondition in Go, employee SQL and whole-run SQL. Separate current applicability comparison from fixed authority validation and application-consumption guards. Do not merely remove `fresh()` or `payroll_employee_sources_match` and assume all current-source coupling is gone.
- [ ] Refactor finalization to this ordered transaction contract:

```text
validate tenant/capability and exact identity
lock run/candidate/control in a consistent order
if an exact committed receipt exists: return it
load trusted requirements and current control version
reject cancelled or held candidate
require matching approval when the binding requires it
if freshness == reconcile_current: resolve and compare applicable sources here
validate fixed entry authority, pair integrity and instruction application constraints
post exact money + applications + liabilities + receipt atomically
```

- [ ] Default legacy callers without a new explicit binding to existing maker/checker and freshness requirements. Test a granted `not_required` binding separately; ordinary callers cannot obtain it by adding request fields or changing session values.
- [ ] Make old whole-run routes honor controls or reject use after employee coordination. A held/cancelled candidate must not be postable through an alternative public route or protected application gateway.
- [ ] Keep error codes distinct for hold, cancellation, missing approval, source staleness and other concurrency conflict. A serialization failure is not automatically proof that a source changed; retries must resolve the receipt before deciding whether work remains.
- [ ] Run both policy cases with already-consumed one-time and already-applied recurring instructions. Both reject a second application, including concurrent competing runs. Test replacement version expiry without requiring all current-source equality in fixed-draft mode.
- [ ] Review the exact SQL/Go enforcement and backward compatibility; commit policy-aware finalization.

## Task C3: prove concurrency, batch outcomes and fixed history

- [ ] Hold one of 100 drafts and finalize the other 99. Verify 99 receipts, one held outstanding draft, no consumption for that draft, and truthful whole-run status. A batch that includes the held draft reports its actual exclusion/conflict without rolling back already committed colleagues.
- [ ] Race hold against commit using transaction barriers. If hold wins, no posting occurs; if commit wins, the later hold fails and the receipt survives. Repeat cancellation/commit and competing finalizations; arbitrary sleeps are not race evidence.
- [ ] Simulate a lost HTTP response after some employee commits. Retry returns existing receipts and finishes eligible remaining employees without duplicate money, applications or liability rows. Preserve current HTTP per-employee transaction boundaries.
- [ ] Prove new monetary content receives a new identity, old approval does not transfer, simulation writes no monetary/application/control state, and complete candidate creation returns fixed content. Reuse existing atomic batch/seal primitives instead of adding a mandatory organizational step.
- [ ] Prove cancel/rebuild consumes nothing until commit, and source expiry/replacement remains permitted throughout review. No day-long source freeze is introduced.
- [ ] Run migration upgrade/refusal tests with controls/reviews/receipts present. Review targeted results and update CP-3.

## Verification

```bash
PAYROLL_TEST_POSTGRES_BIN=/tmp/payroll-postgres16/bin go test ./internal/modules/payroll -run 'Test(DraftControl|EmployeeFinalization|InstructionIntegrity|RecurringInstruction|Finalizer)' -count=1 -v
go test ./cmd/server ./internal/platform/authorization/... -count=1
```

Use the actual new test names consistently with the filter; explicitly run any
new test outside it. The output must show policy B, hold races and alternate-route
denials executing. Do not inherit the old branch's passing status as new evidence.

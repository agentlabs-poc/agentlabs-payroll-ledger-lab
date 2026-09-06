# Payroll compatibility D — annual handoff and public acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Coding agents must use `gpt-5.6-sol`, reasoning effort `medium`, as requested by the user.

**Goal:** Deliver the payroll-side annual package and prove the integrated handbook journey through granted APIs and CLI.

**Architecture:** Use read-only aggregation of committed entries and corresponding settlement evidence. Expose new operations using existing API/CLI conventions and keep official certificate generation separate.

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

## Files and interfaces

Create Core `internal/modules/payroll/annual_package.go`,
`annual_package_repository.go`, `annual_package_test.go` and
`annual_package_db_test.go`. Extend existing reporting handlers/routes and
`cmd/agl-hrms-cli/cmd_payroll_layer1.go`; add
`cmd/agl-hrms-cli/payroll_handbook_journey_test.go`. Update route/permission
manifests and the existing CLI contract tests. Reuse an equivalent read-only
package if CP-0 finds one rather than adding a duplicate API.

The existing `reports.go:GetForm16` and CLI `report form16` are deferred.
Keep that distinction explicit: the annual package is a separate information
handoff, not a claim to issue Form 16.

The proposed annual-package query identifies employee, employer/tenant scope,
reporting period and cutoff. The response contains included entry IDs, scoped
month/component totals, liability/settlement allocations and proof references,
coverage status, missing supplied inputs, and the declared cutoff/snapshot basis.
Use canonical IDs and exact decimal strings from existing contracts.

## Task D1: scoped payroll-side annual package

- [ ] Add database fixtures for employee A/employer X/year Y with twelve posted gross amounts of 50,000, liabilities 12,000, allocated payments 10,000; employee B gross 720,000; A's prior-year gross 480,000; and an additional employer. Assert this package only includes A/X/Y.
- [ ] Implement read-only aggregation with this contract:

```text
select each committed entry in requested payroll scope once
sum its recorded effects by month/component; do not recompute from current salary
select obligations belonging to those entries
sum only their corresponding allocations within the declared cutoff basis
retain corresponding remittance/proof references
report missing expected periods and missing annual inputs as unknown/missing, never zero
```

- [ ] Use one consistent database read snapshot. Define the reporting cutoff separately from payment date and payroll period; return selected record identities and observed-at information. Do not claim repeatable historical snapshots from timestamps alone. If the API promises reproducibility, retain the package manifest through the existing export/evidence mechanism rather than mutating payroll.
- [ ] Use supplied employment/reporting context for expected months. When unavailable, report coverage as unverified; do not assume twelve months for a joiner or claim completeness merely from existing rows.
- [ ] Include supplied annual facts/official-record references through a governed input or handoff context; report missing inputs and their responsible layer. Core performs no tax formula or official issuance decision.
- [ ] Prove gross 600,000, liabilities 12,000, settled 10,000, outstanding 2,000; a later package including another 2,000 settlement has zero outstanding and unchanged payroll gross. Cover multiple results in one employee/month, duplicate references, cross-year settlement, partial allocation of a shared remittance and missing coverage.
- [ ] Review, run the annual tests and commit the read-only package with its public API permission and response contract.

## Task D2: complete CLI access and transport contracts

- [ ] Extend CLI contract/journey tests for exact-draft proposal/approval, controls/history, selected employee finalization, batch outcomes, liability inspection, remittance recording/allocation, and annual package retrieval. Use command groups consistent with the existing `draft`, `ledger` and report commands.
- [ ] Reuse `newPayrollJSONPostCommand`/GET helpers where applicable; ensure IDs remain strings, money is exact, expected hashes/control versions and idempotency keys pass unchanged. Keep token and credential material out of logs.
- [ ] Add command handlers and permission documentation alongside each new API. Handle partial batch outcomes explicitly; a successful HTTP batch envelope must not imply every employee committed.
- [ ] Exercise instruction creation through the repaired adapter, not a direct database seed substitute. Retain CLI simulation behavior and non-writing proof.
- [ ] Run CLI tests, review compatibility/help text and commit the public command unit.

## Task D3: authenticated integrated acceptance

**E2E repository:** `/home/agent-005/workspace/poc/agentlabs-hrms-e2e` is the
currently available checkout. Its `AGENTS.md`, `Makefile` and
`scripts/payroll/README.md` were read during planning. The current authoritative
CLI journey is `scripts/payroll/s03_signoff.sh` plus
`scripts/payroll/s03c_layer1_signoff.py`; ordinary `tests/test_payroll.py` is not
an equivalent substitute for that identity-bound proof.

Create `scripts/payroll/handbook_compat_signoff.py` and
`scripts/payroll/handbook_compat_signoff_contract_test.py`, extending the existing
resumable evidence conventions. Update `scripts/payroll/README.md` and
`Makefile:test-payroll-contracts`. Build scoped fixtures through granted APIs/CLI;
do not substitute privileged SQL for the public journey being certified.

- [ ] Recheck the canonical S03C acceptance instructions and current E2E branch. Create a dedicated E2E branch/worktree; leave unrelated local work intact.
- [ ] Exercise manager intake → finite instruction → complete fixed draft → required approval or authorized alternative → hold/release/selection → commit → ledger/payslip → liability → partial/full remittance → annual handoff.
- [ ] Run the same source-change inputs under policy A and B. Capture exact candidate, policy/control evidence, server and CLI commit identity, scoped principal, and final posted amounts.
- [ ] Exercise the retained subsequent-month adjustment example. Demonstrate the upper-layer after-exit accounting handoff without implementing accounting or changing posted payroll.
- [ ] Add tenant/permission denials, duplicate request replay, lost-response recovery, atomic failure and 99/100 batch evidence. Verify balances and stored authority after each outcome.
- [ ] Preserve existing S03/S03C manifests and add a separately versioned compatibility manifest binding exact Core/CLI identity, tenant, subjects, candidate/control identities, policy mode, amounts and request keys. Use an authorized policy-binding profile for new controls; profile capabilities do not prescribe an organizational headcount. Re-read terminal authority on resume instead of trusting cached success.
- [ ] Run the E2E commands below after configuring the documented profiles and isolated state directories. Record invocation, result, artifact paths and exact commits in Core `docs/payroll-handbook-conformance.md` and E2E evidence. Unavailable credentials or service leave live acceptance open; skipped/setup-failed cases are not success.
- [ ] Review the integrated evidence and commit the acceptance changes. An external blocker leaves CP-4 open even if unit/database tests pass.

## Task D4: final handbook reconciliation

- [ ] Run the master plan's complete local verification once after the final integrated code change; investigate failures before widening tests or retrying blindly.
- [ ] Check every CP-0 matrix row. Add missing evidence or repair a demonstrated mismatch; no row marked `not yet proven` may be reported as full handbook compatibility.
- [ ] Update Core and handbook implementation status with full SHAs, migration numbers, API/CLI coverage, selected test policy configurations and remaining external delivery boundaries. Preserve historical findings and Q-020's superseded rationale.
- [ ] Review the final diff for policy accidentally embedded in generic operations, exposed bypasses, changed posted history and unsupported issuance claims. Commit documentation and present CP-5 results.

## Verification

```bash
PAYROLL_TEST_POSTGRES_BIN=/tmp/payroll-postgres16/bin go test ./internal/modules/payroll -run 'TestAnnualPackage' -count=1 -v
go test ./cmd/agl-hrms-cli -count=1
```

In the E2E worktree, run the existing contract target extended with the new
script tests, then the new live journey with the documented authenticated
profiles and exact server-commit configuration:

```bash
make test-payroll-contracts
python3 scripts/payroll/handbook_compat_signoff.py --preflight-only
python3 scripts/payroll/handbook_compat_signoff.py
```

The new script is a planned deliverable, not an existing runnable command.
Use a completed identity-bound S03/S03C baseline or run their documented public
journeys in the disposable acceptance environment. Its preflight must verify
policy-control grants and sufficient scoped fixture permissions before payroll
mutations. Full release validation remains the E2E `AGENTS.md` sequence when a
release is requested. Final execution also runs all master-plan checks.
No shipping, merging, deployment or statutory issuance is implied by these tests.

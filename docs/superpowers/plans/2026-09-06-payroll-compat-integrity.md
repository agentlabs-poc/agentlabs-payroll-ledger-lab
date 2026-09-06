# Payroll compatibility A — source and application integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Coding agents must use `gpt-5.6-sol`, reasoning effort `medium`, as requested by the user.

**Goal:** Repair the source API and preserve instruction identities, lifetime and atomic application semantics.

**Architecture:** Port the policy-independent migration/source fixes from the preserved candidate. Use the existing governed source gateway and keep its authority validation intact.

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

Modify `internal/modules/payroll/payroll_instruction_authority_repository.go`,
`calculation_governed_source.go`, and the available numbered migration corresponding
to candidate `000092_payroll_instruction_integrity.{up,down}.sql`.
Port `instruction_integrity_db_test.go` and required isolated test helpers.
Create `internal/modules/payroll/instruction_version_api_db_test.go`.
Extend `payroll_instruction_authority_test.go` and
`cmd/agl-hrms-cli/payroll_layer1_journey_test.go` where the public path needs coverage.

Keep `CreateInstructionVersion`'s Go interface and the existing protected
`payroll_create_instruction_version` 17-argument signature. Correct the adapter
call and casts to match that SQL declaration exactly. No public request field
needs changing for this defect. Preserve `recurringInstructionsConsumedInPeriod`
from the candidate as the eligibility query for logical instruction/month.

## Task A1: repair real instruction-version creation

- [ ] Add `TestInstructionVersionPublicCreationPreservesFields` using the existing granted source handler/service setup. Send one amount-backed request and one JSON-input request; read back cadence, component version, currency/input, effective dates and principal evidence. Do not bypass the adapter under test.
- [ ] Run the new test and confirm the baseline fails at the incorrect SQL invocation, not from missing authorization or fixtures.
- [ ] Change the query to the existing gateway's exact parameter order:

```sql
SELECT version_id, version, input_hash, created_at
FROM payroll_create_instruction_version(
  $1,$2,$3,$4,$5,$6::numeric,$7,$8::jsonb,$9,$10,$11,$12,$13,$14,$15,$16,$17
);
```

- [ ] Verify the SQL declaration's types before retaining these casts; preserve tenant, actor, subject and executor-type positions. Exercise the command's normal create/review/activate sequence, request retry, and a different-tenant denial.
- [ ] Run targeted tests below, inspect the actual returned fields, review and commit `fix: align payroll instruction version gateway arguments`.

## Task A2: retain storage and application integrity

- [ ] Port the candidate key/index/application tests before the migration and source change. Confirm the specific baseline failures for a 101/160-character key and repeated recurring application.
- [ ] Apply the policy-independent migration and source filter together. Keep these constraints:

```sql
ALTER TABLE payroll_instruction_applications ALTER COLUMN stable_key TYPE varchar(160);
CREATE UNIQUE INDEX uq_payroll_instruction_applications_recurring_period
ON payroll_instruction_applications(tenant_id,employee_id,instruction_id,year,month)
WHERE cadence='recurring';
```

- [ ] Retain the candidate's full catalog equivalence check before removing duplicate indexes. Preserve unique constraints; migration must fail on semantic drift or duplicate historical applications, and downgrade must refuse to truncate long keys.
- [ ] Run key lengths 100/101/160, concurrent same-month attempts across runs/versions, next month, another tenant/employee, and exact retry. Keep the documented one-time-to-recurring regression; do not infer that two different logical instructions represent one business request.
- [ ] Review and commit the retained migration/source changes independently from controls and contributions.

## Task A3: prove finite lifetime and immutable sources

- [ ] Extend the governed-source integration cases with a September-through-January standing instruction. Prove exactly those five target months eligible, February excluded, and a September run performed later still evaluates September's period.
- [ ] Prove a skipped month does not extend the supplied expiry; expiry/replacement retains original source content. Source history cannot be updated in place through the application role.
- [ ] Prove draft creation and cancellation consume no instruction; a successful final commit records consumption/application atomically. Where cancellation requires package C, register that dependent case in C and leave the combined gate open until it passes.
- [ ] Reuse existing finite/open interval support without inventing loan balance accounting. Repair an existing path only if these concrete cases expose a mismatch; preserve supplied dates and business amounts.
- [ ] Review the source evidence, commit any required repair, and update CP-1.

## Verification

```bash
PAYROLL_TEST_POSTGRES_BIN=/tmp/payroll-postgres16/bin go test ./internal/modules/payroll -run 'Test(Instruction|Recurring|ValidatePayrollInstruction)' -count=1 -v
go test ./cmd/agl-hrms-cli -run 'Payroll' -count=1
```

Every new integration test must run, not skip. This package does not claim that
policy B or holds work before package C. Return the commit, failing/passing
regression evidence, and the exact public request/response fields checked.

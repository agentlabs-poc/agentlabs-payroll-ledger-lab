# Payroll compatibility B — contributions and liabilities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Coding agents must use `gpt-5.6-sol`, reasoning effort `medium`, as requested by the user.

**Goal:** Represent explicit contribution pairs and payroll-backed obligations with accurate settlement history.

**Architecture:** Keep pair validation and three distinct settlement records. Move country classification to an explicit adapter contract, while protected posting validates the declared metadata and creates the obligation atomically.

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

Modify Core `internal/modules/payroll/employer_contribution.go`,
`candidate_batch.go`, `candidate_batch_repository.go`, `ledger_service.go`,
`ledger_projection.go`, `ledger_reporting.go`, `reports.go`,
`liability_register.go`, `liability_register_repository.go` and their candidate tests.
Reshape candidate migrations `000093_payroll_employer_contribution_pairs` and
`000094_payroll_liability_register` under the sequence selected at CP-0.
Create `internal/modules/payroll/liability_classification.go` for the country
adapter boundary and `liability_classification_test.go` for its mapping cases.
Wire routes/permissions with existing `routes.go`, `register.go`,
`internal/platform/authorization/manifest.go` and database authority inventories.

The proposed batch addition is explicit mechanical pair intent on the submitted
operation, `representation: "employer_contribution_pair"`. The authorized producer
supplies the amount; Core generates only the equal earning/deduction representation.
It returns the complete fixed candidate before review. Existing request versions
must retain their documented behavior; use a versioned batch contract for a
changed representation rule. Simulation and application use the same expansion.

The proposed liability metadata is `authority_key`, optional `jurisdiction_key`,
and `classification_version`, bound to the component/proposal authority and
included in the fixed candidate's authority representation. Amount and currency
come from the posted entry, never from a separate free-form obligation request.
Country adapters map PF/ESI/PT/TDS into that contract; Core validates supplied
scope and registered metadata instead of hardcoding a four-value enum.

## Task B1: make pair production explicit

- [ ] Add cases to `employer_contribution_test.go` and candidate batch tests: explicit pair, omitted intent under the new contract, malformed pair, mismatched currency, retry, simulation and retained historical `none` entry during amendment.
- [ ] Establish expected totals using exact decimal values:

```text
salary earning       +50000.00
contribution earning  +1000.00
contribution deduction -1000.00
gross=51000.00; deductions=1000.00; net=50000.00; obligation basis=1000.00
```

- [ ] Replace implicit new-contract classification expansion with the declared representation. Reserve internal linkage metadata against caller forgery. Reject incomplete required pairs before sealing; never silently drop a contribution or emit half a pair.
- [ ] Remove blanket conversion of retained historical `none` rows in a fresh amendment under the new contract. Require explicit conversion intent; keep original history and replay unchanged. Review the old request-version compatibility path separately.
- [ ] Keep Go/SQL pair checks, derived totals, linked reversals and reports consistent; test that a new amount has a new candidate identity and receives no transferred approval.
- [ ] Run the contribution tests red then green, review migration and gateway consistency, and commit the pair-contract change.

## Task B2: preserve generic obligation and remittance authority

- [ ] Port partial payment, concurrent allocation, replay, backfill and immutable-history tests from `liability_register_db_test.go`. Add an authorized non-PF/ESI/PT/TDS classification case and an unrecognized/unauthorized classification denial.
- [ ] Replace new-table category/state hardcoding with the governed metadata relationship. Keep tenant foreign keys, unique posted-entry authority, immutable obligations/remittances/allocations and proof requirements. No arbitrary liability amount is accepted.
- [ ] Move the current four-category reporting-tag/state map into `liability_classification.go` or an existing country adapter discovered at CP-0. Preserve original jurisdiction on correction; a changed employee work state cannot reroute old authority.
- [ ] Bind classification before draft sealing and retain it through posting. An updated adapter after approval cannot silently change the destination of a fixed proposal. For historical backfill, derive only from recorded historical authority; missing classification must be reported, not fabricated.
- [ ] Retain allocation checks with the following transaction invariant:

```text
lock corresponding obligation and remittance balances
require same tenant, authority, applicable jurisdiction and currency
require 0 < allocation <= outstanding obligation
require allocation <= unallocated remittance
append allocation and idempotent receipt together
```

- [ ] Prove 10,000 obligation + 6,000 allocation leaves 4,000; later 4,000 closes it with both proofs. Prove concurrent allocations cannot exceed either side, wrong scope/currency fails, and one contribution pair creates one obligation.
- [ ] Review schema/query suitability using actual lookup paths and catalog evidence; retain three tables because their records have separate histories. Commit the register/adapter unit.

## Task B3: corrections and compatibility

- [ ] Test a supplied subsequent-month adjustment linked to the original payroll. Original entries, amounts, application records and payment proofs remain byte-for-byte unchanged.
- [ ] Keep paired reversal mechanics where the explicit correction requests them; do not automatically restore instruction eligibility or settle a credit against another obligation.
- [ ] Preserve signed credit evidence without claiming an automatic refund or allocation policy. Test the original jurisdiction and amount in historical backfill and correction paths.
- [ ] Verify the upper-layer journey routes an after-exit correction to accounting; do not add a universal Core business-policy inference. Core continues to protect already posted history regardless of the caller's workflow.
- [ ] Run targeted tests and migration compatibility checks, review the B1/B2 integration, and update CP-2.

## Verification

```bash
PAYROLL_TEST_POSTGRES_BIN=/tmp/payroll-postgres16/bin go test ./internal/modules/payroll -run 'Test(Employer|Contribution|Liability|Candidate)' -count=1 -v
go test ./internal/platform/authorization/... -count=1
```

Test both baseline upgrade and retained historical records. Inspect tests whose
names fall outside the filter and run them explicitly. Return exact migration
numbers, representation version, classification contract, proof examples and
remaining delivery gaps; CLI coverage closes in package D.

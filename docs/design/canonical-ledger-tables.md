# Canonical ledger table mapping and deprecation register

**Lab design pin, 2026-09-08.** Retained here at the user's request. Read the [design index](README.md) for status and ownership. This is readable design content, not a forwarding page.

Initial pin reconciled with [Core source at `b72312a`](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/docs/payroll/ledger-table-mapping.md). Acceptance and proposal labels below remain in force; the browser lab and production schema are unchanged.

**Subsequent pinned design direction, 2026-09-08:** review the 16 supporting
tables for consolidation into one shared `tenant / key / value / ts` table.
The [canonical-record chapter](payroll-records.md) records the component
example, other candidate entries, rationale and all 16 proposed mappings. The
chapter also records a proposed fifth availability column, `state`. The
inventory below still describes existing physical storage; supporting roles do
not require retaining 16 separate tables. No replacement migration has occurred.

**User-directed disposition, 2026-09-08.** The user instructed: “anything that is
not mapping to our canonical ledgers should be depricated.” Apply that rule to
the current payroll schema: a retained table needs a concrete canonical ledger
role or a necessary supporting role for its records and guarantees. A foreign
key to payroll or an existing runtime dependency alone is insufficient.

The canonical ledgers are Salary Earning, monthly standing instructions, one-time
instructions, the fixed employee Draft Ledger, the committed Payroll Ledger,
and the Employer-Liability Register. See [core concepts](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/docs/payroll/handbook/core-concepts.md)
and [123 Architecture](123-architecture.md).

## Scope and meaning of status

This inventory covers **58 payroll and payroll-adjacent tables: 9 canonical L1
ledger tables, 16 L1 supporting tables, 1 candidate L2 output table and 32
deprecated structures**. It enumerates payroll-prefixed tables,
`employee_payroll_*` tables and the explicitly listed salary, payslip, tax,
advance, challan and settlement tables from current up-migrations. Shared HRMS
authentication, employee, workflow, extension-engine and general configuration
storage is outside this payroll-schema disposition. This is a source inventory,
not a live database catalog inspection.

- **Canonical L1 ledger** marks the nine table names and ledger responsibilities
  confirmed by the user below. It does not certify every existing column,
  lifecycle, dependency or API contract as conformant.
- **Mapped support/candidate** identifies a justified supporting responsibility. It does
  not approve the exact table design, every stored operation, current API shape,
  mandatory workflow, source tracing or run dependency.
- **Deprecated** marks the existing structure as unaccepted for the canonical
  core-payroll design. A potential L2/L3 purpose does not reinstate it without
  reconciliation with L1. For adjacent tax/loan domains, this is a disposition
  of their role in core payroll, not an instruction to delete unrelated records.

All existing data and dependencies remain. This marking changes documentation
only: no DROP/ALTER/COMMENT statements are executed, and historical migrations,
runtime behavior and schema privileges are unchanged. No replacement table names,
removal date or migration plan are invented. The register is the canonical schema
status; old migration declarations describe what was implemented.

## Canonical ledger mappings by layer

### Layer 1: canonical ledger tables

**User-confirmed canonical, 2026-09-08.** After reviewing this L1 ledger list,
the user instructed: “can you mark these table as canonical layer-1 ledgers”.
All nine tables below are designated **Canonical L1 ledger tables** for their
stated roles. The 16 supporting tables in the next section remain separate.
Existing implementation conformance gaps remain open.
**Salary Earning Ledger: no accepted standalone representation identified.**
Standing and one-time instructions share physical storage while retaining their
separate canonical meanings.

| Table | Canonical mapping and limits | Schema source |
|---|---|---|
| `payroll_calculation_revisions` | Draft Ledger: identifiable content revisions and retained basis; current mutable preparation is not approved by this mapping. | [000075](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000075_payroll_calculations.up.sql) |
| `payroll_calculations` | Draft Ledger: employee-period calculation identity; current run dependency still needs reconciliation. | [000075](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000075_payroll_calculations.up.sql) |
| `payroll_draft_entries` | Draft Ledger: proposed employee earning/deduction entries. | [000076](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000076_payroll_draft_ledger.up.sql) |
| `payroll_instruction_versions` | Instruction ledgers: immutable content, cadence and applicability. Group 3 URI/lifecycle conformance remains open. | [000080](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000080_payroll_fact_instruction_authority.up.sql) |
| `payroll_instructions` | Standing and one-time instruction ledgers: employee instruction identity. | [000080](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000080_payroll_fact_instruction_authority.up.sql) |
| `payroll_ledger_entries` | Payroll Ledger: immutable committed monetary entries. | [000077](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000077_payroll_posted_ledger.up.sql) |
| `payroll_statutory_allocations` | Employer-Liability Register: explicit settlement amounts linking remittances and obligations. | [000094](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000094_payroll_liability_register.up.sql) |
| `payroll_statutory_obligations` | Employer-Liability Register: obligations arising from posted payroll. | [000094](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000094_payroll_liability_register.up.sql) |
| `payroll_statutory_remittances` | Employer-Liability Register: immutable remittance amounts and supplied proof. | [000094](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000094_payroll_liability_register.up.sql) |

### Layer 1: necessary supporting records

These support the named ledgers and their guarantees; they are not additional
canonical ledgers. Keeping a role does not approve an independent public resource
or grandfather unrelated uses of shared storage.

| Table | Canonical mapping and limits | Schema source |
|---|---|---|
| `payroll_calculation_candidates` | Draft Ledger: fixed employee candidate identity/content hashes referenced by reviews and commit receipts. | [000082](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000082_payroll_candidate_authority.up.sql) |
| `payroll_candidate_batches` | Draft Ledger: one-calculation operation replay evidence; not a canonical cross-employee batch resource. | [000082](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000082_payroll_candidate_authority.up.sql) |
| `payroll_candidate_instruction_resolution_links` | Draft and instruction ledgers: links from those resolutions to their entry effects. | [000082](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000082_payroll_candidate_authority.up.sql) |
| `payroll_candidate_instruction_resolutions` | Draft and instruction ledgers: proposed instruction effects used to record committed applications. | [000082](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000082_payroll_candidate_authority.up.sql) |
| `payroll_component_versions` | Salary, instruction, draft and posted ledgers: exact component definition used by an entry; Group 1 remains unchanged. | [000073](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000073_payroll_component_versions.up.sql) |
| `payroll_draft_control_events` | Draft Ledger: retained history of its controls. | [000096](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000096_payroll_draft_controls.up.sql) |
| `payroll_draft_controls` | Draft Ledger: applicable authorized controls for the exact employee draft. | [000096](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000096_payroll_draft_controls.up.sql) |
| `payroll_employee_candidate_reviews` | Draft Ledger: review evidence bound to an exact employee proposal. | [000095](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000095_payroll_employee_finalization.up.sql) |
| `payroll_employee_finalization_receipts` | Draft and Payroll Ledgers: durable individual commit outcome and replay evidence. | [000095](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000095_payroll_employee_finalization.up.sql) |
| `payroll_entry_batches` | Draft Ledger: entry-operation replay evidence. Relief-only use inherits the relief-contract deprecation. | [000076](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000076_payroll_draft_ledger.up.sql) |
| `payroll_fields` | Salary, instruction, draft and posted ledgers: earning/deduction component identity; explicitly retained in Group 1. | [000053](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000053_payroll_fields.up.sql) |
| `payroll_http_idempotency` | Canonical ledger operations: HTTP request replay protection. Deprecated endpoint receipts remain historical evidence. | [000086](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000086_payroll_http_idempotency.up.sql) |
| `payroll_instruction_application_effects` | Instruction applications: links to their actual posted monetary effects. | [000084](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000084_payroll_instruction_applications.up.sql) |
| `payroll_instruction_applications` | Instruction ledgers and Payroll Ledger: committed instruction consumption/application. | [000084](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000084_payroll_instruction_applications.up.sql) |
| `payroll_mutation_evidence` | Canonical ledger operations: retained actor, action and before/after evidence. This does not admit unrelated operation families. | [000073](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000073_payroll_component_versions.up.sql) |
| `payroll_source_authority_actions` | Instruction ledgers: source-operation replay/evidence. Generic fact uses inherit fact-contract deprecation. | [000080](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000080_payroll_fact_instruction_authority.up.sql) |

### Layer 2: software-owned auxiliary primitives

**No existing physical table design has been accepted as canonical L2 storage
in this review.** 123 Architecture permits L2 to own reusable packages and other
auxiliary records. Their canonical concepts and operations must be defined, and
their use of L1 reconciled, before accepting a table design. Existing compensation,
run, calculation-input and other auxiliary structures remain in the deprecated
inventory below; they are not reinstated by assigning them an L2 label.

One existing output table has a concrete Payroll Ledger mapping. It is listed
here as a candidate auxiliary projection, not as a core ledger or an accepted
L2 table design.

| Table | Canonical mapping and limits | Schema source |
|---|---|---|
| `payslips` | Payroll Ledger: derived output; candidate L2 placement, not an approved table design. Run coupling remains unresolved. Posted-ledger provenance: [migration 77](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000077_payroll_posted_ledger.up.sql#L960). | [000009](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000009_payroll.up.sql) |

### Layer 3: application or AI composition

**No canonical L3 tables have been prescribed in HRMS Core.** A task-specific
composition does not create a new core ledger or obtain direct mutation authority
over L1 records. Any application-owned persistence needs its own explicit
contract; this register does not invent table names or schemas for it.

## Deprecated: no accepted canonical ledger mapping

| Table | Reason for deprecation | Schema source |
|---|---|---|
| `advance_recoveries` | Loan/advance servicing and recovery tracking. Core represents supplied earning/deduction instructions and their payroll applications. | [000055](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000055_employee_advances.up.sql) |
| `employee_advances` | Loan/advance servicing and recovery tracking. Core represents supplied earning/deduction instructions and their payroll applications. | [000055](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000055_employee_advances.up.sql) |
| `employee_payroll_fact_versions` | Generic typed calculation-input catalog; no established mapping to a canonical salary/instruction ledger. Possible L2 input capability is not yet approved. | [000080](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000080_payroll_fact_instruction_authority.up.sql) |
| `employee_payroll_facts` | Generic typed calculation-input catalog; no established mapping to a canonical salary/instruction ledger. Possible L2 input capability is not yet approved. | [000080](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000080_payroll_fact_instruction_authority.up.sql) |
| `employee_salary` | Legacy salary-template/assignment shape; no accepted component-level Salary Earning Ledger contract. Potential auxiliary reuse requires redesign/review. | [000009](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000009_payroll.up.sql) |
| `full_final_settlements` | Full-and-final business workflow; no canonical L1 ledger mapping. The handbook places after-exit correction processing in accounting. | [000060](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000060_full_final_settlements.up.sql) |
| `payroll_challan_authority_evidence` | Legacy filing/run-manifest contract; the canonical liability model records obligations, proof-bearing remittances and allocations separately. Preserve existing evidence. | [000077](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000077_payroll_posted_ledger.up.sql) |
| `payroll_compensation_plan_assignments` | Existing compensation-plan workflow/storage; Group 2 APIs already deprecated. It is not the accepted Salary Earning Ledger representation. | [000079](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000079_payroll_compensation_plans.up.sql) |
| `payroll_compensation_plan_batches` | Existing compensation-plan workflow/storage; Group 2 APIs already deprecated. It is not the accepted Salary Earning Ledger representation. | [000079](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000079_payroll_compensation_plans.up.sql) |
| `payroll_compensation_plan_lines` | Existing compensation-plan workflow/storage; Group 2 APIs already deprecated. It is not the accepted Salary Earning Ledger representation. | [000079](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000079_payroll_compensation_plans.up.sql) |
| `payroll_compensation_plan_versions` | Existing compensation-plan workflow/storage; Group 2 APIs already deprecated. It is not the accepted Salary Earning Ledger representation. | [000079](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000079_payroll_compensation_plans.up.sql) |
| `payroll_compensation_plans` | Existing compensation-plan workflow/storage; Group 2 APIs already deprecated. It is not the accepted Salary Earning Ledger representation. | [000079](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000079_payroll_compensation_plans.up.sql) |
| `payroll_employee_run_coordination` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000095](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000095_payroll_employee_finalization.up.sql) |
| `payroll_fact_definition_versions` | Generic typed calculation-input catalog; no established mapping to a canonical salary/instruction ledger. Possible L2 input capability is not yet approved. | [000080](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000080_payroll_fact_instruction_authority.up.sql) |
| `payroll_fact_definitions` | Generic typed calculation-input catalog; no established mapping to a canonical salary/instruction ledger. Possible L2 input capability is not yet approved. | [000080](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000080_payroll_fact_instruction_authority.up.sql) |
| `payroll_payment_evidence` | Run-level bank-payment acknowledgment/manifest; not payroll commit or employer remittance settlement. | [000077](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000077_payroll_posted_ledger.up.sql) |
| `payroll_prepare_batches` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000075](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000075_payroll_calculations.up.sql) |
| `payroll_relief_applications` | Nonmonetary relief definitions/decisions; not monetary draft entries or committed instruction applications. No canonical ledger role established. | [000076](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000076_payroll_draft_ledger.up.sql) |
| `payroll_relief_versions` | Nonmonetary relief definitions/decisions; not monetary draft entries or committed instruction applications. No canonical ledger role established. | [000074](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000074_payroll_relief_catalog.up.sql) |
| `payroll_reliefs` | Nonmonetary relief definitions/decisions; not monetary draft entries or committed instruction applications. No canonical ledger role established. | [000074](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000074_payroll_relief_catalog.up.sql) |
| `payroll_run_calc_extension_pins` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000066](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000066_payroll_calc_extension_pins.up.sql) |
| `payroll_run_candidate_actions` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000083](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000083_payroll_candidate_actions.up.sql) |
| `payroll_run_candidate_members` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000082](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000082_payroll_candidate_authority.up.sql) |
| `payroll_run_candidates` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000082](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000082_payroll_candidate_authority.up.sql) |
| `payroll_run_revision_actions` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000081](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000081_payroll_snapshot_revisions.up.sql) |
| `payroll_runs` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000009](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000009_payroll.up.sql) |
| `payroll_schedules` | Run-wide orchestration, configuration or evidence for that workflow; no canonical L1 ledger role. Existing run APIs are deprecated. | [000020](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000020_payroll_schedules.up.sql) |
| `salary_structures` | Legacy salary-template/assignment shape; no accepted component-level Salary Earning Ledger contract. Potential auxiliary reuse requires redesign/review. | [000009](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000009_payroll.up.sql) |
| `statutory_challans` | Legacy filing/run-manifest contract; the canonical liability model records obligations, proof-bearing remittances and allocations separately. Preserve existing evidence. | [000059](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000059_statutory_challans.up.sql) |
| `tax_declarations` | Tax evidence/election/cutoff workflow, not a canonical payroll ledger. A separate tax or auxiliary capability requires its own contract. | [000023](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000023_tax_declarations.up.sql) |
| `tax_regime_elections` | Tax evidence/election/cutoff workflow, not a canonical payroll ledger. A separate tax or auxiliary capability requires its own contract. | [000054](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000054_tax_regime_elections.up.sql) |
| `tax_regime_period_locks` | Tax evidence/election/cutoff workflow, not a canonical payroll ledger. A separate tax or auxiliary capability requires its own contract. | [000077](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000077_payroll_posted_ledger.up.sql) |

## Consequences and unresolved compatibility

There is no approved standalone Salary Earning Ledger representation identified
by this audit. The legacy salary and compensation-plan tables cannot be accepted
as that ledger solely because they currently supply salary inputs.

Standing/monthly and one-time instructions share two physical tables. Their
canonical meanings remain distinct; mapping their records does not settle Group
3's URI/approval/expiry/replacement review. Source-operation evidence shared with
generic facts is retained only for its justified instruction role. Similarly,
entry-batch evidence remains justified for monetary drafts, not as approval of
the separate relief-application contract.

Draft and posted records still reference runs and other deprecated structures.
Those dependencies are explicit implementation gaps, not reasons to delete data
or remove required tables immediately. The same applies to payslip projections,
which must derive their money from the Payroll Ledger. Physical support-table
names do not automatically become canonical public URI resources.

The existing [run API](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/docs/payroll/run-api-deprecation.md) and
[compensation-plan API](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/docs/payroll/compensation-api-deprecation.md) markings remain. This
register does not silently edit other endpoint registrations. Subsequent API
group review must reconcile any endpoints exposing deprecated structures before
accepting them as canonical. Table count alone establishes neither correctness
nor performance. This disposition does not establish merge readiness.

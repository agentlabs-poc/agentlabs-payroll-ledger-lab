# Payroll database table review

Review date: 2026-09-06. The user requested review of the actual database
tables, in addition to closing handbook gaps.

**Conclusion: the schema has useful integrity structures, but is not yet a
good fit for every agreed payroll rule.** Correct the mismatches and redundant
indexes before considering wider consolidation. Table count alone does not
establish whether this model is optimal.

## Evidence and scope

The payroll lab has in-memory TypeScript stores and no database migrations.
This review examines the HRMS Core database migrations and their consuming code.
Fetched `origin/main` is `3a87931ea536c8b617e6e391c14affd03ade9f65`.
The existing local checkout remains at
`13621844165b31346facc53c4b45bbd8d9437816`; comparison shows the reviewed payroll
migrations and referenced implementation files are unchanged between those
revisions. The newer migration 91 concerns local identity mapping.

This is a source-backed design review, not inspection of a deployed catalog or
a measured performance benchmark. No schema, runtime code, or business data
was changed. The numbered browser-lab gaps and these HRMS Core findings describe
different implementations and must not be conflated.

## Findings in priority order

### PAY-DB-001 — challan records do not represent the agreed settlement ledger

**High priority: model mismatch against PAY-CORE-012/016.**
`statutory_challans` has an amount due, one challan number/date, and a filing
status. Its unique key is tenant/type/state/month/year, and recording the same
key updates that row. `payroll_challan_authority_evidence` preserves the
calculated liability manifest, but does not supply separate remitted amounts
and employee-obligation settlement allocations.

Consequently, this shape cannot directly represent our INR 10,000 obligation,
INR 6,000 remittance with proof, INR 4,000 still outstanding, then another
INR 4,000 remittance with its own proof. Replacing the period's challan number
is not equivalent to retaining both settlements and their allocated amounts.

Recommendation: distinguish obligation records, actual remittance/proof records,
and allocations connecting them. The filing tracker can remain a projection if
needed. These are separate record responsibilities; exact new table names and
migration compatibility have not been selected. Do not treat an amount due as
an amount remitted or use a filing-status change to close every liability.

Evidence: [migration 59](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000059_statutory_challans.up.sql#L10),
[migration 77 evidence structure](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000077_payroll_posted_ledger.up.sql#L1850),
[period upsert](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000077_payroll_posted_ledger.up.sql#L2205).

### PAY-DB-002 — employer-contribution classification conflicts with agreed gross

**High priority: model mismatch against PAY-CORE-014.** The component schema
classifies employer contributions as employer cost. Draft enforcement derives
their effect as `none`; `deriveLedgerTotals` collects that effect into a separate
employer total, excluding it from gross and deductions.

That is different from our agreed contribution earning plus matching deduction:
INR 50,000 other earnings plus INR 1,000 contribution should produce INR 51,000
gross, INR 1,000 deduction, and INR 50,000 net. The dedicated employer-contribution
path currently leaves gross at INR 50,000. Generic earning/deduction components
can express a pair, but that does not make the existing dedicated classification
conform to the handbook.

Recommendation: align component classification, produced entries, projection
totals, and corresponding liability creation together. Preserve one obligation
for the pair. A new table or an index change alone cannot fix this mismatch.

Evidence: [component classification](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000073_payroll_component_versions.up.sql#L162),
[derived draft effect](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000076_payroll_draft_ledger.up.sql#L406),
[totals calculation](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/internal/modules/payroll/ledger_service.go#L2999).

### PAY-DB-003 — instruction keys narrow from 160 to 100 characters at finalization

**High priority: concrete schema/API inconsistency.** `payroll_instructions.stable_key`
allows 160 characters. The create validator accepts that same length. However,
`payroll_instruction_applications.stable_key` allows only 100, and the finalizer
copies the original key into it without narrowing or an earlier 100-character
limit.

A 101-character lowercase key passes the declared creation pattern and source
column width, then exceeds the application column's width when that instruction
is applied. This is a statically confirmed data-path inconsistency; a complete
database payroll reproduction was not executed in this review. PostgreSQL
rejects overlength insertion into `varchar(n)` rather than accepting arbitrary
longer values. [PostgreSQL 16 character types](https://www.postgresql.org/docs/16/datatype-character.html).

Recommendation: make the copied field compatible with the already accepted
source contract, then verify lengths 100, 101, and 160 through creation and
finalization. Do not silently truncate a stable instruction identity.

Evidence: [source column](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000080_payroll_fact_instruction_authority.up.sql#L183),
[create validation](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/internal/modules/payroll/payroll_instruction_authority.go#L153),
[application column](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000084_payroll_instruction_applications.up.sql#L13),
[finalizer copy](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000084_payroll_instruction_applications.up.sql#L707).

### PAY-DB-004 — two indexes duplicate existing unique-constraint indexes

**Optimization opportunity confirmed in migration definitions.**

| Explicit index | Existing unique constraint with the same ordered columns |
|---|---|
| `idx_employee_payroll_facts_employee` | `uq_employee_payroll_facts_identity`: tenant_id, employee_id, definition_id |
| `idx_payroll_instructions_employee` | `uq_payroll_instructions_stable_key`: tenant_id, employee_id, stable_key |

Both additional indexes use the same plain column sequence, with no different
predicate or included columns. A unique constraint already creates a B-tree
index on its columns. [PostgreSQL 16 constraints](https://www.postgresql.org/docs/16/ddl-constraints.html).

Recommendation: inspect the deployed definitions/dependencies, retain the unique
constraints, and remove the redundant explicit indexes through a compatible
migration when implementation resumes. Do not drop the unique constraints.
The amount of storage/write overhead saved has not been measured.

Evidence: [fact identity constraint](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000080_payroll_fact_instruction_authority.up.sql#L110),
[instruction constraint](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000080_payroll_fact_instruction_authority.up.sql#L197),
[explicit indexes](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000080_payroll_fact_instruction_authority.up.sql#L288).

### PAY-DB-005 — grouping is supported, but run finalization is a different unit

**Model alignment required against PAY-ARCH-002/PAY-CORE-015.** Posted entries
have an index beginning with tenant, employee, year, month. This supports our
employee-month association without prescribing any particular generated ID.
There is no need to add an employee-month table solely to obtain a canonical
number.

However, calculation identity is scoped to a run/employee/kind, and the exposed
database finalizer commits the run aggregate. This is different from the agreed
employee-period draft commit unit with batches retaining individual outcomes.
Adding a grouping key would not change that transaction boundary.

Recommendation: preserve employee/month querying and exact draft identities;
review the run finalizer and candidate membership together when implementing
individual employee outcomes. Treat run/candidate structures as coordination
where they serve that purpose, not as a reason to impose batch-wide finality.

Evidence: [calculation identity](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000075_payroll_calculations.up.sql#L48),
[employee-period index](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000077_payroll_posted_ledger.up.sql#L816),
[run finalizer](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/internal/modules/payroll/posted_ledger_repository.go#L228).

### PAY-DB-006 — monthly application uniqueness needs explicit closure evidence

**Constraint-coverage finding, not a reproduced duplicate-payroll incident.**
Applications have unique run/version and one-time version keys. The recurring
employee/month path has no corresponding unique constraint in the inspected
table. A non-unique version/year/month index supports reads but does not itself
prevent a second application from another run in that month.

Source loading excludes consumed one-time versions and passes prior-use history
for recurring versions to calculation. That is useful evidence, but is not a
database uniqueness guarantee. Do not assume there is no other control merely
from the missing index; demonstrate the same-month competing-run case through
the supported finalization path before claiming closure.

Recommendation: enforce PAY-CORE-004 at the protected application boundary and
verify competing runs plus the next eligible month. Match the enforcement key
to the selected instruction-application identity, without inferring whether two
different instructions represent the same business request.

Evidence: [application keys](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/migrations/000084_payroll_instruction_applications.up.sql#L22),
[prior-use loading](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/internal/modules/payroll/instruction_application.go#L26),
[source filtering](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/3a87931ea536c8b617e6e391c14affd03ade9f65/internal/modules/payroll/calculation_governed_source.go#L291).

## Structures worth retaining and simplification boundaries

| Table family | Review disposition |
|---|---|
| Source identities and immutable/effective versions | Useful separation of stable identity and changing applicability; keep lifetime and history constraints |
| Compensation plans, lines, and assignments | Represent entitlement independently of committed amounts; distinguish current governed sources from legacy salary projections before consolidating |
| Instructions and instruction versions | One physical instruction family with cadence can represent the two logical instruction ledgers; two logical concepts do not require two duplicate physical schemas |
| Draft entries and posted ledger entries | Distinct reviewable and final lifecycles justify separation; align draft immutability with complete creation |
| Instruction applications and monetary effects | Preserve consumption/application separately from later monetary correction; keep immutability and exact links |
| Calculation/run candidates and action evidence | Review against the selected employee commit boundary; do not merge solely to reduce table count |
| Payslips and statutory trackers | Keep as clearly derived views/snapshots where appropriate; avoid competing sources of monetary truth |

Tenant-scoped foreign keys, effective-range exclusion constraints, immutable
posted/application records, and employee-period indexes are useful existing
controls. These observations do not constitute a complete tenant-isolation audit.

Several tables retain relational fields, JSON, exact bytes, hashes, and principal
metadata. Some of that duplication preserves historical snapshots or exact
request evidence. Review its purpose and measured size before removing it.
Mandatory business-source tracing is not part of the agreed core, but that does
not imply all actor, approval, or instruction-application evidence is redundant.

## What would establish performance suitability

A deployed-schema check should compare catalog definitions with these migrations,
then measure the actual queries for employee/month payroll, annual aggregation,
eligible source selection, application checks, and outstanding liabilities.
Use representative row volumes and query plans before adding broader indexes,
partitioning, or denormalized totals. PostgreSQL's EXPLAIN documentation explains
how to assess plans and actual execution; no such benchmark was run here.
[PostgreSQL 16 EXPLAIN guidance](https://www.postgresql.org/docs/16/using-explain.html).

The immediate conclusion is therefore specific: resolve the ledger/settlement
and lifecycle mismatches, align the instruction-key contract, and remove proven
index duplication after catalog verification. Wider performance optimization
still requires workload evidence.

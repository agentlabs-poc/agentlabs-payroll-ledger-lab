# Canonical supporting records: shared JSON storage

**Lab design pin, 2026-09-08.** Retained here at the user's request. Read the [design index](README.md) for status and ownership. This is readable design content, not a forwarding page.

Initial pin reconciled with [Core source at `b72312a`](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/docs/payroll/handbook/canonical-records.md). Acceptance and proposal labels below remain in force; the browser lab and production schema are unchanged.

**Pinned direction, 2026-09-08.** The user asked for a minimal Layer 1 that is
easy to understand and consume, proposed one reusable key/value table, emphasized
indexing, and reduced its columns to `tenant`, `key`, `value`, and `ts`. After
reviewing the component example and the proposed review of all 16 supporting
tables, the user said: “this looks good. can you pin it down. and pin down other
possible entries.”

During this pin, the user added: “we may need a column to enabled/disabled/deleted
etc”. The proposed `state` extension below records that refinement separately
from the agreed four-column baseline; its exact lifecycle is not yet settled.

This chapter records the agreed design direction and component example, then
lists candidate entries for individual review. It is not an implemented schema,
a completed migration design, or blanket approval of every candidate payload.
The [current table register](canonical-ledger-tables.md) remains the inventory
of existing storage. The nine canonical ledger table designations remain;
this proposal concerns consolidation of their 16 supporting tables.

**Lab design home:** the user subsequently requested that these concepts also
be pinned in the [payroll lab design collection](https://github.com/agentlabs-poc/agentlabs-payroll-ledger-lab/blob/docs/payroll-handbook-compat/docs/design/README.md).
That collection retains the architecture, canonical table mapping and JSON
examples as readable design documents. Core remains the canonical accepted
handbook location under the earlier migration decision; evolving design and
implementation acceptance must be reconciled explicitly across the two repos.

## Agreed direction and rationale

The main design work is identifying canonical terms and consistently applying
their meanings across the handbook, APIs, CLI, record keys and JSON fields.
An existing table, handler or workflow name does not establish a canonical
concept. Review every supporting responsibility; combine duplicates and put
information on the owning ledger when that is its natural home.

Target one supporting-record table **per domain**, with a reusable storage
shape. The four-column baseline is:

| Column | Contract |
|---|---|
| `tenant` | Tenant scope; treatment of existing platform-shared definitions remains to be specified. |
| `key` | Canonically defined record locator; type-key versus unique-record-key encoding remains to be finalized. |
| `value` | JSONB object conforming to the record type's versioned schema. |
| `ts` | Database-recorded creation timestamp; not business effective time, revision identity or commit ordering. |

### Domain-owned tables

**Pinned refinement, 2026-09-08:** the user proposed that “each domain can have
its own key value table”. Share the envelope and validation/indexing approach;
each domain owns its terms, schemas, permissions, lifecycle and indexes.

For payroll, the working table name is `payroll_records`; the physical name is
not yet a migration contract. Attendance or leave could use separate domain-owned
tables if justified. Their table names, records and implementation are not
prescribed here. This proposal does not introduce one application-wide store
into which all domains write, or a table per canonical key.

Domain and architecture layer are different dimensions. Separate domain tables
do not promote L2/L3 policy into L1, require new services or remove atomicity from
payroll commit. Client tooling can reuse the four/five-column envelope while
validating each domain's own software-owned contract. Core payroll money stays
in the canonical ledgers; this table consolidates supporting records.

### Proposed fifth column: `state`

Use a controlled shared availability state, provisionally `enabled`, `disabled`
or `deleted`. This is a proposed physical-column extension requested for
consideration, not a finalized enum or migration. It makes a frequently queried
cross-cutting property explicit while keeping domain payloads in JSON.

| Proposed state | Meaning and limits |
|---|---|
| `enabled` | Available for permitted new use, subject to domain applicability and other rules; does not mean approved or committed. |
| `disabled` | Unavailable for new use; identity and historical references remain. Reactivation requires the type's permitted transition. |
| `deleted` | Logical removal from normal use/listing; retained for history and existing references. Does not authorize physical deletion. |

Draft hold, review approval, instruction consumption and payroll commit remain
domain concepts; they are not values in this shared availability enum. Not every
record type must support every availability transition. Disabling or deleting
evidence must never reopen instruction consumption, remove commit/retry
protection, change posted money or hide required audit evidence. The relationship
to component DELETE must be settled explicitly rather than silently changing
that API's behavior.

Decide whether availability belongs to a definition revision or its stable
subject, and how changes are represented with immutable payload/history. Options
include a new immutable revision/tombstone or a protected availability update
with durable transition evidence. No unrestricted UPDATE or extra history table
is prescribed. A state transition and its required evidence must be atomic.

For versioned subjects, select the authoritative current revision before testing
availability: disabling revision 2 must not accidentally resurrect enabled
revision 1. Existing historical references must still resolve even if the current
subject is disabled/deleted. Current/effective-version selection therefore needs
an explicit contract before an enabled-only partial index is accepted.

Index `state` together with actual tenant/type/subject predicates when justified;
do not automatically add a standalone index on its few values. Ordinary-listing
filters and historical/integrity lookups have different visibility requirements.
The four-column examples below remain the baseline; adopting the extension adds
an outer `state` field with type-appropriate validation.

Do not add a physical column for every use case. Keep important query fields
near the outside of the JSON document and define targeted indexes for required
access. JSON nesting alone supplies neither an index nor an integrity guarantee.
Fewer columns/tables do not by themselves demonstrate lower CPU, disk or latency.

Reuse is a storage capability, not permission to put arbitrary business concepts
in L1. [123 Architecture](123-architecture.md) still governs ownership: software
owns canonical contracts, L2 owns reusable auxiliary composition, and L3 can
own task-specific or AI composition. L1 exposes authorized domain operations;
this decision does not introduce unrestricted key/value writes or bulk writes.

## Canonical contract for each entry

Every entry needs: meaning and layer; identity and owner; versioned JSON schema;
allowed operations and lifecycle; references and integrity rules; supported
queries and indexes; replay behavior; and valid/invalid examples.

Examples below use a proposed namespace, `payroll.*`. The term identifies the
type; a complete key such as `payroll.component/C101/1` also identifies one
record revision. `C101` is an illustrative identifier and `1` its revision.
No ID-generation algorithm is prescribed. Key grammar, escaping, maximum
length, and agreement between key and payload identity must be finalized before
implementation. A timestamp alone cannot distinguish concurrent revisions.

Retain immutable revisions where history is required. The record-type contract
defines the current revision and atomic stale-write protection; uniqueness of
a revision number alone does not establish valid succession. Do not reconstruct
all prior events merely to read current control state when a complete revision
can express it. Monetary draft content remains fixed independently of controls.

## First entry: component definition

**Component example accepted as the starting design.** A component identifies
what an earning or deduction represents. It does not establish an employee's
salary entitlement, amount, formula or organizational approval policy.

Proposed canonical term: `payroll.component`. Existing sources:
[`payroll_fields`](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000053_payroll_fields.up.sql) and
[`payroll_component_versions`](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/b72312a8203a37ab97669f760099516a2bba1d9d/migrations/000073_payroll_component_versions.up.sql).

```json
{
  "tenant": "T1",
  "key": "payroll.component/C101/1",
  "ts": "2026-09-08T10:00:00Z",
  "value": {
    "schema_version": 1,
    "component_id": "C101",
    "revision": 1,
    "code": "basic",
    "label": "Basic salary",
    "kind": "earning",
    "country_code": "IN"
  }
}
```

One definition revision is one row. Subsequent definition changes retain the
component identity and create a new revision; existing ledger references retain
their exact definition. Same-component revisions can reuse the code; distinct
components must not conflict within the agreed tenant/country/code scope.
An effective definition is not necessarily the numerically latest revision.

Still to settle: platform-shared visibility and write protection, country/code
identity rules, effective lifetime, complete kinds and reporting fields,
reference enforcement, and deletion semantics for unused versus referenced
definitions. Preserve the user's component DELETE requirement. Existing API
behavior remains unchanged; neither this example nor consolidation adopts its
current approval state machine or changes the employer-contribution ledger rule.

## Other possible entries

**Candidates recorded for review.** Each example below is only the `value`
object stored with the same four-column envelope. These are related examples
for E101's November 2026 draft D1: loan instruction version IV1 produces a
2,000 INR deduction. Symbols and hashes are illustrative, not valid production
IDs or complete request schemas. Key spellings and full field contracts remain
proposals; shared storage does not create new public API resources.

### `payroll.draft.control`

Complete control state for one exact draft revision, preserving prior control
revisions. The selected policy belongs above L1; L1 enforces authorized controls.
It does not mandate approval or current-source reconciliation for every draft.

```json
{
  "schema_version": 1,
  "draft_id": "D1",
  "revision": 2,
  "employee_id": "E101",
  "payroll_month": "2026-11",
  "actor": "U7",
  "held": false,
  "cancelled": false,
  "reason": "Loan deduction checked; hold released"
}
```

Revision 1 may have `held: true`. Requirements binding, effective review
invalidation and replay evidence must be specified before replacing controls
and their event history. `draft_id` must bind exact immutable draft content;
existing mutable calculation IDs alone are insufficient.

### `payroll.draft.review`

A review decision about exact draft content, when required by selected policy.

```json
{
  "schema_version": 1,
  "draft_id": "D1",
  "draft_content_hash": "illustrative-content-hash",
  "control_revision": 2,
  "actor": "U9",
  "decision": "approved"
}
```

Review identity, permitted decisions and validity after control changes remain
to be specified. Do not infer that every control change invalidates approval or
that a prior review applies to changed draft content.

### `payroll.instruction.resolution`

Proposed treatment of a supplied instruction in an exact draft. This does not
consume the instruction or require tracing its upstream business origin.

```json
{
  "schema_version": 1,
  "draft_id": "D1",
  "instruction_version_id": "IV1",
  "disposition": "applied",
  "effects": [
    {"draft_entry_id": "DE2", "amount": "2000.00", "currency": "INR"}
  ]
}
```

Specify replacement, removal and exclusion against canonical instruction
semantics before copying current enum values. An exclusion needs a reason and
does not imply consumption. Effect amounts here are magnitudes; the referenced
entry establishes earning/deduction direction. Resolve whether these details
belong in a supporting record or directly on the immutable draft.

### `payroll.instruction.application`

Permanent evidence of an instruction's committed application and its monetary
effects. It is recorded atomically with the employee's posted payroll.

```json
{
  "schema_version": 1,
  "instruction_version_id": "IV1",
  "employee_id": "E101",
  "payroll_month": "2026-11",
  "draft_id": "D1",
  "cadence": "monthly",
  "effects": [
    {"ledger_entry_id": "PE2", "amount": "2000.00", "currency": "INR"}
  ]
}
```

Monthly instructions have one ordinary application per applicable month until
expiry; one-time instructions are consumed at commit. A changed version ID must
not accidentally bypass the agreed instruction identity/consumption scope.
Corrections preserve the original application and monetary history. Exact
consumption indexes and correction-effect representation remain to be designed.
JSON effect arrays do not by themselves enforce foreign keys or prevent
duplicate links. Verify reference enforcement and reverse-lookup queries before
accepting consolidation of the separate effect table.

### `payroll.operation.receipt`

Durable evidence of one authorized domain operation, its retry identity and
outcome. Consolidate duplicate evidence where it describes that same operation.

```json
{
  "schema_version": 1,
  "operation": "payroll.commit",
  "subject_id": "D1",
  "executor": "U7",
  "idempotency_key": "commit-e101-nov26",
  "request_hash": "illustrative-request-hash",
  "outcome": {
    "status": "committed",
    "posted_entry_ids": ["PE1", "PE2"]
  }
}
```

Specify initiator/delegation evidence where applicable, operation scope, changed
request rejection, before/after evidence and exact HTTP replay requirements.
HTTP requests and internal domain operations can have different retry scopes;
sharing their format does not make those scopes interchangeable. Whether they
can share one receipt instance requires an operation-by-operation mapping.
Commit outcome durability must not depend on a disposable HTTP-cache lifetime.
No cross-employee batch resource follows from this receipt type.

## All 16 existing supporting tables: review map

Every row is a proposed consolidation disposition, not a migration instruction.

| # | Existing table | Candidate home or elimination of duplication |
|---|---|---|
| 1 | `payroll_fields` | `payroll.component`: stable component identity within versioned definitions. |
| 2 | `payroll_component_versions` | `payroll.component`: immutable definition revisions. |
| 3 | `payroll_calculation_candidates` | Evaluate exact identity/hashes on the canonical draft revision; do not invent another canonical candidate resource. |
| 4 | `payroll_draft_controls` | `payroll.draft.control`: current complete control revision. |
| 5 | `payroll_draft_control_events` | Prior control revisions plus operation evidence; preserve reasons and retry results. |
| 6 | `payroll_employee_candidate_reviews` | `payroll.draft.review`: exact-content review evidence. |
| 7 | `payroll_employee_finalization_receipts` | `payroll.operation.receipt`: permanent individual commit outcome. |
| 8 | `payroll_instruction_applications` | `payroll.instruction.application`: committed consumption/application. |
| 9 | `payroll_instruction_application_effects` | Application effects with enforced posted-entry relationships; representation open. |
| 10 | `payroll_candidate_instruction_resolutions` | `payroll.instruction.resolution` or owned draft content; decide once. |
| 11 | `payroll_candidate_instruction_resolution_links` | Resolution effects with enforced draft-entry relationships. |
| 12 | `payroll_entry_batches` | `payroll.operation.receipt`: one-calculation entry-operation evidence. Deprecated relief uses remain deprecated. |
| 13 | `payroll_candidate_batches` | `payroll.operation.receipt`: request/result and content-change evidence, preserving operation scope. |
| 14 | `payroll_source_authority_actions` | `payroll.operation.receipt`: instruction-operation evidence; deprecated generic fact uses remain deprecated. |
| 15 | `payroll_http_idempotency` | `payroll.operation.receipt`: HTTP replay information where compatible; preserve distinct scopes where needed. |
| 16 | `payroll_mutation_evidence` | `payroll.operation.receipt`: actor/action/before-after evidence where the same operation owns it. |

## Indexes and enforcement are part of the contract

Start with direct tenant/key lookup and a uniqueness rule for record identity,
subject to final key grammar and shared-tenant semantics. Use targeted expression
indexes on JSON fields for agreed queries; use partial indexes where justified
by record type and matching query predicates. Do not add a blanket whole-payload
GIN index or an index per hypothetical filter. Index order follows the actual
tenant, subject, employee/month and ordering predicates.

For each candidate, specify exact-record lookup, history/current or effective
revision lookup where applicable, required reverse-reference queries and
uniqueness guarantees. In particular: component identity across revisions,
stale control updates, review/content binding, instruction consumption and
operation retry identity need explicit database/transaction enforcement.
Required fields cannot silently be missing/null and evade unique constraints.
Cross-record reference checks must be safe against concurrent changes, not
merely client-side existence checks. JSON storage does not provide these rules
automatically.

Client scripts may prepare payloads, validate shared schemas, calculate proposals
and coordinate employees. Repository/CI scripts may detect vocabulary and schema
drift. Reusable software-owned scripts are L2; task-specific composition can be
L3. Server/database enforcement still protects tenant isolation, authorization,
valid records, references, uniqueness and atomic commits against stale or
bypassed clients. Canonical schemas, examples and validation utilities should be
version controlled; no scripts or schema package are implemented by this pin.

Technical basis: PostgreSQL supports [JSONB indexing](https://www.postgresql.org/docs/current/datatype-json.html),
[expression indexes](https://www.postgresql.org/docs/current/indexes-expressional.html)
and [partial indexes](https://www.postgresql.org/docs/current/indexes-partial.html).
These capabilities make the target feasible; they do not prove this particular
design meets current performance or compatibility requirements.

## Next review and implementation boundary

Review component identity/definition first, then each remaining mapped table,
settling only material contract decisions. Record accepted contracts separately
from candidate examples. Before any migration, reconcile existing data and
dependencies, define constraints/indexes and prove atomicity, concurrent retries,
reference integrity, and required query plans on representative data. Measure
index size and read/write cost rather than promising a gain from table count.

This chapter pins design and rationale only. Existing component and instruction
APIs, the CLI, migrations and data are unchanged. Run/compensation deprecations
remain. It does not fill the Salary Earning Ledger representation gap, approve
new APIs, establish overall merge readiness or authorize merging pending PRs.

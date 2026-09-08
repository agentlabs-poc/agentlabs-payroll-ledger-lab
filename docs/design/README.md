# Payroll design pins

**User-directed design home, 2026-09-08.** The user asked that the canonical
tables and new payroll key/value model be pinned in the lab repo, and proposed
key/value storage per domain and, subsequently, per layer (L1/L2/L3), with
domain-specific or shared API wrappers. These documents retain the concepts, examples,
indexing rationale and outstanding contract decisions here in readable form.

| Design pin | Contents and status |
|---|---|
| [123 Architecture](123-architecture.md) | Agreed L1 core primitives, L2 software-owned auxiliary primitives and L3 application/AI composition; canonical vocabulary before API contracts. |
| [Canonical ledger tables](canonical-ledger-tables.md) | Nine user-designated L1 ledger tables, the 16 existing supporting tables, candidate L2 output and deprecated structures. Existing storage inventory, not the replacement schema. |
| [Payroll records by domain and layer](payroll-records.md) | L1/L2/L3 key/value tables and wrappers, four-column baseline, proposed fifth `state` column, six original entry examples, an L2 employee-settings candidate and all 16 L1 consolidation mappings. |

## Domain ownership and minimal storage

**Pinned 123 Architecture storage rule:** core canonical tables plus one
canonical key/value table per domain/layer. The complete rule, including keys,
indexes, state, wrappers and client/server responsibilities, is in
[123 Architecture](123-architecture.md#canonical-storage-model).

Each domain can own a table for each layer's data while sharing a minimal shape:

```text
Payroll domain
  Canonical monetary/source ledgers
  payroll_l1_records               Core supporting records
  payroll_l2_records               Reusable software-owned auxiliary data
  payroll_l3_records               Application/AI composition data
    Each: tenant | key | value(JSONB) | ts
          state                    (proposed fifth column)

Other domains, when justified
  Their own domain records and tables for the owning layers
    Same reusable envelope; their own canonical contracts and indexes
```

These are working table names. This is one table per domain and owning layer,
not one per record type. Payroll
component definitions, controls, reviews, instruction effects and receipts may
share the L1 store when their reviewed role belongs to L1; the six candidate
terms are not six new tables. The
canonical ledgers continue to own money, instructions and committed history.
Other domain table names or implementations are not approved by this example.

The shared envelope does not decide layer ownership. L1 keeps domain integrity
and atomic one-employee commits; L2/L3 perform reusable or task-specific
composition. Client-side scripts can validate canonical schemas and prepare
records. Authoritative permissions, references, concurrency, uniqueness and
commit guarantees remain enforced at the server/database boundary.

Domain APIs can express canonical operations; shared key/value wrappers can
provide scoped record access and permitted mutation. L1 writes still execute
complete domain operations. L2/L3 generic writes are limited to their authorized
namespaces and contracts, and cannot write L1 by selecting its table. Exact APIs,
deployment placement and DDL remain to be reviewed; no new endpoint is implemented.

## Meaning before storage

For every canonical term, settle meaning, identity, JSON fields, lifecycle,
operations, queries and indexes together. A type key and a unique record key
serve different purposes; exact encoding remains open. `ts` is creation evidence,
not a revision number. Important JSON query fields can use targeted expression
indexes without becoming physical columns.

The user specifically required canonical key construction for indexing. Each
type therefore needs one shared encoder/validator and an explicit subject/record
identity contract. The proposed `<canonical-type>/<subject-id>/<record-id>`
shape is documented with its query/index rules in the record chapter; exact
grammar remains under review. Numeric revisions sort numerically, and disabling
or logically deleting a record must not free its identity for conflicting reuse.

The proposed shared `state` describes availability: enabled, disabled or
logically deleted. It does not replace domain hold, approval or commit states.
Historical references and consumption/retry guarantees must survive state changes.
The entry contract must prevent an older enabled revision becoming current merely
because a newer revision was disabled. Full transition and indexing rules remain
to be reviewed before implementation.

## Documentation ownership and status

The lab is the home for this evolving design discussion and its pins. Core
remains the canonical accepted payroll handbook location under the earlier
user-directed migration. The existing forwarded handbook chapters remain intact;
these new design documents restore local design content without undoing that
migration. Future refinements should be discussed and pinned here, then reconciled
with Core before being treated as accepted implementation requirements.

Each design document records the exact Core source used for this initial pin.
That source binding is provenance, not a claim that future edits synchronize
automatically. Preserve the distinction between agreed principles, candidate
payloads and implemented behavior in both repositories. Full schemas, index DDL,
migrations, validation scripts and performance proof are not implemented here.

Existing PRs carry the work: [Lab #1](https://github.com/agentlabs-poc/agentlabs-payroll-ledger-lab/pull/1)
and [Core #190](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/190), whose
merge destination is [Core hub #172](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/172).
No PR per term or table is needed. These pins do not authorize a PR merge or
database/runtime change.

# Payroll design pins

The umbrella model is **123 Architecture — a new software-design paradigm for
AI-native applications**. SQLite is the first proving ground for its concrete
payroll contracts, before production implementation.

**User-directed design home, 2026-09-08.** The user asked that the canonical
tables and new payroll key/value model be pinned in the lab repo, and proposed
key/value storage per domain and, subsequently, per layer (L1/L2/L3), with
domain-specific or shared API wrappers. These documents retain the concepts, examples,
indexing rationale and outstanding contract decisions here in readable form.

| Design pin | Contents and status |
|---|---|
| [SQLite-first proof plan](sqlite-proof-plan.md) | Finite checkpoints for the SQLite lab proof, with production PostgreSQL acceptance kept separate. |
| [123 Architecture](123-architecture.md) | Agreed L1 core primitives, L2 software-owned auxiliary primitives and L3 application/AI composition; canonical vocabulary before API contracts. |
| [Canonical ledger tables](canonical-ledger-tables.md) | Current three-ledger target, with the former nine-table designation, 16 supporting roles and deprecated structures retained as historical inventory. |
| [Payroll records by domain and layer](payroll-records.md) | Supplied L1/L2 key/value tables and wrappers, consumer-owned L3, four-column baseline, proposed fifth `state` column, nine L1 record types, L2 employee settings and all 16 supporting-role mappings. |

## Domain ownership and minimal storage

**Pinned 123 Architecture storage rule:** core canonical tables plus one
canonical key/value table per domain/layer. The complete rule, including keys,
indexes, state, wrappers and client/server responsibilities, is in
[123 Architecture](123-architecture.md#canonical-storage-model).

**Latest ownership correction:** the supplied software provides L1 and L2.
Consumers own L3 composition and persistence; we do not supply an L3 table or API.

Each domain can own a table for each software-owned layer's data:

```text
Payroll domain
  payroll_draft_ledger             Fixed draft monetary entries
  payroll_ledger                   Committed payroll entries
  payroll_employer_liability_ledger  Obligations, remittances, allocations
  payroll_l1_records               Core supporting records
  payroll_l2_records               Reusable software-owned auxiliary data
    Record stores: tenant | key | value(JSONB) | ts
          state                    (proposed fifth column)

Other domains, when justified
  Their own domain records and tables for software-owned L1/L2
    Same reusable envelope; their own canonical contracts and indexes

Consumers (L3)
  Own their application/AI composition and choose their own persistence
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
complete domain operations. L2 generic writes are limited to authorized
namespaces and contracts; L3 consumers use these L1/L2 APIs. Exact APIs,
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
grammar is pinned: dot-delimited type tokens, colon-delimited identity segments,
and backslash escaping of literal colon/backslash inside identities. Numeric revisions sort numerically, and disabling
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
payloads and implemented behavior in both repositories. Detailed production schemas, migrations and performance proof remain open.
The isolated SQLite prototype exercises explicitly stated assumptions; it does
not establish production conformance.

The [SQLite folding implementation plan](sqlite-fold-implementation-plan.md)
tracks the lab-only implementation and its scoped review. Design pins and executable
proof status are kept separate; production compatibility remains unproved.

Existing PRs carry the work: [Lab #1](https://github.com/agentlabs-poc/agentlabs-payroll-ledger-lab/pull/1)
and [Core #190](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/190), whose
merge destination is [Core hub #172](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/172).
No PR per term or table is needed. These pins do not authorize a PR merge or
database/runtime change.

The [canonical tables and record types](payroll-records.md#canonical-tables-and-canonical-record-types)
are listed separately, with layer, meaning, example keys and acceptance status.

The [historical nine-table proof](../evidence/sqlite-record-fold/README.md) records
33 passing tests at its source revision. The three-ledger simulation has its own
row catalogue and verification; the earlier result does not prove this new layout.

**Current target:** [three canonical ledgers and complete simulation row map](three-ledger-simulation.md).
This supersedes the earlier nine-table target.

Read the [canonical row mind map](canonical-row-map.md) for the complete type/relationship catalogue.

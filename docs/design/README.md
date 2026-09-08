# Payroll design pins

**User-directed design home, 2026-09-08.** The user asked that the canonical
tables and new payroll key/value model be pinned in the lab repo, and proposed
one key/value table per domain. These documents retain the concepts, examples,
indexing rationale and outstanding contract decisions here in readable form.

| Design pin | Contents and status |
|---|---|
| [123 Architecture](123-architecture.md) | Agreed L1 core primitives, L2 software-owned auxiliary primitives and L3 application/AI composition; canonical vocabulary before API contracts. |
| [Canonical ledger tables](canonical-ledger-tables.md) | Nine user-designated L1 ledger tables, the 16 existing supporting tables, candidate L2 output and deprecated structures. Existing storage inventory, not the replacement schema. |
| [Payroll supporting records](payroll-records.md) | Domain-owned key/value table, four-column baseline, proposed fifth `state` column, component example, five further candidate entry types and all 16 consolidation mappings. |

## Domain ownership and minimal storage

Each domain can own a supporting-record table while sharing a minimal shape:

```text
Payroll domain
  Canonical monetary/source ledgers
  payroll_records                  (working table name)
    tenant | key | value(JSONB) | ts
    state                          (proposed fifth column)

Other domains, when justified
  Their own domain records and supporting-record table
    Same reusable envelope; their own canonical contracts and indexes
```

This is one supporting table per domain, not one per record type. Payroll
component definitions, controls, reviews, instruction effects and receipts may
share `payroll_records`; the six candidate terms are not six new tables. The
canonical ledgers continue to own money, instructions and committed history.
Other domain table names or implementations are not approved by this example.

The shared envelope does not decide layer ownership. L1 keeps domain integrity
and atomic one-employee commits; L2/L3 perform reusable or task-specific
composition. Client-side scripts can validate canonical schemas and prepare
records. Authoritative permissions, references, concurrency, uniqueness and
commit guarantees remain enforced at the server/database boundary.

## Meaning before storage

For every canonical term, settle meaning, identity, JSON fields, lifecycle,
operations, queries and indexes together. A type key and a unique record key
serve different purposes; exact encoding remains open. `ts` is creation evidence,
not a revision number. Important JSON query fields can use targeted expression
indexes without becoming physical columns.

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

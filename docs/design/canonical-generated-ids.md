# Canonical generated IDs: Snowflake Base36

Accepted on 2026-09-09. Generated opaque entity and ledger-entry IDs use a
readable canonical type prefix followed by `_` and a classic Snowflake integer
encoded in lowercase Base36 (`0-9a-z`).

## Representation and meaning

- Format: `<type-prefix>_<snowflake-base36>`.
- The numeric suffix is a positive 63-bit Snowflake value, encoded without leading zeros: 1–13 characters. The prefix adds to the total length.
- JSON and canonical keys carry the complete prefixed string, never a JavaScript Number.
- The decoded value must fit the positive signed 64-bit range; matching the alphabet alone is insufficient validation.
- Entity identity remains stable across revisions. Revision numbers remain decimal counters.
- Tenant, employee ownership and record type remain explicit in the canonical key.
- Registered semantic codes such as BASIC and HRA remain readable codes.
- An externally supplied employee identity is retained; this decision does not rename existing employees.

Example: decimal `1234567890123456789` encodes exactly as `9do1sj396nf9`.

```text
payroll.component:BASIC:1
payroll.earning:E101:earning_9do1sj396nf9:1
payroll.earning:E101:earning_9do1sj396nf9:2
```

The last two keys identify revisions of the same employee earning. A new entity
gets a new ID; a retry reuses its existing identity. The Snowflake timestamp is
creation metadata, not payroll month, effective date or commit order.

## Canonical type prefixes

| Identity | Prefix |
|---|---|
| Generated employee ID | `employee_` |
| Earning ID | `earning_` |
| Instruction ID | `instruction_` |
| Draft ID | `draft_` |
| Draft ledger entry ID | `draftentry_` |
| Committed payroll entry ID | `payrollentry_` |
| Employer-liability ledger entry ID | `liabilityentry_` |
| Review ID | `review_` |
| Instruction resolution ID | `resolution_` |
| Instruction application ID | `application_` |
| Operation receipt ID | `receipt_` |

The prefix describes entity type, not mutable status, employee, month or tax
regime. All employer-liability entry kinds share `liabilityentry_`; their kind
remains explicit in the ledger row. Draft control and employee settings use the
owning identity plus revision and need no additional generated ID. Prefixes must
match the expected identity type; consumers must not invent aliases. Other ID
families require a canonical definition before adding prefixes.

The full key still includes record namespace and employee ownership. The prefix
also makes a standalone reference intelligible; it does not replace either scope.

## Generator requirements

Use the classic 41-bit millisecond timestamp, 10-bit worker identity and 12-bit
sequence layout. Before implementing the generator, pin one immutable epoch and
a worker-assignment policy. Concurrent generators must not share worker identity;
restarts and backward clock movement must not permit timestamp/sequence reuse.
Sequence exhaustion waits for a later millisecond. Retain database uniqueness
constraints; conflicting IDs must never overwrite existing records.

Base36 is an encoding, not additional randomness. Numeric time ordering does not
imply lexicographic ordering across different string lengths. Index identity for
lookup and use explicit timestamps for chronological queries.

## Rationale and implementation status

Chosen for compact lowercase identifiers and time-based generation. Coordination
and clock handling are required; independently started client generators cannot
assume uniqueness without worker assignment.

This pins the accepted format. Current SQLite demo fixtures still use readable
local IDs and existing derived entry IDs. Generator wiring and fixture conversion
are separate implementation work; no production schema or API is changed here.

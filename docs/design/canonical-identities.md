# Canonical identity before key syntax

## Agreed rule

The user requires every employee-owned record to include the employee identity
in its key. The complete key must identify one record uniquely within its tenant.
This is a domain identity requirement, not an optional naming convention.

Define the record's meaning, owner, identity and versioning before deciding how
to encode its key. Key identity and JSON identity must agree. Shared component
definitions belong to the tenant; an employee's amount belongs to an
employee-owned earning record that references a component definition.

The earlier SQLite/browser keys such as `payroll.earning:EARN-BASIC:1` violate
this ownership rule. The user explicitly requested correction of the employee
earning example. The scoped correction below retains the existing earning ID
and revision and adds employee identity through the authoritative key contract.
Other employee-owned record families still require reconciliation.

## Generic segment columns — agreed storage direction

The user clarified and approved a shared envelope with generic columns:

```text
tenant | key1 | key2 | ... | key10 | value JSON | ts | state
```

Canonical JSON remains unchanged by this storage refinement. Its serialized
`key` is decoded into `key1` through `key10` for storage and indexing. These
columns are a projection of the canonical key, not another independently writable
identity. The payload and canonical meanings do not change. The earlier
employee-ownership correction remains a separate, unresolved identity task.

Each column holds one decoded canonical segment. The columns are not named
`employee_id`, `component_id` or other payroll-specific meanings. The owning
canonical record contract defines the ordered segments and their meanings.

The user's exact example is:

| Serialized canonical locator | key1 | key2 | key3 |
|---|---|---|---|
| `payroll.component:BASIC` | `payroll` | `component` | `BASIC` |

This example demonstrates segmentation, not a decision to remove immutable
revision identity. A versioned component row still needs its revision in the
complete identity; its proposed extension is `key4 = "1"` for revision 1.
Every employee-owned record must similarly carry employee identity in an assigned
key slot. The earning-cardinality question below remains open; it does not block employee ownership in keys.

### Meaning, flexibility and serialization

New canonical record types can reuse these columns and define different JSON
payloads without adding a table or domain-specific columns. There are at most ten
segments. An existing type must keep one defined positional mapping; arbitrary
per-row meanings would make queries and references ambiguous.

The canonical definition, rather than column names, specifies namespace tokens,
identity fields, separators, revision semantics and payload agreement. The complete
ordered tuple, together with tenant and owning store, identifies the record.
Neither timestamp nor availability changes that identity. Software validates
canonical meaning; the authoritative storage boundary must still enforce tenant
scope, uniqueness, references and permitted writes.

Do not split blindly on every dot or colon. Parse namespace dots and identity
separators using the registered grammar, respecting escaped characters. The
existing grammar treats dots inside opaque IDs as literal and escapes literal
colon/backslash. A type contract must preserve that distinction when decoding
columns and reconstructing the serialized locator. If a different escaping rule
is adopted, it needs an explicit compatibility decision and round-trip proof.
Different registered types must never yield the same complete tuple.

### Indexes and fetching

An index beginning with `(tenant, key1, key2, key3)` can support tenant/domain/type/
component prefix queries in the example. It groups related keys within the index;
this is not physical table partitioning. Columns alone do not provide this benefit.
Exact full-key lookup may already be equally fast with the previous indexed string.
Indexed JSON expressions can also provide equivalent lookup performance.

Choose additional indexes from actual query patterns. An employee in a later slot
may require a different index when earlier slots are not constrained. Do not add
all possible combinations or promise faster overall payroll execution without a
comparison. Reference: [PostgreSQL multicolumn indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html)
and [expression indexes](https://www.postgresql.org/docs/current/indexes-expressional.html).

### Implementation details still to prove in SQLite

The following are proposed mechanics, not additional agreed business rules:

- Use decoded text segments, with one consistent unused trailing-slot convention.
  A candidate is non-null empty trailing slots, with empty used segments and gaps
  rejected. Nullable slots need explicit uniqueness treatment; ordinary composite
  uniqueness must not allow duplicate identities through null slots.
- Preserve case and distinguish the complete tuple from shorter lookup prefixes.
- Define numeric revision ordering explicitly; text ordering alone puts 10 before 2.
- Derive segment columns from the canonical JSON key using its registered
  contract. Validate key/column agreement and lossless reconstruction; do not
  expose two independently writable identities. Keeping canonical JSON unchanged
  does not require duplicating the serialized key in another physical column.
- Prove escape round trips, duplicate rejection, employee ownership, reference
  preservation, revision/state behavior and indexed query plans before timing.
- Compare equivalent indexed-string and segment-column queries on the same data.
  Report lookup and write costs, index space and total operation time separately.

Next checkpoints: settle each record's complete identity; pin its slot mapping and
queries; implement and verify the isolated SQLite fold; regenerate the row map,
HTML snapshots and diagrams together. No production schema or API change follows
from this pin. The current simulation remains evidence for the earlier layout.

## Employee earning identity

**Correction target; implementation paused for the whole-flow fidelity study.**

Meaning: an employee's entitlement to an amount for one payroll
component, valid over an effective period.

| Property | Meaning |
|---|---|
| Owner | Tenant and employee |
| Component | Exact version of a component meaning, such as Basic or HRA |
| Value | Amount, currency and effective dates |
| History | Changes create immutable versions |

The employee is required regardless of how many earning streams a component may
have. Preserve the existing earning ID and immutable revision; do not introduce
a new employee/component uniqueness policy merely to correct ownership.

```text
payroll.earning:<employee-id>:<earning-id>:<revision>
payroll.earning:E101:EARN-BASIC:1
```

| Column | Meaning | Example |
|---|---|---|
| key1 | Domain namespace | payroll |
| key2 | Canonical record type token | earning |
| key3 | Owning employee | E101 |
| key4 | Existing earning identity within that employee | EARN-BASIC |
| key5 | Immutable revision | 1 |
| key6–key10 | Unused | Representation remains a storage decision |

Within a tenant, two employees may use the same earning ID and revision without
colliding. Key employee, earning ID and revision must agree with the JSON value.
History/current selection must include employee scope. A draft must reject an
earning owned by another employee, and all exact source references must retain
the complete employee-qualified key.

The separate question of whether a consuming organization allows multiple earnings
for one employee/component does not justify omitting employee ownership. This
correction retains existing earning IDs and does not add such a restriction or
claim it has been agreed. The JSON value's fields and payroll amounts are unchanged;
the corrected key propagates through actual source references and regenerated
SQLite snapshots, rather than only changing a browser label.

The Basic ₹30,000 and HRA ₹20,000 example demonstrates component definitions and
employee amounts; it does not resolve earning-stream identity or establish an
organizational compensation policy.

## Subsequent reconciliation

Apply the same definition-first method next to
instructions, draft metadata, controls, reviews, resolutions, applications,
operation receipts and employee settings. Record which are employee-owned and
which are shared; employee ownership must be explicit rather than inferred from
an arbitrary ID. Resolve references and query/index dimensions from those
identities, then update the simulation, JSON, examples and diagrams together.

The three canonical ledger tables and the separation of shared components from
employee earnings remain unchanged by this discussion. Existing proof results
describe the earlier key contract; they do not establish compliance with this
new ownership requirement.

## Shared definition source

The [canonical definition register](canonical-definitions.json) is the shared
meaning/ownership source displayed by the HTML timeline. It distinguishes the
five storage tables from the ten record types and explicitly marks the unresolved
earning-cardinality question separately from the required employee identity.
Editing a display label is not a substitute for correcting actual stored keys
and their references.

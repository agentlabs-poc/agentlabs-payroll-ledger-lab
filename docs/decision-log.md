# HRMS Payroll Handbook — decision log

New design discussion is pinned locally in [Payroll design pins](design/README.md):
123 Architecture, canonical ledger tables, domain-owned key/value storage and
candidate entries. This preserves the user's subsequent lab-design direction;
the migrated handbook decision history below still belongs to Core.

The subsequent pinned [123 Architecture storage rule](design/123-architecture.md#canonical-storage-model)
is core canonical tables plus one canonical key/value table per domain/layer.
It includes L1/L2/L3 storage ownership, canonical keys/indexes, the proposed
availability column, domain/general wrappers and client/server enforcement.

The [software-design premise](design/123-architecture.md#software-design-premise)
and employee payroll preferences/policy assignment as an L2 use case are also
pinned. Exact employee-settings fields remain proposed. This records a coherent
design direction, not a claim of implemented behavior or proven novelty.

The user subsequently directed SQLite-first proof before touching production
code. The [proof plan](design/sqlite-proof-plan.md) records canonical storage,
keys, state, wrappers, payroll commit/ELR, failure/retry and query-plan checkpoints.
It distinguishes lab behavior from later PostgreSQL-specific acceptance. The
plan is pinned; no prototype or completed proof is claimed.

The user requested the framing **123: a new software-design paradigm for AI-native
applications**, now pinned in the architecture chapter. The established name
123 Architecture remains, with 123 Software Design Paradigm as an alternative
description of the proposed synthesis. The SQLite proof has not yet been executed.

**Latest direction:** continue folding the 16 supporting roles into
`payroll_l1_records`, using L2 only for auxiliary data. Software does not provide
L3; consumers own its composition and persistence. This supersedes the earlier
proposal for a software-provided L3 key/value table/API. The lab's SQLite
implementation plan proceeds on that corrected basis; production code is untouched.

This chapter has moved to HRMS Core, the canonical payroll documentation source.

[Read the canonical chapter](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/decision-log.md). The original edition and its rationale are preserved in Git history and Core’s [migration record](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/migration-record.md).

Existing section links are forwarded below.

<a id="hrms-payroll-handbook--decision-log"></a>
- [HRMS Payroll Handbook — decision log](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/decision-log.md#hrms-payroll-handbook--decision-log)

<a id="discussion-questions"></a>
- [Discussion questions](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/decision-log.md#discussion-questions)

<a id="domain-decisions"></a>
- [Domain decisions](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/decision-log.md#domain-decisions)

<a id="proposal-dispositions"></a>
- [Proposal dispositions](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/decision-log.md#proposal-dispositions)

<a id="alternatives-and-history"></a>
- [Alternatives and history](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/decision-log.md#alternatives-and-history)

## 2026-09-08 — Canonical storage vocabulary and key grammar pinned

The user approved dot-separated canonical type tokens, colon-separated identity
segments, and backslash escaping of literal colon/backslash inside identities.
This supersedes the provisional slash examples. Shared encoding/parsing must
preserve opaque case and reject ambiguous spellings; numeric revisions sort
numerically. Key syntax does not prescribe an ID-generation algorithm.

The user also requested an explicit distinction between canonical tables and
canonical record types. The record chapter now calls out the nine designated L1
ledger tables, target L1/L2 shared stores, six L1 supporting record types and L2
employee settings. Detailed candidate contracts remain proposals. L3 storage
belongs to consumers. Rationale: a minimal vocabulary must distinguish storage
structure, domain meaning and individual identity without creating a table for
every supporting concept. Production code and schemas are unchanged.

## 2026-09-08 — Exactly three canonical ledgers

The user named `payroll_draft_ledger`, `payroll_ledger` and
`payroll_employer_liability_ledger` as the complete canonical-ledger set and asked
for extreme simplicity. This supersedes the nine-table target. Instructions,
earnings and draft metadata can be canonical L1 records; obligation/remittance/
allocation remain distinct monetary entry types within the employer ledger.

Rationale: physical implementation tables should not inflate the consumer's
canonical ledger vocabulary. Preserve exact references, indexes, immutable
history and employee-atomic operations while reducing table count. The user then
requested commit/push and a return to simulation with all canonical row examples
and a complete mind map. The [design](design/three-ledger-simulation.md) defines this SQLite-only step.
No production runtime/API/CLI/migration changes are authorized here.

## 2026-09-08 — Canonical browser alignment and component meaning

The user requested that the HTML demo reflect the three canonical ledgers and
L1 records, and explicitly accepted JSON. The page now displays captured rows
from actual SQLite operations. Rationale: a second browser payroll engine can
drift from the executable model; a snapshot viewer keeps the examples inspectable
without introducing another write API or business-rule implementation.

The user then corrected the broad `SALARY` example: components should represent
meanings such as Basic and HRA. Each has its own component definition; an employee
earning supplies the employee, amount and effective dates and references one exact
component version. A salary total does not become an additional component or
ledger. This distinction is reflected in the current JSON, diagrams and row maps.

The illustrative E101 fixture uses Basic ₹30,000 plus HRA ₹20,000. This split is
example data, not an agreed organizational compensation policy. Employer
contribution ₹3,000 and loan ₹2,000 preserve gross ₹53,000, deductions ₹5,000 and
net ₹48,000. The three earning sources produce five draft/posted monetary lines
because employer contribution has matching gross and deduction effects.

The correction changes examples and their explanation, not the set of canonical
tables or the opaque ID contract. Historical evidence and isolated tests may use
other legal component IDs; they are not the current human-facing scenario.

## 2026-09-08 — Employee ownership is part of canonical key identity

The user rejected employee earning keys without an employee identity. Every
employee-owned record must include that owner in its key; the complete key must
uniquely identify the record within its tenant. The user explicitly required
canonical definitions before implementation, so no employee-key/schema rewrite
has started. The prior fixed key grammar must be reconciled, not patched ad hoc.

The open earning-identity question is whether one employee/component pair has one
earning stream with successive versions or may have multiple independent earnings.
That determines whether an independent earning ID is needed. The shared definition
register records meanings and owners while leaving this decision open.

The user also requested a chronological HTML view that puts L1 records and ledger
entries together at their creation step, and displays the canonical definitions.
This presentation work uses the existing snapshots, with an explicit notice that
their employee-owned key layout is not the final contract.

## 2026-09-08 — Generic columns hold canonical key segments

The user clarified that `payroll.component:BASIC` must map to `key1 = payroll`,
`key2 = component`, `key3 = BASIC`, with generic slots up to `key10`. The user
approved pinning this direction and proceeding. This replaces the proposed
employee/type-specific column interpretation and the single physical key target.
Canonical meanings and ordered identity definitions remain in the record contract;
JSON values remain flexible. Employee identity is still part of employee-owned
keys, and immutable revision identity is not removed by the short component example.

Rationale: one reusable envelope can support many canonical record types while
exposing queryable key segments. Matching indexes can narrow prefix lookups and
group related keys; this is not physical partitioning. No runtime speedup has been
measured. The [identity contract](design/canonical-identities.md) records pending slot mappings, unused-slot
uniqueness, escaping, revision ordering and SQLite proof steps. These storage
mechanics do not resolve the outstanding earning-stream identity decision.
Production schemas, APIs and CLI remain unchanged.

The user then explicitly clarified: keep canonical JSON unchanged and document
that the key is decoded into columns. The columns are a storage/index projection
of that key, not a new payload format or independently writable identity. This
refinement does not itself settle the earlier employee-owned key correction.

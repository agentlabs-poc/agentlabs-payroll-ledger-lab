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

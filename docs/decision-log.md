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

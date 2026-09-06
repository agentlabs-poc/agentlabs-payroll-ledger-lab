# Payroll handbook compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Coding agents must use `gpt-5.6-sol`, reasoning effort `medium`, as requested by the user.

**Goal:** Make Core implement the agreed ledger contracts and support the two organizational freshness policies with verified public operations.

**Architecture:** Reuse reviewed Core primitives and the useful local fixes. Add explicit draft controls and producer intent, preserve exact posting, and assemble reports from committed records. Keep organizational choices separate from generic monetary integrity.

**Tech Stack:** Existing HRMS Core Go services, PostgreSQL protected gateways and migrations, Cobra CLI, and repository acceptance tooling. No new framework or calculation engine.

**Spec:** [Layer-1 contracts](../../layer-1-contracts.md), [HRMS payroll policy](../../hrms-payroll-policy.md), [operation contracts](../../payroll-operation-contracts.md), [reconciliation](../../implementation-reconciliation.md).

## Global constraints

- “A usable complete draft has fixed content.”
- “An active hold excludes the draft from commit; history remains available.”
- “The employee-period draft is the unit of monetary commit.”
- “Posted history is immutable.”
- “Money and currency are represented exactly.”
- “No canonical number generator is prescribed.” Employee/month association does not replace exact draft identity.
- Preserve tenant/capability checks, atomic applications and durable replay under both freshness policies.
- Default existing callers to their current approval/freshness safeguards; policy changes require authorized, recorded controls.
- No direct attendance-to-payroll transition, business-origin deduplication, tax formulas, official certificate issuance, or general accounting.
- All paths below are relative to HRMS Core unless explicitly identified as handbook or E2E paths. New names and interfaces are proposed engineering choices, not previously approved handbook field names.
- Existing Core `AGENTS.md`: `VERSION` is authoritative; public API, migrations, CLI, authorization and configuration are compatibility surfaces.

---

## Status, scope and chosen approach

Plan prepared 2026-09-06; no implementation starts in this documentation pass.
Core main was rechecked at `3a87931ea536c8b617e6e391c14affd03ade9f65`.
The preserved candidate is `fix/payroll-ledger-schema@01268e5`, last code
`5bc0b1a`. The handbook reconciliation is `65f24ee`.

Recommend adapting the local fixes in a new integration branch. Rebuilding
payroll would duplicate accepted Core behavior; a wrapper alone cannot fix
mandatory SQL freshness or prevent another caller from committing a held draft.
Adaptation preserves useful tests and history while changing the actual gates.

This is a program of four bounded implementation packages, plus an initial
coverage checkpoint. Each package has its own plan and acceptance gate. Existing
code counts as supported only with relevant evidence; the six PAY-DB findings
are not a complete inventory of handbook compatibility.

## Repository and branch scope

| Repository | Planned work |
|---|---|
| `agentlabs-hrms-core` | Source/application fixes, explicit contribution handling, generic liability metadata, draft controls, protected commits, annual package, APIs, CLI and tests |
| `agentlabs-payroll-ledger-lab` | Plans, conformance matrix, rationale and evidence; preserve the TypeScript demonstration as a historical lab |
| `agentlabs-hrms-e2e` | Authenticated integration evidence for the exact Core commit; inspect its current instructions/harness before editing |
| `agentlabs-hrms-design` | Read hub/acceptance constraints; no design-repository edits or ticket changes planned |

At execution, create an isolated worktree on `feat/payroll-handbook-compat`
from then-current Core main. Preserve `fix/payroll-ledger-schema` unchanged.
Port reviewed changes deliberately; do not merge the entire old branch or copy
all its migrations before their dependencies are ready. Preserve existing
migration numbers through current main. Reuse unshipped 92–95 only if still free
and verified never deployed; otherwise assign the next available sequence and
update test fixtures. Never rewrite a migration already shipped elsewhere.

## Coding and review arrangement

- Primary agent owns the conformance matrix, interface decisions, integration and review.
- Dispatch each bounded coding task to a fresh `gpt-5.6-sol` agent with `reasoning_effort: medium` and a self-contained task packet; use `fork_turns: none` so the model override is explicit.
- Include exact handbook clauses, owned files, prerequisite commits, acceptance cases and commands. The agent returns its commit, test evidence and unresolved issues.
- Keep one coding owner for shared payroll services/migrations. Parallel coding is limited to independent files after their interfaces are fixed; four available slots are a ceiling, not a target.
- Review contract compliance and then code quality after each task. Fix findings before integration; do not treat the coding agent's summary as verification.
- Commit each verified unit locally. Publishing, merging and deployment are separate from this plan's implementation checkpoints.

## CP-0: establish coverage and lock interfaces

**Files:** create Core `docs/payroll-handbook-conformance.md`; update handbook
`docs/implementation-reconciliation.md` only with actual new evidence.

- [ ] Recheck main, candidate ancestry, working-tree changes and migration availability; record full SHAs and preserve the old candidate.
- [ ] Fill the following coverage matrix with actual service/gateway/CLI/test references and one of `verified`, `needs change`, or `not yet proven`. An existing endpoint name alone is not evidence.
- [ ] Review the proposed controls and metadata contracts in packages B/C against current hash and gateway formats. Keep existing serialized identities compatible; use explicit versioning for new authority formats.
- [ ] Record this as an engineering checkpoint before coding the controls. Raise only an actual handbook conflict or material choice; do not reopen the generic organizational questionnaire or PAY-Q-020.

| Handbook contract | Planned owner and completion evidence |
|---|---|
| Manager/API intake; producer-supplied amounts | A: repaired instruction API; B: explicit complete proposals; no internal attendance transition |
| Salary entitlement and immutable fact/instruction replacement | A: existing protected source operations tested with expiry, replacement and late target-period processing |
| Monthly and one-time applications | A: identity/uniqueness and no draft consumption; C: same guards under both policies |
| Complete fixed draft; simulation has no monetary writes | B/C: exact candidate identity, atomic batch/seal behavior and replacement history |
| Approval, hold/release and uncommitted cancellation | C: exact-draft controls, authorized history, race and bypass tests |
| Freshness policy A and draft authority policy B | C: same changed-source scenario gives the two agreed outcomes |
| Independent employee commits and employee-month association | C: 99/100 case, multiple results grouped without duplicate aggregation; D: public evidence |
| Subsequent-month corrections and accounting boundary after exit | B: immutable linked adjustments; D: retained policy journey and explicit handoff; no Core inference of business intent |
| Contribution gross/net and one liability basis | B: 50,000 + 1,000 example and historical compatibility |
| Partial remittance, proof and remaining liability | B: 10,000 → 4,000 → 0, concurrency and preserved proofs |
| Annual package, missing coverage and cutoff | D: employee/employer/year isolation, exact-once sums and settlement evidence |
| Tenant permissions, exact money, retries and atomic failures | All packages locally; D against the built Core through API/CLI |

If CP-0 discovers an additional mismatch in an unchanged path, add a bounded
repair and test to its owning package before claiming compatibility. Do not
silently classify unverified baseline behavior as done.

## Delivery sequence and checkpoints

| Order | Package | Gate |
|---|---|---|
| 1 / CP-1 | [A — source and application integrity](2026-09-06-payroll-compat-integrity.md) | Public instruction creation works; full keys, finite expiry and application constraints preserved |
| 2 / CP-2 | [B — contributions and liabilities](2026-09-06-payroll-compat-money.md) | Explicit pairs and generic obligation authority; correct gross/net, partial settlement and immutable corrections |
| 3 / CP-3 | [C — draft controls and policy-aware commit](2026-09-06-payroll-compat-controls.md) | Both policies, protected hold/cancel/release, independent commits and exact replay work through all relevant gates |
| 4 / CP-4 | [D — annual package and public acceptance](2026-09-06-payroll-compat-acceptance.md) | Scoped reporting and authenticated CLI/API journeys pass against the exact integrated commit |
| 5 / CP-5 | Final reconciliation | Every in-scope matrix row has evidence; handbook distinguishes implementation, employer policy and deployment status |

Control interfaces are reviewed at CP-0 because they are high impact. Their
implementation follows money/application dependencies; the sequence is not a
request to implement every feature before seeing a useful result.

## Final verification and done condition

After each package run its targeted tests and review the diff. After integration:

```bash
PAYROLL_TEST_POSTGRES_BIN=/tmp/payroll-postgres16/bin go test ./internal/modules/payroll -count=1
make test-short
make build
go test ./cmd/agl-hrms-cli -count=1
git diff --check
```

The local PostgreSQL path is the previously used test installation; verify its
executables first or use the repository-supported PostgreSQL test provisioner.
Skipped database tests are not a passing integration gate. Use isolated databases,
never production data. Run the E2E commands and identity-bound signoff specified in package D against
the built commit and record the exact invocation and server/CLI identity. If release
is later requested, also apply Core's `make test` and `make package-release` gates.

Done means each in-scope contract is implemented or proven already supported,
all new operations are granted and reachable through API/CLI, migrations preserve
history, and both policy scenarios pass. External live-proof blockers must remain
visible; a local build cannot close that checkpoint. Employer-specific approver
lists, formulas and certificate issuance are not conditions for this completion.

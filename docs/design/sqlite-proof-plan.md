# SQLite proof of 123 Architecture

**Pinned sequence, 2026-09-08.** The user proposed proving the model with SQLite
before touching actual production code. This plan belongs to the existing lab
design work and [Lab #1](https://github.com/agentlabs-poc/agentlabs-payroll-ledger-lab/pull/1).
It is not a report of a completed prototype or a new production implementation.

The contract under test is [123 Architecture](123-architecture.md): core canonical
tables plus one canonical key/value table per software-owned domain/layer
(L1/L2). Consumers own L3 persistence; no L3 store is supplied. The
[record chapter](payroll-records.md) supplies candidate JSON examples and the
complete 16-table consolidation map; the [table register](canonical-ledger-tables.md)
supplies current ledger roles and known representation gaps.

## Intended result

Produce a small executable lab that creates an isolated SQLite database, seeds
representative records and exercises domain-specific/shared wrappers. A small
number of documented commands should reproduce the proof and its report. Keep
the database disposable and separate from live payroll; retain the source,
fixtures and results needed to reproduce findings. The browser experiment need
not change merely to exercise storage.

Resolve key/lifecycle ambiguities through explicit prototype assumptions and
evidence, then review the resulting canonical contract. A prototype choice must
not silently become a production requirement. Keep the model focused on payroll;
do not build a general framework before demonstrating the concrete case.

## Finite proof checkpoints

| Checkpoint | Exercise | Required evidence |
|---|---|---|
| 1. Canonical storage and keys | Representative core ledger tables and L1/L2 stores; valid/invalid payloads; exact key encoder/decoder; conflicting key/payload identities. | Agreed versus prototype-only schema choices; malformed records rejected; tenant/store scope separated; numeric revision 10 follows 2; no supplied L3 persistence. |
| 2. Definitions, settings and state | Versioned components, L2 employee preferences/policy assignment and enabled/disabled/logically deleted history. | Effective versus latest revision behavior; disabled newer records do not resurrect older ones; existing references remain resolvable; protected evidence cannot be deleted to reopen consumption. |
| 3. Draft-to-posted integrity | One employee's salary and a monthly loan instruction, fixed draft, selected controls/review, commit and instruction application. | Posted money and application/receipt are atomic; held drafts cannot commit; no policy choice is mandated merely by the prototype. |
| 4. Failure, retry and expiry | Duplicate/changed retries, competing commits, stale control updates, injected failure, database reopen and the loan's first/last/expired periods. | No duplicate money or consumption; rollback leaves no partial commit; committed evidence survives reopen; expiry follows payroll period; settings do not rewrite posted facts. |
| 5. Indexed access and consumption | Exact record, subject history/current state, employee/month, instruction application, operation replay and required reverse links through wrappers. | Query plans for representative cardinalities; query results, latency, database/index space where measurable, and evidence that domain/general paths enforce the same contract. |

Use the illustrative E101 payroll: salary INR 50,000, monthly loan deduction INR
2,000 valid October 2026 through February 2027, and November net INR 48,000. This
is a fixture, not an organizational payroll rule. Add a separate one-time
instruction fixture to prove single consumption without changing that example's
expected totals. Use deterministic expected amounts and portable JSON fixtures.

The complete model also needs payroll-backed employer liabilities and a
remittance/allocation example: liability remains outstanding without settlement
evidence; allocation reduces it without changing posted payroll. Salary Earning
Ledger representation is a known gap: declare any prototype representation as
such rather than invent an accepted production table. Check every one of the
16 supporting roles against the proof, including combined/eliminated records,
before claiming complete architectural coverage.

## Portability and authority boundaries

Use a portable JSON document contract; SQLite can store JSON as text with JSON
functions and validation. SQLite's optional JSONB format is not binary compatible
with PostgreSQL JSONB. [SQLite JSON documentation](https://www.sqlite.org/json1.html)

Explicitly enable and verify foreign-key enforcement on every test connection.
JSON reference arrays additionally need the chosen contract's reference checks;
valid JSON alone provides none. [SQLite foreign-key documentation](https://www.sqlite.org/foreignkeys.html)

Exercise competing connections and rollback, while recording SQLite's single-
writer concurrency model. A SQLite result does not predict PostgreSQL writer
throughput or establish its locking behavior. [SQLite isolation documentation](https://www.sqlite.org/isolation.html)

Wrapper scope tests can demonstrate tenant/layer authorization behavior in the
lab. They cannot prove PostgreSQL database roles/RLS, server authentication or
production deployment isolation. A shared API wrapper must not allow a caller
to bypass the domain handler by selecting the L1 table or inventing a record key.

## Evidence and exit criteria

Record source revision, SQLite/runtime versions, fixture size, commands,
pass/fail assertions, query plans and measured timings/storage. Keep functional
proof separate from performance claims; do not extrapolate a small lab timing
to the earlier 3,000-employee production-service benchmark.

The lab passes when the covered contracts and their failure/retry paths behave
as specified, all 16 roles have an explicit disposition, and remaining findings
are resolved or accurately scoped. Then reconcile the demonstrated contracts
into Core's handbook before implementing them. Production acceptance still
requires PostgreSQL-specific indexes/constraints, authority, concurrency,
migration/data compatibility and runtime regression proof.

This plan pins the order of work. No SQLite database, prototype implementation,
successful test result or production change is created by this documentation.

# Payroll Ledger Lab

> **Identity contract under review:** every employee-owned record must include
> the employee in its key. The existing serialized examples predate this rule;
> they are not the final key contract. See [canonical identity definitions](docs/design/canonical-identities.md).

The payroll handbook, contracts, decisions, and rationale now live in [HRMS Core](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/handbook.md). Core is the canonical accepted handbook source. The lab retains the browser experiment, forwarding pages for migrated chapters, and the [current design pins](docs/design/README.md) requested by the user.

## Current design pins

- [SQLite-first proof before production implementation](docs/design/sqlite-proof-plan.md)
- [123 Architecture and canonical vocabulary](docs/design/123-architecture.md)
- [Canonical ledger tables and existing support-table inventory](docs/design/canonical-ledger-tables.md)
- [Payroll key/value records by domain and layer, wrappers, JSON, state and indexes](docs/design/payroll-records.md)

The proposed shape is one key/value table per domain and software-owned layer
(L1/L2), with `tenant`,
`key`, `value` and `ts`, plus a proposed `state` column. Payroll owns its canonical
terms and indexes; other domains may reuse the shape with their own contracts.
Domain-specific APIs and general wrappers can operate owned records while
preserving L1 domain operations and authority boundaries.
Consumers own L3 composition and storage; this software supplies no L3 table/API.
The pins contain full design content and distinguish accepted direction from
remaining proposals. The SQLite and browser simulations exercise the pinned prototype contracts.
Production schema and API migration remain separate work.

## Migrated handbook

Publication order: merge Core hub PR #172 before this forwarding PR so the canonical `main` targets exist.

The [independent handbook review](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/main/docs/payroll/handbook/review-2026-09-08.md) records the resolved documentation findings. Reviewed implementation is integrated in [Core draft hub PR #172](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/172); complete authenticated handbook acceptance remains pending in [E2E PR #61](https://github.com/agentlabs-poc/agentlabs-hrms-e2e/pull/61).

## Python CLI and persistent SQLite

The [CLI guide](docs/design/python-cli.md) lists all implemented L1 and L2
primitives and runnable commands. L3 consumer Python scripts invoke the CLI;
the CLI calls the existing primitives in process. Production HRMS core remains Go.

```sh
./payroll-cli --help
python3 -m sqlite_lab.cli_demo --db /tmp/payroll-cli-walkthrough.sqlite
```

Use a fresh database path, or an empty database prepared by `payroll-cli reset`.
The walkthrough retains it for subsequent CLI queries. Use `--tax-regime old`
to compare the [Karnataka example](docs/design/karnataka-payroll-demo.md) with
the default new regime; obligations stay unpaid unless `--settle` is selected.
Generated IDs follow the [prefixed Snowflake Base36 direction](docs/design/canonical-generated-ids.md);
current demo IDs are supplied fixtures and generator wiring remains separate.

## Canonical HTML simulation

The browser shows a guided playback of **actual SQLite simulation rows**. It uses
three canonical ledger tables and one L1 record table; L2 settings are separate.
Salary earnings and monthly/one-time instructions are canonical records, not
additional ledgers. The [HTML walkthrough](docs/design/canonical-html-demo.md)
explains every stage and record family.

```sh
npm ci
npm run dev -- --port 5174
```

Open the displayed URL. Select a stage or use the next/previous controls to
inspect the rows present at that point. Expand a row to see its complete JSON,
including its canonical key, references, state and integer minor-unit amounts.
The browser reads a checked-in fixture; it does not write to a live database.

Regenerate the browser fixture from the executable Python simulation:

```sh
python3 -m sqlite_lab.demo --output public/canonical-flow.json
```

The connected example covers E101 and E102 over October 2026–March 2027 in
18 stages, including a five-month loan, future-effective earnings, draft policy
choices and subsequent-month corrections. Employer obligations total ₹36,000;
explicit remittance allocations demonstrate partial and complete settlement.
All three monetary ledgers appear as tables, with original JSON expandable.

Only these are canonical ledgers:

- `payroll_draft_ledger`: fixed draft monetary lines.
- `payroll_ledger`: committed monetary lines.
- `payroll_employer_liability_ledger`: obligations, remittances and allocations.

`payroll_l1_records` holds component definitions, earnings, instructions, draft
metadata, controls, reviews, resolutions, applications and operation receipts.
`payroll_l2_records` holds auxiliary employee settings. Consumers own L3.

The original browser's salary/input ledgers, mutable draft objects and mandatory
approval sequence have been superseded. The current page focuses on canonical
storage; HR intake, organizational policy and document rendering belong to the
consuming application. This remains a prototype, not a production API or a
claim of PostgreSQL compatibility.

## SQLite proof and diagrams

- [Three-ledger design](docs/design/three-ledger-simulation.md)
- [Complete canonical row map](docs/design/canonical-row-map.md)
- [Canonical storage SVG](docs/diagrams/payroll-canonical-storage.svg)
- [Employee journey SVG](docs/diagrams/payroll-employee-journey.svg)
- [SQLite commands and scope](sqlite_lab/README.md)
- [Historical nine-table proof](docs/evidence/sqlite-record-fold/README.md)

The earlier evidence remains source-bound historical material; it does not prove
the new three-ledger implementation.

Current [three-ledger evidence](docs/evidence/three-ledger-simulation/README.md) retains
the complete row catalogue and the verified browser journey.

# Payroll Python CLI Implementation Plan

**Goal:** Demonstrate all existing L1 and L2 payroll operations through a Python CLI calling existing Python primitives in process against persistent SQLite.

**Architecture:** Python is the executable lab reference. Go remains production HRMS core. CLI adapters preserve primitive inputs/outputs; scripts own policy and multi-operation orchestration.

**Tech stack:** Python standard library, existing Payroll and RecordStore, SQLite.

**Spec:** [CLI reference and layer inventory](../../design/python-cli.md). User-approved CLI → in-process Python payroll primitives → SQLite; all L1 and implemented L2 primitives exposed. Existing canonical identity and three-ledger contracts apply.

## Constraints

- Sol-medium performs coding; root maintains docs and checks actual execution.
- No Go/production changes, new dependencies, bulk L1 operations or additional schema tables.
- Existing fresh demo and HTML output remain usable.
- Retain an explicit database path; refuse destructive reseeding.
- L1 reads stay L1; L2 includes only implemented employee-settings operations. The CLI is an interface; Python subprocess scripts are L3 consumer examples.
- Tenant scope applies to every query. Expose an explicit operation allowlist, not arbitrary SQL or private methods.
- JSON inputs use existing canonical field names. Ledger output supports actual tables and JSON.
- Snowflake Base36 with canonical prefixes is accepted; generator configuration/conversion is separate. Supplied example IDs must be described as fixtures, not claimed as generated IDs.
- User requested demo work without regression expansion. Execute the walkthrough and check persistence, errors and amounts; no new regression campaign.

## Work

- [x] Add `sqlite_lab/cli.py`: explicit L1/L2 operation groups, initialization, canonical ledger/record reads, JSON input, table/JSON output and nonzero error exit.
- [x] Add `sqlite_lab/cli_demo.py`: separate CLI processes operate on one retained database; demonstrate inputs through draft/control/review/commit and employer obligation/remittance/allocation, plus replay and timing.
- [x] Update `sqlite_lab/demo.py`: optional retained `--db` for the existing six-month/18-stage flow; preserve default temporary behavior and refuse reseeding an existing populated database.
- [x] Document exact runnable commands and full supported primitive inventory.
- [x] Run the CLI walkthrough, reopen/query its database from another process, and run the six-month export against retained SQLite. Check three monetary ledgers, L1/L2 records and expected totals.
- [x] Commit on the existing Lab branch and push; retain the existing PR.

## Execution evidence

- `33cc84c`: retained six-month SQLite walkthrough; 18 stages, five tables, 93 committed rows.
- `af4279a`: CLI exposes 18 L1 and four L2 operations; L3 subprocess walkthrough.
- Actual L3 run: 26 operation/read calls before final table display, 1426.539 ms including Python process startup. Gross ₹58,000, deductions ₹5,000, net ₹53,000; six draft and six committed rows.
- Held commit rejected; identical commit replay preserved outcome; ₹3,000 outstanding after remittance, zero after allocation; three ELR rows.
- Fresh-process ledger reads succeeded. A different tenant returned no rows; uninitialized databases and L2 settings passed to L1 history were rejected.
- HTML build passed. Demo timing is not a production Go/Postgres benchmark.

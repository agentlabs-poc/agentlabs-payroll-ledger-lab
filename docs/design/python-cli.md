# Python CLI reference demonstration

Python supplies the executable lab reference. Production HRMS core remains Go.

```text
L3 consumer Python script
    → CLI interface
        → L1 core primitive or L2 auxiliary primitive (in process)
            → SQLite
```

The layer is determined by responsibility, not language or transport. The CLI
adds no business policy. Consumer scripts choose employees, sequence, approval
requirements, source reconciliation and explicit remittance allocations.

## Operation inventory

L1 owns canonical payroll facts and monetary invariants. The CLI exposes the
existing Python primitives using their original argument names:

| Area | L1 operations |
|---|---|
| Components | `define_component`, `disable_component` |
| Employee earnings | `define_earning` |
| Instructions | `add_instruction`, `add_instruction_version`, `instruction_application` |
| Draft | `create_draft`, `set_draft_control`, `review_draft`, `commit` |
| Employer liability | `record_obligation`, `record_remittance`, `allocate_remittance`, `elr_outstanding` |
| Canonical record reads | `get_l1`, `history_l1`, `current_l1`, `effective_l1_source` |

L2 owns software-provided auxiliary data. Currently implemented operations are
`put_l2_settings`, `get_l2`, `current_l2_settings`, `effective_l2_settings`.
Reusable compensation templates are a possible L2 concept, not an implemented
command. Optional India tax-regime selection is represented in L2 settings; calculation stays in the L3 example. See the [Karnataka fixture](karnataka-payroll-demo.md).

`ledger` reads the three canonical monetary ledgers. `records l1` and
`records l2` list the respective record stores. All reads are tenant-scoped.
No command exposes unrestricted SQL or raw writes to L1 records.

## Natural commands and saved defaults

From the Lab repo, configure the CLI once:

```sh
./payroll-cli configure --db /tmp/payroll.sqlite --tenant T1 --actor payroll-admin
./payroll-cli reset
```

`configure` saves database, tenant, actor and output preferences in
`.payroll-cli.json`. Use `--config PATH` or `PAYROLL_CLI_CONFIG` for a separate
configuration. Explicit CLI options override saved defaults. The local config
is not committed to Git.

`reset` empties **all tenants' payroll data in the configured local demo database**
and recreates the five tables, preserving CLI configuration. It refuses an
unrelated database. This is an explicit demo reset, not a production migration.

Commands use domain nouns and verbs:

```sh
./payroll-cli component define --input - <<'JSON'
{"component_id":"BASIC","revision":1,"code":"BASIC","label":"Basic","kind":"earning","country_code":"IN"}
JSON

./payroll-cli settings set --input settings.json
./payroll-cli earning define --input earning.json
./payroll-cli instruction add --input instruction.json
./payroll-cli draft create --input draft.json
./payroll-cli draft review --input review.json
./payroll-cli draft commit --input commit.json
./payroll-cli --format table ledger payroll
./payroll-cli --format table ledger liability
```

The JSON files above are supplied operation inputs, not files automatically
created by configuring the CLI. Use `--input -` to supply a JSON object on stdin.
Canonical argument names and integer minor-unit amounts are preserved. Settings
commands map to L2; component/earning/instruction/draft/liability commands map to
L1. The interface itself does not own company policy.

The original `python3 -m sqlite_lab.cli ... l1 <operation>` and `l2 <operation>`
forms remain available. `operations` prints their explicit inventory. `records l1`
and `records l2` list tenant-owned records. Full canonical ledger table names are
also accepted, alongside `draft`, `payroll` and `liability` display aliases.

## L3 consumer walkthrough

Run the consumer Python script, which invokes separate CLI processes for the
individual L1/L2 operations:

```sh
python3 -m sqlite_lab.cli_demo --db /tmp/payroll-cli-walkthrough.sqlite
```

Use `--step` to display each actual CLI command, its JSON input and result,
with Enter to advance:

```sh
python3 -m sqlite_lab.cli_demo --db /tmp/payroll-cli-stepped.sqlite --step
```

It leaves SQLite available for further CLI inspection. The consumer chooses the
flow and explicit allocation amounts; no orchestration is added to L1. Its
assertions check the actual returned results and it reports elapsed time.

For `history_l1` and `current_l1`, supply `record_type` plus its named identity
fields without revision. For example:

```json
{"record_type":"payroll.earning","employee_id":"E101","earning_id":"earning_9do1sj396nf9"}
```

## Existing six-month reference

Retain the actual SQLite database underlying the existing 18-stage HTML flow:

```sh
python3 -m sqlite_lab.demo --db /tmp/payroll-six-month.sqlite --output /tmp/payroll-six-month.json
python3 -m sqlite_lab.cli --db /tmp/payroll-six-month.sqlite --tenant T1 --actor payroll-admin --format table ledger payroll_ledger
```

Use a fresh database path: the walkthrough refuses to overwrite populated data.
The original command without `--db` still uses disposable SQLite and exports
snapshots. HTML renders captured rows; it is not an HTTP payroll service.

## Boundaries

There are five canonical data tables: three monetary ledgers and L1/L2 record
stores. L3 consumer scripts have no supplied L3 database table or bulk L1 API.
This demonstrates domain behavior, not production Go/Postgres throughput.

Generated IDs are specified by the [prefixed Snowflake Base36 contract](canonical-generated-ids.md).
Current example IDs are supplied fixtures, not evidence of a working distributed
Snowflake generator. Epoch, worker coordination and generator wiring remain a
separate implementation task.

## Karnataka example

The current CLI consumer uses actual canonical salary, EPF/EPS, Karnataka
profession-tax and income-tax withholding components. Select `--tax-regime new`
or `--tax-regime old`; `--step` displays each command. The default stops with
unpaid authority obligations; add `--settle` to demonstrate remittance and allocation.

[Fixture assumptions, amounts and source basis](karnataka-payroll-demo.md) are
explicit. The earlier generic 26-call example remains historical evidence; its
₹58,000 gross and ₹3,000 liability are not the current Karnataka fixture amounts.

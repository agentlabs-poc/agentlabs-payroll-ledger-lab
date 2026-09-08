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
command. Tax regime settings are not implemented in the current settings schema.

`ledger` reads the three canonical monetary ledgers. `records l1` and
`records l2` list the respective record stores. All reads are tenant-scoped.
No command exposes unrestricted SQL or raw writes to L1 records.

## Commands

Run from the Lab repository root. Initialize a new database explicitly:

```sh
python3 -m sqlite_lab.cli --db /tmp/payroll-cli.sqlite --tenant T1 --actor payroll-admin init
```

Invoke a primitive with a JSON object from a file or standard input:

```sh
python3 -m sqlite_lab.cli --db /tmp/payroll-cli.sqlite --tenant T1 --actor payroll-admin l1 define_component --input - <<'JSON'
{"component_id":"BASIC","revision":1,"code":"basic","label":"Basic","kind":"earning","country_code":"IN"}
JSON
```

The same envelope applies to `l1 <operation>` and `l2 <operation>`. Operation
arguments follow the Python primitive contract; tenant and actor come from CLI
options. Read errors and rejected operations return a nonzero exit status.

Inspect actual persisted ledgers as tables:

```sh
python3 -m sqlite_lab.cli --db /tmp/payroll-cli.sqlite --tenant T1 --actor payroll-admin --format table ledger payroll_draft_ledger
python3 -m sqlite_lab.cli --db /tmp/payroll-cli.sqlite --tenant T1 --actor payroll-admin --format table ledger payroll_ledger
python3 -m sqlite_lab.cli --db /tmp/payroll-cli.sqlite --tenant T1 --actor payroll-admin --format table ledger payroll_employer_liability_ledger
python3 -m sqlite_lab.cli --db /tmp/payroll-cli.sqlite --tenant T1 --actor payroll-admin records l1
python3 -m sqlite_lab.cli --db /tmp/payroll-cli.sqlite --tenant T1 --actor payroll-admin records l2
```

List the full grouped inventory with `operations` (using the same database, tenant and actor options).

The default output is JSON. Original integer minor-unit amounts remain canonical;
formatted amounts are only presentation.

## L3 consumer walkthrough

Run the consumer Python script, which invokes separate CLI processes for the
individual L1/L2 operations:

```sh
python3 -m sqlite_lab.cli_demo --db /tmp/payroll-cli-walkthrough.sqlite
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

## Demonstrated result

The L3 example executes 26 CLI calls before final ledger display. Its actual
assertions cover gross ₹58,000, deductions ₹5,000 and net ₹53,000, a rejected
held commit, identical commit replay, and ₹3,000 remaining outstanding after
remittance until allocation closes it. SQLite retains six draft entries, six
committed entries, three ELR entries and the L1/L2 records. Timings include
Python subprocess startup and are illustrative local execution measurements.

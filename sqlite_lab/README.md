# Three-ledger SQLite payroll simulation

This disposable simulation implements exactly three canonical ledgers:
`payroll_draft_ledger`, `payroll_ledger`, and
`payroll_employer_liability_ledger`. Canonical definitions, sources, draft
metadata, controls, applications and receipts live in `payroll_l1_records`;
employee settings live in `payroll_l2_records`. These are the only five physical
tables. There are no compatibility views or supplied L3 storage.

Run the complete real-file suite and disposable proof from the repository root:

```sh
python3 -m unittest discover -s sqlite_lab -p 'test_*.py' -v
python3 -m sqlite_lab.prove
python3 -m sqlite_lab.prove --output-dir /tmp/payroll-three-ledger-evidence
```

The retained form refuses to overwrite `proof.sqlite3`, `evidence.json`,
`canonical-rows.json`, or `canonical-catalog.json`. `connect()` also rejects a
database with an incompatible earlier prototype topology; it never migrates it.

The L1 registry contains exactly `payroll.component`, `payroll.earning`,
`payroll.instruction`, `payroll.draft`, `payroll.draft.control`,
`payroll.draft.review`, `payroll.instruction.resolution`,
`payroll.instruction.application`, and `payroll.operation.receipt`. L2 contains
`payroll.employee.settings`. The catalogue also covers draft and posted monetary
rows plus obligation, remittance, and allocation rows: 15 required kinds total.

Keys use `<type>:<subject>:<record>`. Dots separate registered namespace tokens.
Within identity segments only, `\:` represents a colon and `\\` represents a
backslash. Unknown, unnecessary, and trailing escapes are rejected; identities
preserve case. Revisions are positive canonical decimal digits and sort
numerically. The 64-character ASCII identity limit remains a prototype choice.

Earnings and instructions are immutable versioned L1 sources that reference an
exact component version, employee, integer minor-unit amount, and inclusive
effective bounds. An instruction also stores an opaque version ID and cadence.
Draft creation accepts exact earning and instruction record keys. It does not
accept a calculation ID or invent salary entitlement from a scalar amount. A
fixed `payroll.draft:<id>:1` record stores source keys, content hash, employee,
month, and balanced totals; its monetary lines live in the draft ledger.

Component kind determines direction. Earnings add to gross, deductions add to
deductions, and employer contributions add equal expense and liability amounts
to gross and deductions, leaving net unchanged. The connected E101 fixture uses
salary 5,000,000, employer contribution 300,000, and loan deduction 200,000:
gross 5,300,000, deductions 500,000, net 4,800,000.

Commit uses `BEGIN IMMEDIATE`, validates the exact draft/control and optional
review, copies all draft lines to immutable posted rows, records instruction
applications and effects, and writes a durable outcome receipt in one
transaction. Stable instruction identity protects monthly and one-time
consumption across versions. A separate one-time earning instruction fixture
proves that earning direction and protection.

The employer-liability ledger uses immutable typed rows. An obligation must
exactly match one posted employer-liability row. A remittance requires proof.
Allocations reference both and enforce obligation and remittance caps; one
remittance may span obligations. The connected fixture records 300,000 due,
200,000 remitted and allocated, and 100,000 outstanding.

`canonical-rows.json` contains every actual row from all five tables.
`canonical-catalog.json` contains one actual stored example for every required
kind with meaning, owner, identity, references, validation, and indexed queries.
The evidence report includes source hashes, timings, row counts, query plans,
storage measurements, the earlier 16-role disposition, and the former nine-table
replacement map.

This is targeted prototype validation, not full production JSON Schema. Record
timestamps come from the Python wrapper. Employee, actor, policy, and upstream
source referents are external to this simulation. Exact HTTP response replay,
PostgreSQL permissions/RLS, migration compatibility, concurrency behavior, and
representative load remain unproved. No timing is a performance claim.

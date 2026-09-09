# Historical nine-table SQLite payroll proof

**Historical evidence:** this proves the former nine-table layout, not the current
[three-ledger target](../../design/three-ledger-simulation.md). Reproduce it from
the source revision below; the current simulation is being converted.

Source: `44de62d61965f624b180016801c8068716802ba5`, Python 3.14.4,
SQLite 3.46.1. This is the isolated lab proof of the folding design, not
production compatibility or performance acceptance.

- [Measured proof and persisted ELR rows](proof.json): source hashes, outcomes,
  query plans, fixture timings/storage, all 16 supporting-role dispositions and gaps.
- [Seven full stored record examples](record-examples.json): owning table,
  canonical record type, key and complete JSON row for each of the six L1 types
  and L2 employee settings. Detailed payloads are prototype choices.
- [Canonical table/type inventory](../../design/payroll-records.md#canonical-tables-and-canonical-record-types):
  the nine designated ledgers, target shared stores, meanings and approved grammar.

## Reproduce

Run from the lab repository root:

```sh
python3 -m unittest discover -s sqlite_lab -p 'test_*.py' -v
python3 -m sqlite_lab.prove --output-dir /tmp/payroll-proof-new
```

Choose a fresh output directory: the proof refuses to overwrite an existing
database or evidence file. The JSON files retained here are small text evidence;
the disposable SQLite database is not committed. Source hashes bind the measured
implementation. The retained report additionally reads actual ELR rows from that
database, and the examples are selected from its L1/L2 stores.

## Verified result

Controller verification: **33 tests passed**, 0.118 seconds for the test suite;
Python compilation and whitespace checks passed. A separate fresh proof run
produced 21 L1 records, two L2 records and the nine canonical table representations.
All four reported query plans use their intended expression/partial indexes.
The fixture database occupies 159,744 bytes (39 pages of 4,096 bytes).
These tiny-fixture timings and plans are not a scale benchmark.

The E101 November fixture has INR 50,000 gross, INR 2,000 loan deduction and
INR 48,000 net. Loan applicability includes October through February and excludes
March. Separate tests prove one-time consumption across instruction versions,
atomic commit/rollback, reopen/retry, competing commits, hold/review and exact
key/payload identities. The contribution regression asserts INR 53,000 gross,
INR 3,000 deductions and INR 50,000 net for salary INR 50,000 plus contribution
INR 3,000. The separate ELR journey leaves INR 3,000 outstanding until a
challan-backed INR 2,000 allocation reduces it to INR 1,000.

Review corrections have observable regressions: fractional/boolean ELR amounts,
wrong or duplicate liability sources, component collisions/identity changes,
case/wildcard lookup collisions, malformed keys, escaped L2 lookups and omitted
employer contributions in gross/deductions. Remittance proof is required.

## Scope and remaining gaps

Fifteen old supporting roles have representative witnessed or combined evidence;
exact HTTP response replay remains an explicit transport gap. This is role-level
consolidation evidence, not exhaustive replacement of every legacy table behavior.

PostgreSQL authority/RLS, constraints/indexes, concurrency, migration compatibility,
representative load, platform-shared component definitions, a canonical salary
source and the L2 policy referent remain unproved. Prototype validation covers
closed top-level fields and selected invariants, not a complete production JSON
Schema. The wrapper supplies `ts`; the design's database-recorded timestamp is
not yet implemented. Consumers own L3 persistence; no L3 store/API is supplied.

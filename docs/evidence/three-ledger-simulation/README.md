# Three-ledger simulation evidence

> These results prove the prototype before the employee-owned key correction.
> They do not prove the new identity rule. See
> [canonical identity definitions](../../design/canonical-identities.md).

Verified source: `d7e7b426c4fb33d1115371a30e59d4561dbb723e`. The JSON evidence also binds the exact
schema and Python operation/export files by SHA-256. This replaces the earlier
nine-table proof for the current model; the old evidence remains historical.

## Reproduce

```sh
python3 -m unittest discover -s sqlite_lab -p 'test_*.py'
python3 -m py_compile sqlite_lab/*.py
python3 -m sqlite_lab.prove --output-dir /tmp/payroll-three-ledger-new-proof
python3 -m sqlite_lab.demo --output public/canonical-flow.json
npm run build
```

Use a fresh output directory for the retained proof; the command refuses to
overwrite a database or evidence files. Generated SQLite databases are disposable
and are not committed.

## Verified result

- 42 Python tests passed on real temporary-file SQLite databases.
- Exactly five physical tables: three canonical ledgers, L1 records and L2 records.
- All 15 required row kinds are present, with per-kind examples and reference checks.
- E101 has separate Basic (3,000,000) and HRA (2,000,000) earning records and
  component definitions. With employer contribution and loan, there are five
  draft lines and five posted lines. The component split is illustrative.
- E101 November: gross 5,300,000, deductions 500,000 and net 4,800,000 INR minor units.
- Employer liability: 300,000 due; remittance 200,000 with `challan:REM1` does not
  close the obligation. Allocation reduces outstanding to 100,000.
- A separate E102 one-time earning example rejects repeat consumption through a
  newer instruction version. This adds rows beyond the browser's E101-only journey.
- Regressions cover immutable history, hold/release and optional review, exact
  source authority, opaque/escaped IDs, same-tenant reference mismatches,
  rollback/retry, stable instruction consumption, ELR identities and allocation caps.
- The retained export validates internal component, source, draft, effect,
  historical control, receipt and employer-ledger references.

| Table | Exported rows |
|---|---:|
| `payroll_draft_ledger` | 9 |
| `payroll_employer_liability_ledger` | 3 |
| `payroll_l1_records` | 31 |
| `payroll_l2_records` | 1 |
| `payroll_ledger` | 7 |

## Inspect

- [All actual rows](canonical-rows.json)
- [All 15 row-kind examples, meanings and query/index notes](canonical-catalog.json)
- [Source hashes, outcomes, timings and query plans](evidence.json)
- [Readable canonical row map](../../design/canonical-row-map.md)
- [HTML walkthrough](../../design/canonical-html-demo.md)
- [Browser snapshot data](../../../public/canonical-flow.json)

The browser fixture captures ten stages of the E101 journey from actual SQLite
operations. Its source hashes match the committed executable inputs. Earlier browser verification covered all stages, expandable JSON, three ledger
panels, separate L1/L2 panels, totals and liability distinctions, stage/reset
controls, and preserved keyboard focus. Desktop (1440px) and mobile (390px) checks found no page overflow.
The built page loaded both bundled SVG diagrams and its JSON with HTTP 200; no
browser console errors or warnings were reported.

Independent review identified and closed source-authority, reference-binding,
opaque-version-ID, export-reference and ELR-identifier gaps, then the browser
focus defect. The final scoped re-review found no new breakage.

## Timeline and definition pin verification

At UI source `f676bf9`, the timeline replaces the earlier separate table explorers.
CDP compared every rendered row, including its full JSON and table identity, with
each of the ten selected SQLite snapshots. All ten comparisons matched; the final
timeline contains 31 rows exactly once. The shared definitions show five storage
tables, ten record types, the pending employee-identity contract and the approved
generic segment-column direction. The mobile page at 390px had no horizontal
page overflow; JSON expansion and Previous-button focus worked.

The definition/source pin documents unchanged canonical JSON and key-derived
columns. These checks verify presentation and the current captured rows; they do
not prove the future segment-column schema or its performance. The UI build passed.

## Scope

These are prototype contracts and finite-fixture measurements. The complete
catalogue is not full production acceptance. PostgreSQL permissions/RLS,
migrations, production concurrency/load and exact HTTP response-byte replay remain
unproved. Employee, actor and policy referents are external. No production Core,
API, CLI or database migration changed in this simulation work.

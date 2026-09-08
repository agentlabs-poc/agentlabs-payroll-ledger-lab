# Canonical HTML payroll walkthrough

> **Identity contract under review:** every employee-owned record must include
> the employee in its key. The existing serialized examples predate this rule;
> they are not the final key contract. See [canonical identity definitions](canonical-identities.md).

The HTML demo follows the [three-ledger design](three-ledger-simulation.md).
It displays actual row snapshots produced by named payroll operations in a
temporary SQLite database. The browser is a playback and inspection tool;
changing the displayed step does not create or undo database transactions.

## Why the browser changed

The older page called salary earnings and monthly/one-time instructions separate
ledgers. That contradicted the agreed minimal model. The user requested that the
HTML be realigned and explicitly accepted showing JSON. The current demo therefore
shows three monetary ledger tables, a canonical L1 record store and a separate
auxiliary L2 store. It reads exported SQLite rows so the browser does not maintain
a second payroll implementation with different rules.

## Walk the example

The employee is E101 and the payroll month is November 2026. JSON amounts are
integer INR minor units: `5000000` means ₹50,000.

| Step | Canonical rows and meaning |
|---|---|
| Sources | `payroll.component` defines Basic, HRA, employer contribution and loan. Separate `payroll.earning` records hold ₹30,000 Basic, ₹20,000 HRA and ₹3,000 employer contribution. `payroll.instruction` records a ₹2,000 monthly loan, effective October 2026 through February 2027 inclusive. Auxiliary employee settings are in L2. |
| Draft | `payroll.draft` identifies the exact employee/month, sources, content hash and totals. Monetary lines appear in `payroll_draft_ledger`. `payroll.instruction.resolution` identifies how the loan becomes a deduction in this draft. |
| Hold | A new `payroll.draft.control` revision holds the draft. A commit attempt is rejected; no posted lines or consumption evidence are added. The draft snapshot stays fixed. |
| Release | Another control revision releases the hold, retaining the earlier control history. |
| Review | This example records a `payroll.draft.review` bound to the exact draft and control context. Review requirements are chosen by the consuming layer; the demonstration is not a mandatory L1 approval workflow. |
| Commit | Posted lines appear in `payroll_ledger`, together with permanent `payroll.instruction.application` evidence and a `payroll.operation.receipt`. These are one employee's atomic commit. |
| Obligation | An employer-liability `obligation` references the exact committed employer-liability line for ₹3,000. |
| Remittance | A `remittance` records ₹2,000 with challan proof. Outstanding remains ₹3,000 until payment is allocated. |
| Allocation | An `allocation` links the obligation and remittance for ₹2,000. Outstanding becomes ₹1,000. All three ELR row types share `payroll_employer_liability_ledger`. |

Gross is ₹53,000, deductions are ₹5,000 and net is ₹48,000. Employer contribution
adds ₹3,000 to both gross and deductions; the loan accounts for the other ₹2,000
deduction. The loan's committed application concerns this employee/month; its
monthly cadence permits subsequent eligible months through expiry.

## Component meaning versus employee amount

`payroll.component:BASIC:1` defines Basic with `kind: earning`.
`payroll.component:HRA:1` separately defines HRA with `kind: earning`.
The middle segment is an opaque component ID; the final segment is its revision.
Neither definition carries E101's salary amount.

`payroll.earning:EARN-BASIC:1` links E101 to the exact Basic component version
with amount `3000000` and effective dates. HRA has its own earning record for
`2000000`. These produce separate draft lines and separate committed lines.
The combined ₹50,000 is a salary total, not another component or source ledger.
The amounts are illustrative, not a fixed compensation rule.

## Read the record keys

`payroll.draft:D1:1` is a record key in `payroll_l1_records`. Its JSON is draft
metadata; monetary entries are rows in `payroll_draft_ledger`. A record type is
not another table.

`payroll.draft.*` is shorthand for related record types, including
`payroll.draft.control` and `payroll.draft.review`. No literal wildcard type is
stored. A control revision does not mutate the fixed draft metadata.

`payroll.instruction.resolution` describes draft treatment.
`payroll.instruction.application` proves committed consumption. A held or
uncommitted draft can have a resolution without an application.

Keys follow `<type>:<subject>:<record>`. Dots separate type tokens. Within opaque
identity segments, a backslash escapes a literal colon or backslash. JSON adds
its own string escaping. Use the shared encoder rather than concatenating IDs.

## Run and regenerate

```sh
npm ci
npm run dev -- --port 5174
python3 -m sqlite_lab.demo --output public/canonical-flow.json
```

The generated JSON carries source hashes for the simulation code. Rebuilding the
fixture runs the Python operations against a fresh temporary database. The
browser needs only the resulting JSON, which is bundled with the demo.

Use the [storage diagram](../diagrams/payroll-canonical-storage.svg),
[employee journey diagram](../diagrams/payroll-employee-journey.svg) and
[complete row map](canonical-row-map.md) alongside the live row explorer.

The simulation has five physical tables and 15 required row kinds. Complete
example coverage does not establish production readiness: PostgreSQL authority,
migrations, load and exact HTTP-response replay remain separate proof work.

The [retained evidence](../evidence/three-ledger-simulation/README.md) records the
source-bound checks, complete row catalogue and browser validation.

## Pinned generic key storage

The definitions panel displays the [shared canonical register](canonical-definitions.json),
including the user's example `payroll.component:BASIC` decoded as `key1 = payroll`,
`key2 = component`, `key3 = BASIC`. Canonical JSON stays unchanged; these generic
columns are a storage/index projection. The timeline still shows actual rows from
the earlier SQLite schema, clearly labelled as such. The [identity contract](canonical-identities.md)
records pending employee identities and the remaining SQLite proof checkpoints.

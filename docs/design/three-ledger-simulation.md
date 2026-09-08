# Three-ledger payroll simulation and canonical row map

> **Current storage direction:** canonical segments occupy generic `key1`–`key10`
> columns. `payroll.component:BASIC` becomes `payroll`, `component`, `BASIC`.
> Single-key rows below describe the existing prototype. See the
> [agreed segment contract](canonical-identities.md#generic-segment-columns--agreed-storage-direction).

> **Identity contract under review:** every employee-owned record must include
> the employee in its key. The existing serialized examples predate this rule;
> they are not the final key contract. See [canonical identity definitions](canonical-identities.md).

**User-approved direction, 2026-09-08.** The user named exactly three canonical
ledgers and requested that other responsibilities move into L1 records wherever
possible, keeping the model extremely simple. The subsequent instruction to
commit/push and return to simulation authorizes the lab implementation and the
complete canonical row map below. This supersedes the earlier nine-table target.
Production migration/API implementation is outside this change.

## Storage and canonical meaning

| Layer | Table | Meaning |
|---|---|---|
| L1 ledger | `payroll_draft_ledger` | Immutable monetary entries of an exact employee draft |
| L1 ledger | `payroll_ledger` | Immutable committed payroll entries |
| L1 ledger | `payroll_employer_liability_ledger` | Immutable obligation, remittance and allocation entries |
| L1 records | `payroll_l1_records` | Canonical versioned definitions, draft metadata, controls and evidence |
| L2 records | `payroll_l2_records` | Reusable auxiliary employee payroll settings |

Only the first three are canonical ledgers. There is no supplied L3 store/API.
L1 therefore uses four physical tables, with one separate L2 table. No renamed
copies or compatibility views recreate the nine former prototype tables.

## Canonical record catalogue

| Record type | Store | Subject / record identity | Meaning |
|---|---|---|---|
| `payroll.component` | L1 | component / numeric revision | Meaning of an earning, deduction or employer contribution |
| `payroll.earning` | L1 | earning / numeric revision | Employee earning entitlement, exact component version, minor-unit amount and effective months |
| `payroll.instruction` | L1 | instruction / numeric revision | Employee instruction including monthly/one-time cadence, applicability/expiry and exact component version |
| `payroll.draft` | L1 | draft / numeric revision | Exact employee/month snapshot identity, selected source versions, content hash and totals |
| `payroll.draft.control` | L1 | exact draft / numeric revision | Complete hold/cancel control state and actor/reason |
| `payroll.draft.review` | L1 | exact draft / review ID | Review bound to exact draft content and control context |
| `payroll.instruction.resolution` | L1 | exact draft / resolution ID | Instruction treatment and draft effects |
| `payroll.instruction.application` | L1 | instruction version / application ID | Permanent application and posted effects; consumption identity is stable instruction ID |
| `payroll.operation.receipt` | L1 | operation subject / receipt ID | Actor, retry identity, request hash, before/after and durable outcome |
| `payroll.employee.settings` | L2 | employee / numeric revision | Effective preferences and opaque reusable policy reference |

These are the simulation's proposed canonical payload contracts. The three ledger
names and separation of tables/record types are pinned; detailed schemas remain
prototype contracts to inspect in the row catalogue. Canonical keys keep the
approved `<type>:<subject>:<record>` grammar, with only literal colon/backslash
escaped inside identities, opaque case and numeric revision ordering.

One earning version represents an employee/component entitlement with explicit
effective-month bounds. A separate employer-contribution earning version uses a
component of that kind. Draft creation selects exact earning and instruction
versions; it must not create entitlement implicitly from an arbitrary salary
argument. Source intake/organizational policy is outside this simulation.
Instruction payload versions keep stable instruction identity and opaque external
version identity, full applicability bounds and amount; expiry is inclusive.

Draft metadata moves to L1; monetary lines remain in `payroll_draft_ledger`.
The prototype can retain a fixed revision-1 snapshot per distinct draft ID and
rebuild under a new draft ID. That is an explicit bounded choice, not a new ID
algorithm or an additional calculation concept. Employee/month groups related
payroll without prescribing ID generation. Committed status derives from durable
commit evidence; never mutate an immutable draft JSON row merely to set status.

## Employer liability entry types

- `obligation`: references the exact posted employer-liability entry and amount.
- `remittance`: records a payment to an authority and its durable challan/proof reference.
- `allocation`: references an obligation and remittance and applies a positive amount.

Outstanding is obligation amount minus allocations to it. A remittance alone
does not close an obligation. One remittance may fund several obligations; enforce
both obligation and remittance allocation caps. Distinct row types share the one
employer-liability ledger; do not embed a mutable list of settlements into a row.

## Integrity and indexing

KV rows retain `tenant`, `key`, `value`, `ts`, `state`. Availability is distinct
from approval/hold/commit. Latest disabled versions must not revive earlier
versions; historical references remain resolvable. Keep exact integer minor units
and INR fixtures. Money and contribution arithmetic are authoritative: employer
contribution increases gross and deductions equally, leaving net unchanged.

Use `(tenant,key)` identity for KV records and tenant-scoped exact references from
ledger rows. Enforce required record types/fields with targeted validation and
constraints; moving parent rows into JSON must not remove referential integrity.
Use partial/expression indexes for source subject/revision, opaque instruction
version lookup, employee/effective-month selection, draft identity, receipt replay
and stable instruction consumption. Keep relevant query fields near the JSON
root. Record query plans for actual simulation queries; do not claim scale gains.

Employee commit remains one transaction: validate exact draft/control/review,
append posted entries, instruction application/effects and durable outcome receipt
atomically. Hold/release and optional approval remain consumer-selected controls.
No cross-employee bulk writes or unrestricted L1 set/delete. Exact HTTP byte replay
and PostgreSQL authority/migration/concurrency/load remain explicit gaps.

## Complete mind map and evidence

The simulation must export all rows from its five tables, plus a catalogue of
all ten KV record types and five ledger row kinds (draft, posted, obligation,
remittance, allocation). Every catalogue entry has a meaning, owning table/layer,
identity, complete stored example, references, validation and query/index notes.
Every required kind must be witnessed; no placeholder examples count as coverage.

Use one connected E101 November example: Basic INR 30,000 plus HRA INR 20,000
(separate earning components and employee records), employer contribution INR 3,000 and monthly loan INR 2,000; gross INR 53,000, deductions INR 5,000,
net INR 48,000. Loan runs October 2026 through February 2027. Record the INR 3,000
obligation, INR 2,000 remittance with proof and allocation, leaving INR 1,000 due.
A separate one-time fixture proves stable consumption across instruction versions.
Include control history, review, receipts and L2 settings so their connections are
visible. Preserve expiry, retry/rollback/race and reference-failure regressions.

A readable Mermaid diagram and table catalogue explain the relationships. Full
JSON rows are evidence, not a replacement for the readable map. Retain source
revision/hashes, fixture timings, index plans, row counts and explicit gaps.
The older nine-table proof remains historical evidence bound to its original
source; it is not evidence for the new topology.

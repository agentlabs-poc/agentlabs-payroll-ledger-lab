# Python lab / Core contract reconciliation

Current implementation tracking: [Core hub #191](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/191). The historical comparison below describes this Python prototype. Component tombstone deletion is now defined and implemented in Core; category-preserving increase/decrease adjustments and immutable L3 revisions are approved for implementation. These Python features remain unimplemented; “awaiting confirmation” below is historical, not a current decision gate.

Authority: Core `docs/payroll-123-api-proposal.md` and `docs/payroll-123-canonical-records.md`, commit `f17321c` (19 method/path pairs). The Python lab exposes CLI/in-process primitives, not an HTTP server. Multiple CLI aliases do not add Core APIs.

## Operation map

Paths below have prefix `/api/v1/payroll`.

| Core method/path | Python primitive or read | Reconciliation |
|---|---|---|
| POST `/l1/components` | `Payroll.define_component` | Existing primitive |
| POST `/l1/components/{component_id}/disable` | `Payroll.disable_component` | Existing primitive |
| DELETE `/l1/components/{component_id}` | No primitive | Logical deletion contract awaiting confirmation |
| POST `/l1/employees/{employee_id}/earnings` | `Payroll.define_earning` | Existing primitive |
| POST `/l1/employees/{employee_id}/instructions` | `Payroll.add_instruction` | Existing primitive |
| POST `/l1/employees/{employee_id}/instructions/{instruction_id}/revisions` | `Payroll.add_instruction_version` | Existing primitive |
| POST `/l1/employees/{employee_id}/drafts/{draft_id}/controls` | `Payroll.set_draft_control` | Existing primitive |
| POST `/l1/employees/{employee_id}/drafts/{draft_id}/reviews` | `Payroll.review_draft` | Existing primitive |
| POST `/l1/records/query` | `RecordStore.get_l1`, `history_l1`, `current_l1`, `effective_l1_source` | Existing named reads; complete structured-query adapter not supplied |
| POST `/l1/ledgers/payroll_draft_ledger` | `Payroll.create_draft` | Implemented; `ledger-post payroll_draft_ledger` |
| GET `/l1/ledgers/payroll_draft_ledger` | CLI `ledger payroll_draft_ledger` | Existing employee/month read |
| POST `/l1/ledgers/payroll_ledger` | `Payroll.commit` | Implemented; `ledger-post payroll_ledger`; never writes ELR |
| GET `/l1/ledgers/payroll_ledger` | CLI `ledger payroll_ledger` | Existing employee/month read |
| POST `/l1/ledgers/payroll_employer_liability_ledger` | Canonical `Payroll.post_elr` dispatcher | Implemented: four closed entry kinds, one write boundary; CLI `liability post` |
| GET `/l1/ledgers/payroll_employer_liability_ledger` | CLI ledger read; `Payroll.elr_outstanding` | Implemented entries/outstanding views and employee ownership filter; production pagination/filter schema remains unpinned |
| POST `/l2/employees/{employee_id}/settings` | `RecordStore.put_l2_settings` | Existing versioned settings |
| POST `/l2/records/query` | `get_l2`, `current_l2_settings`, `effective_l2_settings` | Existing named reads; complete structured-query adapter not supplied |
| POST `/l3/records` | No primitive | Mutation/revision choice awaiting confirmation |
| POST `/l3/records/query` | No primitive | Generic L3 storage boundary, no consumer workflow logic |

## Explicit limits

- L1/L2 record tables now persist `key1`–`key10`. Used slots are nonempty; unused trailing slots are empty strings. The canonical serialized `key` is a virtual generated projection, not independently stored or writable. The existing full-tuple unique index serves the tested prefix query.
- SQLite connections must register the deterministic `canonical_record_key` function; use `sqlite_lab.records.connect`. A plain external SQLite connection cannot evaluate the virtual key without that function. External JSON envelopes remain `tenant/key/value/ts/state`.
- ELR full reversal, replay, replacement obligations and effective balances are implemented on `feat/python-payroll-123`. Verification is recorded below.
- Core supplies L3 storage/access only. Consumer scripts continue to own selection, sequencing and organization policy.
- Prefix/Base36 Snowflake ID representation is accepted, but the epoch/worker/generator contract remains unimplemented. Existing supplied IDs remain readable; no claim of production-generated canonical IDs.
- Category-preserving payroll reductions remain a separate unresolved meaning; ELR reversals do not change posted payroll amounts.
- No Go changes, network server, multi-employee L1 write, or throughput claim is introduced by this reconciliation.

## Canonical ELR CLI body

Use the same entry-kind body described by Core:

```sh
./payroll-cli liability post --input reversal.json
```

```json
{
  "row_kind": "reversal",
  "entry_id": "liabilityentry_9do1sj396nff",
  "reversal_of_entry_id": "liabilityentry_9do1sj396nfe",
  "reason": "Allocation referenced the wrong obligation"
}
```

`liability reverse` is a natural alias accepting the same fields without
`row_kind`. Existing obligation/remittance/allocate aliases remain available.
The canonical `liability post` requires the closed fields for its selected kind;
amount and scope are derived for reversals. No bulk entry body is accepted.

For a historical demo database, use a fresh `--db` path. The current-schema reset
still works; neither connect nor reset silently converts an older schema.

## Ledger command shape

```sh
./payroll-cli ledger-post payroll_draft_ledger --input draft.json
./payroll-cli ledger-post payroll_ledger --input commit.json
./payroll-cli ledger-post payroll_employer_liability_ledger --input entry.json
./payroll-cli ledger payroll_employer_liability_ledger --view outstanding --employee E101
```

Full canonical table names and the existing `draft`, `payroll`, `liability`
aliases are accepted. An employer-wide remittance has no employee owner;
employee filtering follows obligations through their exact posted payable,
including allocation/reversal references. ELR `--month` retains its existing
`reporting_period` meaning; it is not silently renamed to payroll month.

The lab still has five physical tables until the L3 mutation/namespace contract
is settled. Component DELETE is also still unsupported. These are three of the
19 Core method/path contracts, not hidden extra operations. No production HTTP
service, permission integration or complete query/pagination schema is claimed.

## Verification — 2026-09-09

- Full Python suite: **73 tests passed** (`python3 -m unittest discover -s sqlite_lab -p 'test_*.py' -q`).
- Proof catalogue: **16/16 declared record/ledger kinds**, including an actual reversal and replacement allocation. This is kind coverage, not complete production-contract certification.
- Fresh natural CLI walkthrough with `--settle`: completed settings/sources, draft, commit, obligations, remittances and allocations. Employee outstanding view returned five obligations with total outstanding zero.
- Key-column prefix lookup and effective-obligation lookup use the expected existing/replacement indexes under `EXPLAIN QUERY PLAN`; no throughput claim.
- SQL `INSERT OR REPLACE` cannot bypass immutable-row guards on supported connections; foreign keys and recursive triggers are enabled and verified.
- `git diff --check` passed. No load test or Go changes.

Local walkthrough evidence: `/tmp/payroll-123-final.6kpe4h/` (disposable; not committed).

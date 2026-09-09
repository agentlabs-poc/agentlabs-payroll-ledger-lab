# Python/Core payroll reconciliation

**Goal:** Bring the executable Python/SQLite lab into line with the accepted Core payroll 123 contract, preserving natural CLI commands and consumer-owned L3 composition.

**Authority:** Core `docs/payroll-123-api-proposal.md` and `docs/payroll-123-canonical-records.md` at `f17321c`. These describe 19 HTTP method/path contracts, not 19 existing Python functions. No HTTP server or Go implementation is part of this work.

**Architecture:** Three immutable monetary ledgers; canonical L1/L2 records and generic L3 storage. CLI calls individual in-process domain/storage operations. No L1 bulk writes, automatic payroll-to-ELR orchestration, or company-specific policy.

## Checkpoints

- [x] ELR: implement canonical single-entry dispatch and full reversal, same-ID replay, dependency ordering, replacement obligation uniqueness, and effective balances. Files: `sqlite_lab/payroll.py`, ELR section of `schema.sql`, `test_elr_reversals.py`.
- [x] Record storage: persist decoded `key1` through `key10`, preserve external canonical key/JSON and exact references. Use nonempty used slots and empty unused trailing slots. A virtual serialized key can retain existing query/FK compatibility without storing a second identity. Files: `records.py`, record-store section of `schema.sql`, focused storage tests.
- [ ] L3/component deletion: obtain the material mutation decisions before implementing dependent behavior. L3 logic remains external. Update the contract with the accepted decisions.
- [ ] CLI reconciliation: reuse named primitives; add the canonical ELR body entry point and six-table storage access. Preserve useful natural commands. Publish an exact Core route-to-Python-operation matrix; mark any undecided contract unsupported instead of inventing it.
- [x] Verification: existing 58-test baseline, focused reversal/key/layer cases, natural CLI walkthrough against a fresh disposable database. No load test or production changes.

## Proof and compatibility limits

Existing databases must not be silently reset or migrated. The revised prototype uses a fresh database and rejects incompatible schemas. No user benchmark database is touched.

Generic L3 mutation and component DELETE were open in the source contract; questions are pending. Snowflake epoch/worker coordination is also unpinned. Preserve supplied IDs and label any remaining generator gap; do not claim complete compatibility on the strength of a route count.

The six-table target and identity columns are architectural requirements, not a throughput promise. Record actual validation and remaining gaps here before completion.

## Completed checkpoint

ELR, L1/L2 physical key columns, canonical ledger CLI adapters and the 19-contract
operation map are complete. Full suite: 73 tests pass; fresh CLI settlement
walkthrough passes; proof catalogue contains 16/16 declared kinds.

L3 storage/write semantics and component deletion remain pending the requested
user choices; no implicit policy was implemented. Production query/pagination,
permissions and Snowflake generator coordination remain explicitly unproved.
This is a tested checkpoint, not a claim of complete Core conformance.

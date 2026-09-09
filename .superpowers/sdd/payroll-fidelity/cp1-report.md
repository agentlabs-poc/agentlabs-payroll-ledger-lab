# Payroll fidelity SQLite report

## Result

CP1 employee ownership and period-effective source selection are implemented in `3994a43`. The subsequently authorized minimal CP2 backend behavior is implemented in `5c6dff6`. No production HRMS code, dependency, batch API, L3 store, or sixth SQLite table was added.

The current generator executes 18 actual stages for E101 and E102 across October 2026 through March 2027 using exactly five tables.

## Interface decisions

- `canonical_key(record_type, *identity)` and `parse_key(key)` use one registered identity map and reject wrong arity, including old employee-less forms. Opaque colons and backslashes round-trip; dots remain literal.
- Employee-owned operations take `employee_id` explicitly. Local earning, instruction, and draft IDs remain unchanged and may repeat across employees.
- `history_l1` and `current_l1` accept the registered identity prefix. `effective_l1_source` selects the highest numeric revision with `effective_from <= payroll_month` within tenant, employee, and local source ID. Availability and expiry are checked only after that selection, so disabled or expired eligible revisions never resurrect older rows.
- Draft and posted stable monetary IDs include employee scope. Draft sources, controls, reviews, resolutions, applications, receipts, and emitted exact references retain employee-qualified ownership.
- Drafts store the full applicable `source_basis`. `commit(..., reconcile_sources=True)` compares it inside the existing write transaction. `fresh_review_required` independently chooses whether exact-content approval must also match the current control revision.
- `adjustment_of` is present only for a supplied one-time correction and must resolve to an earlier posted entry for the same tenant and employee at instruction, draft, and commit boundaries.
- Employer-liability rows retain employer, authority, currency, and optional reporting-period scope. Allocations require matching employer/authority/currency and may cross reporting periods. Commit returns `employer_liability_entry_ids` as a list.

## Files

- `sqlite_lab/records.py`
- `sqlite_lab/payroll.py`
- `sqlite_lab/schema.sql`
- `sqlite_lab/test_records.py`
- `sqlite_lab/test_payroll.py`

The demo/export worker owns `sqlite_lab/demo.py`, `sqlite_lab/prove.py`, `sqlite_lab/test_demo.py`, and `public/canonical-flow.json` after the explicit handoff.

## Validation

- Baseline: `python3 -m unittest discover -s sqlite_lab -p 'test_*.py' -v` — 42 tests passed.
- RED: `python3 -m unittest sqlite_lab.test_records.RecordStoreTest.test_employee_owned_keys_require_the_registered_owner_arity sqlite_lab.test_payroll.PayrollTest.test_two_employees_can_reuse_local_source_and_draft_ids sqlite_lab.test_payroll.PayrollTest.test_cross_owner_sources_and_draft_operations_are_rejected sqlite_lab.test_payroll.PayrollTest.test_future_source_revision_applies_only_from_its_month_without_disabled_fallback -v` — failed on old key arity, tenant-global collisions, missing explicit operation scope, and future revision selection as intended.
- GREEN: the same four-test command — 4 tests passed.
- Owned compatibility check: `python3 -m unittest sqlite_lab.test_records sqlite_lab.test_payroll.PayrollTest -v` — 37 tests passed.
- Minimal CP2 compatibility check: `python3 -m unittest sqlite_lab.test_payroll.PayrollTest.test_connected_e101_totals_include_contribution_and_loan sqlite_lab.test_payroll.PayrollTest.test_hold_release_optional_exact_review_and_immutable_draft sqlite_lab.test_payroll.PayrollTest.test_elr_one_remittance_spans_obligations_and_caps -v` — 3 tests passed.
- Actual generator: `python3 -m sqlite_lab.demo --output /tmp/payroll-fidelity-current.json` — succeeded; 18 stages, 2 employees, 6 months, 5 tables.
- Compile: `python3 -m py_compile sqlite_lab/records.py sqlite_lab/payroll.py sqlite_lab/test_records.py sqlite_lab/test_payroll.py sqlite_lab/demo.py sqlite_lab/prove.py sqlite_lab/test_demo.py` — passed.

No push was performed.

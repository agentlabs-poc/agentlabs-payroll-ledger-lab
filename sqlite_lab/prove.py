"""Consumer-composed, measured journey for the SQLite payroll proof."""

from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import tempfile
import time
from pathlib import Path

from .payroll import Conflict, Payroll
from .records import connect


TABLES = [
    "payroll_l1_records", "payroll_l2_records", "payroll_instructions",
    "payroll_instruction_versions", "payroll_calculations",
    "payroll_calculation_revisions", "payroll_draft_entries",
    "payroll_ledger_entries", "payroll_statutory_obligations",
    "payroll_statutory_remittances", "payroll_statutory_allocations",
]


def _stage(timings, name, operation):
    started = time.perf_counter_ns()
    result = operation()
    timings[name] = round((time.perf_counter_ns() - started) / 1_000_000, 3)
    return result


def _plan(connection, sql, parameters=()):
    return [row[3] for row in connection.execute("EXPLAIN QUERY PLAN " + sql, parameters)]


def _run(database: Path):
    timings = {}
    connection = _stage(timings, "initialize", lambda: connect(database))
    payroll = Payroll(connection, "T1", "U7")

    def definitions_and_settings():
        payroll.define_component("SALARY", 1, "salary", "Salary", "earning", "IN")
        payroll.define_component("LOAN", 1, "loan", "Loan deduction", "deduction", "IN")
        payroll.define_component("EMPLOYER", 1, "employer", "Employer contribution", "employer_contribution", "IN")
        payroll.records.put_l2_settings("T1", {
            "schema_version": 1, "employee_id": "E101", "revision": 1,
            "effective_from": "2026-01", "policy_ref": {"id": "standard", "revision": 1},
            "payslip_locale": "en-IN",
        })
        payroll.records.put_l2_settings("T1", {
            "schema_version": 1, "employee_id": "E101", "revision": 2,
            "effective_from": "2027-01", "policy_ref": {"id": "standard", "revision": 1},
            "payslip_locale": "hi-IN",
        })
        payroll.add_instruction("I-LOAN", "IV-LOAN-1", 1, "E101", "LOAN", 200_000,
                                "monthly", "2026-10", "2027-02")
    _stage(timings, "definitions_and_settings", definitions_and_settings)

    november = _stage(timings, "draft_E101", lambda: payroll.create_draft(
        "CAL1", "D1", "E101", "2026-11", 5_000_000, ["IV-LOAN-1"]
    ))

    def control_review_commit():
        payroll.set_draft_control("D1", True, False, "consumer check", 1)
        payroll.set_draft_control("D1", False, False, "consumer release", 2)
        payroll.review_draft("D1", "R1", november["content_hash"], 3, "approved")
        return payroll.commit("D1", "commit-e101-nov26", 3, approval_required=True)
    commit = _stage(timings, "review_and_commit_E101", control_review_commit)

    def one_time_journey():
        payroll.add_instruction("I-ONCE", "IV-ONCE-1", 1, "E102", "LOAN", 10_000,
                                "one_time", "2026-11", "2026-11")
        draft = payroll.create_draft("CAL2", "D2", "E102", "2026-11", 100_000, ["IV-ONCE-1"])
        committed = payroll.commit("D2", "commit-e102-once", 1)
        payroll.add_instruction_version("I-ONCE", "IV-ONCE-2", 2, "LOAN", 10_000)
        payroll.create_draft("CAL3", "D3", "E102", "2026-11", 100_000, ["IV-ONCE-2"])
        rejected = False
        try:
            payroll.commit("D3", "commit-e102-once-again", 1)
        except Conflict:
            rejected = True
        return {"draft_net_minor": draft["net_minor"], "commit": committed,
                "second_version_consumption_rejected": rejected}
    one_time = _stage(timings, "one_time_consumption", one_time_journey)

    def employer_liability_journey():
        payroll.create_draft("CAL4", "D4", "E201", "2026-11", 0, [],
                             employer_contribution_minor=300_000)
        outcome = payroll.commit("D4", "commit-e201-contribution", 1)
        payroll.record_obligation("OB1", outcome["employer_liability_entry_id"], 300_000)
        before = payroll.elr_outstanding("OB1")
        payroll.record_remittance("REM1", 200_000)
        payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 200_000)
        after = payroll.elr_outstanding("OB1")
        return {"outstanding_before_remittance_minor": before,
                "outstanding_after_allocation_minor": after}
    elr = _stage(timings, "employer_liability", employer_liability_journey)

    row_counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                  for table in TABLES}
    query_plans = {
        "component_history": _plan(connection,
            "SELECT key FROM payroll_l1_records WHERE tenant=? "
            "AND key LIKE 'payroll.component:%' AND json_extract(value,'$.component_id')=? "
            "ORDER BY CAST(json_extract(value,'$.revision') AS INTEGER) DESC",
            ("T1", "LOAN")),
        "effective_employee_settings": _plan(connection,
            "SELECT key FROM payroll_l2_records WHERE tenant=? "
            "AND key LIKE 'payroll.employee.settings:%' "
            "AND json_extract(value,'$.employee_id')=? AND json_extract(value,'$.effective_from')<=? "
            "ORDER BY json_extract(value,'$.effective_from') DESC, "
            "CAST(json_extract(value,'$.revision') AS INTEGER) DESC LIMIT 1",
            ("T1", "E101", "2026-11")),
        "instruction_application_reverse_lookup": _plan(connection,
            "SELECT key FROM payroll_l1_records WHERE tenant=? "
            "AND key LIKE 'payroll.instruction.application:%' "
            "AND json_extract(value,'$.instruction_id')=? "
            "AND json_extract(value,'$.employee_id')=? AND json_extract(value,'$.payroll_month')=?",
            ("T1", "I-LOAN", "E101", "2026-11")),
        "operation_replay": _plan(connection,
            "SELECT key FROM payroll_l1_records WHERE tenant=? "
            "AND key LIKE 'payroll.operation.receipt:%' "
            "AND json_extract(value,'$.executor')=? AND json_extract(value,'$.operation')=? "
            "AND json_extract(value,'$.subject_id')=? AND json_extract(value,'$.idempotency_key')=?",
            ("T1", "U7", "payroll.commit", "D1", "commit-e101-nov26")),
    }
    page_size = connection.execute("PRAGMA page_size").fetchone()[0]
    page_count = connection.execute("PRAGMA page_count").fetchone()[0]
    try:
        index_bytes = connection.execute(
            "SELECT COALESCE(SUM(pgsize),0) FROM dbstat WHERE name IN "
            "(SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%')"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        index_bytes = None

    def evidence_keys(record_type):
        return [row[0] for row in connection.execute(
            "SELECT key FROM payroll_l1_records WHERE key LIKE ? ORDER BY key", (record_type + ":%",)
        )]
    def receipt_keys(operation_prefix):
        return [row[0] for row in connection.execute(
            "SELECT key FROM payroll_l1_records WHERE key LIKE 'payroll.operation.receipt:%' "
            "AND json_extract(value,'$.operation') LIKE ? ORDER BY key",
            (operation_prefix + "%",),
        )]
    components = evidence_keys("payroll.component")
    controls = evidence_keys("payroll.draft.control")
    reviews = evidence_keys("payroll.draft.review")
    resolutions = evidence_keys("payroll.instruction.resolution")
    applications = evidence_keys("payroll.instruction.application")
    receipts = evidence_keys("payroll.operation.receipt")
    commit_receipts = receipt_keys("payroll.commit")
    instruction_receipts = receipt_keys("payroll.instruction.")
    role_mapping = [
        {"role": "payroll_fields", "status": "witnessed", "evidence": components},
        {"role": "payroll_component_versions", "status": "witnessed", "evidence": components},
        {"role": "payroll_calculation_candidates", "status": "witnessed", "evidence": ["payroll_calculation_revisions:D1.content_hash+candidate_identity"]},
        {"role": "payroll_draft_controls", "status": "witnessed", "evidence": controls},
        {"role": "payroll_draft_control_events", "status": "witnessed", "evidence": controls[:3]},
        {"role": "payroll_employee_candidate_reviews", "status": "witnessed", "evidence": reviews},
        {"role": "payroll_employee_finalization_receipts", "status": "witnessed", "evidence": commit_receipts},
        {"role": "payroll_instruction_applications", "status": "witnessed", "evidence": applications},
        {"role": "payroll_instruction_application_effects", "status": "witnessed", "evidence": applications},
        {"role": "payroll_candidate_instruction_resolutions", "status": "witnessed", "evidence": resolutions},
        {"role": "payroll_candidate_instruction_resolution_links", "status": "witnessed", "evidence": resolutions},
        {"role": "payroll_entry_batches", "status": "witnessed_combined", "evidence": commit_receipts,
         "limit": "only one-employee commit entry-operation evidence is exercised"},
        {"role": "payroll_candidate_batches", "status": "witnessed_combined", "evidence": ["D1 content hash", *commit_receipts],
         "limit": "no bulk or mutable candidate-batch resource"},
        {"role": "payroll_source_authority_actions", "status": "witnessed", "evidence": instruction_receipts,
         "limit": "instruction create/version actor and before/after evidence only; no upstream source tracing or deprecated generic facts"},
        {"role": "payroll_http_idempotency", "status": "explicit_gap", "evidence": [],
         "gap": "domain receipt replay is witnessed; exact HTTP response replay requires a transport adapter"},
        {"role": "payroll_mutation_evidence", "status": "witnessed_combined", "evidence": receipts,
         "limit": "commit receipt contains executor and required before/after evidence"},
    ]
    result = {
        "scope": "SQLite lab proof; consumer composes the journey and owns any L3 persistence",
        "runtime": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version},
        "outcomes": {
            "E101_november": {"gross_minor": november["gross_minor"],
                                "deductions_minor": november["deductions_minor"],
                                "net_minor": november["net_minor"], "commit": commit},
            "one_time_fixture": one_time,
            "employer_liability_fixture": elr,
        },
        "timings_ms": timings,
        "row_counts": row_counts,
        "query_plans": query_plans,
        "storage": {"database_bytes": database.stat().st_size,
                    "page_size": page_size, "page_count": page_count,
                    "measured_index_bytes": index_bytes},
        "role_mapping": role_mapping,
        "gaps": [
            "PostgreSQL constraints, RLS, permissions and writer concurrency are unproved",
            "exact HTTP response replay and transport behavior are unimplemented",
            "platform-shared component definitions are unimplemented",
            "salary entitlement is an explicitly external fixture input",
            "policy_ref remains opaque; no auxiliary policy referent contract is proved",
        ],
    }
    connection.close()
    result["storage"]["database_bytes"] = database.stat().st_size
    return result


def run_proof(output_dir: Path | None = None):
    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix="payroll-sqlite-proof-") as directory:
            return _run(Path(directory) / "proof.sqlite3")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    database = output_dir / "proof.sqlite3"
    evidence = output_dir / "evidence.json"
    if database.exists() or evidence.exists():
        raise FileExistsError("refusing to reuse or overwrite proof evidence")
    result = _run(database)
    evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="retain proof.sqlite3 and evidence.json")
    args = parser.parse_args(argv)
    print(json.dumps(run_proof(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

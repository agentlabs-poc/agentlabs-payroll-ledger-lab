"""Run and export the complete three-ledger payroll simulation."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path
from .payroll import Conflict, Payroll
from .records import connect

TABLES = (
    "payroll_l1_records",
    "payroll_l2_records",
    "payroll_draft_ledger",
    "payroll_ledger",
    "payroll_employer_liability_ledger",
)
L1_TYPES = (
    "payroll.component",
    "payroll.earning",
    "payroll.instruction",
    "payroll.draft",
    "payroll.draft.control",
    "payroll.draft.review",
    "payroll.instruction.resolution",
    "payroll.instruction.application",
    "payroll.operation.receipt",
)
LEDGER_KINDS = (
    ("draft", "payroll_draft_ledger"),
    ("posted", "payroll_ledger"),
    ("obligation", "payroll_employer_liability_ledger"),
    ("remittance", "payroll_employer_liability_ledger"),
    ("allocation", "payroll_employer_liability_ledger"),
)

def _stage(timings, name, fn):
    start = time.perf_counter_ns()
    result = fn()
    timings[name] = round((time.perf_counter_ns() - start) / 1_000_000, 3)
    return result


def _plan(connection, sql, args=()):
    return [
        row[3]
        for row in connection.execute("EXPLAIN QUERY PLAN " + sql, args)
    ]


def _rows(connection, table):
    result = []
    for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid"):
        item = dict(row)
        if table in {"payroll_l1_records", "payroll_l2_records"}:
            item["value"] = json.loads(item["value"])
        result.append(item)
    return result


def _source_hashes():
    root = Path(__file__).parent
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in ("schema.sql", "records.py", "payroll.py", "prove.py")
    }


def _source_revision():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).parents[1],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None

def _catalogue(rows):
    meanings = {
        "payroll.component": "versioned payroll component meaning",
        "payroll.earning": "versioned employee earning entitlement",
        "payroll.instruction": "versioned employee earning/deduction instruction",
        "payroll.draft": "fixed employee/month draft metadata",
        "payroll.draft.control": "versioned hold/cancel control",
        "payroll.draft.review": "exact-content review evidence",
        "payroll.instruction.resolution": "draft effect resolution",
        "payroll.instruction.application": (
            "permanent posted instruction application"
        ),
        "payroll.operation.receipt": "durable actor/retry/outcome evidence",
        "payroll.employee.settings": (
            "effective L2 employee preferences and opaque policy reference"
        ),
        "draft": "immutable proposed monetary line",
        "posted": "immutable committed monetary line",
        "obligation": "posted employer-liability obligation",
        "remittance": "authority payment with proof",
        "allocation": "amount linking obligation and remittance",
    }
    entries = []
    for kind in L1_TYPES + ("payroll.employee.settings",):
        table = (
            "payroll_l2_records"
            if kind == "payroll.employee.settings"
            else "payroll_l1_records"
        )
        example = next(
            row for row in rows[table] if row["key"].startswith(kind + ":")
        )
        entries.append(
            {
                "kind": kind,
                "category": (
                    "L2 record" if table.endswith("l2_records") else "L1 record"
                ),
                "table": table,
                "layer": "L2" if table.endswith("l2_records") else "L1",
                "meaning": meanings[kind],
                "identity": "(tenant,key); canonical type:subject:record",
                "example": example,
                "references": (
                    "canonical keys in value are exact same-tenant references; "
                    "employee/actor/policy are external where present"
                ),
                "validation": (
                    "closed top-level prototype fields, key/payload identity, "
                    "targeted types/lifecycle"
                ),
                "indexed_queries": (
                    "exact key plus type-specific current/effective/replay access"
                ),
            }
        )
    for kind, table in LEDGER_KINDS:
        example = next(row for row in rows[table] if row["row_kind"] == kind)
        entries.append(
            {
                "kind": kind,
                "category": "ledger row",
                "table": table,
                "layer": "L1 ledger",
                "meaning": meanings[kind],
                "identity": "tenant plus table row identity",
                "example": example,
                "references": (
                    "exact tenant-scoped L1/ledger keys or external employee "
                    "identity"
                ),
                "validation": (
                    "immutable typed shape, integer minor units and "
                    "reference/cap checks"
                ),
                "indexed_queries": (
                    "exact identity, employee/month or allocation/outstanding lookup"
                ),
            }
        )
    return {"coverage": {"covered": len(entries), "required": 15}, "entries": entries}

def _run(database):
    timings = {}
    connection = _stage(timings, "initialize", lambda: connect(database))
    payroll = Payroll(connection, "T1", "U7")

    def setup():
        salary = payroll.define_component(
            "SALARY", 1, "salary", "Salary", "earning", "IN"
        )["key"]
        loan = payroll.define_component(
            "LOAN", 1, "loan", "Loan", "deduction", "IN"
        )["key"]
        employer = payroll.define_component(
            "EMPLOYER",
            1,
            "employer",
            "Employer contribution",
            "employer_contribution",
            "IN",
        )["key"]
        bonus = payroll.define_component(
            "BONUS", 1, "bonus", "Bonus", "earning", "IN"
        )["key"]
        salary_earning = payroll.define_earning(
            "EARN-SALARY", 1, "E101", salary, 5_000_000, "2026-01"
        )["key"]
        employer_earning = payroll.define_earning(
            "EARN-EMPLOYER", 1, "E101", employer, 300_000, "2026-01"
        )["key"]
        loan_key = payroll.add_instruction(
            "I-LOAN",
            "IV-LOAN-1",
            1,
            "E101",
            loan,
            200_000,
            "monthly",
            "2026-10",
            "2027-02",
        )["key"]
        bonus_key = payroll.add_instruction(
            "I-BONUS",
            "IV-BONUS-1",
            1,
            "E102",
            bonus,
            50_000,
            "one_time",
            "2026-11",
            "2026-11",
        )["key"]
        e102 = payroll.define_earning(
            "EARN-E102", 1, "E102", salary, 100_000, "2026-01"
        )["key"]
        payroll.records.put_l2_settings(
            "T1",
            {
                "schema_version": 1,
                "employee_id": "E101",
                "revision": 1,
                "effective_from": "2026-01",
                "policy_ref": {"id": "standard", "revision": 1},
                "payslip_locale": "en-IN",
            },
        )
        return salary_earning, employer_earning, loan_key, bonus_key, e102

    salary_earning, employer_earning, loan_key, bonus_key, e102 = _stage(
        timings, "sources", setup
    )
    draft = _stage(
        timings,
        "draft_E101",
        lambda: payroll.create_draft(
            "D1",
            "E101",
            "2026-11",
            [salary_earning, employer_earning],
            [loan_key],
        ),
    )

    def commit_e101():
        payroll.set_draft_control("D1", True, False, "consumer check", 1)
        payroll.set_draft_control("D1", False, False, "consumer release", 2)
        payroll.review_draft("D1", "R1", draft["content_hash"], 3, "approved")
        return payroll.commit("D1", "commit-e101", 3, True)

    committed = _stage(timings, "commit_E101", commit_e101)

    def one_time():
        one_time_draft = payroll.create_draft(
            "D2", "E102", "2026-11", [e102], [bonus_key]
        )
        first = payroll.commit("D2", "commit-e102", 1)
        first_instruction = payroll.records.get_l1("T1", bonus_key)["value"]
        second = payroll.add_instruction_version(
            "I-BONUS",
            "IV-BONUS-2",
            2,
            first_instruction["component_key"],
            50_000,
        )
        payroll.create_draft(
            "D3", "E102", "2026-11", [e102], [second["key"]]
        )
        rejected = False
        try:
            payroll.commit("D3", "commit-e102-again", 1)
        except Conflict:
            rejected = True
        return {
            "totals": {
                "gross_minor": one_time_draft["gross_minor"],
                "deductions_minor": one_time_draft["deductions_minor"],
                "net_minor": one_time_draft["net_minor"],
            },
            "second_version_rejected": rejected,
            "commit": first,
        }

    once = _stage(timings, "one_time", one_time)

    def settle():
        payroll.record_obligation(
            "OB1", committed["employer_liability_entry_id"], 300_000
        )
        payroll.record_remittance("REM1", 200_000, "challan:REM1")
        before = payroll.elr_outstanding("OB1")
        payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 200_000)
        return {
            "before_allocation_minor": before,
            "outstanding_minor": payroll.elr_outstanding("OB1"),
            "proof_ref": "challan:REM1",
        }

    elr = _stage(timings, "liability", settle)
    rows = {table: _rows(connection, table) for table in TABLES}
    catalog = _catalogue(rows)
    plans = {
        "earning_effective": _plan(
            connection,
            "SELECT key FROM payroll_l1_records "
            "WHERE tenant=? AND key LIKE 'payroll.earning:%' "
            "AND json_extract(value,'$.employee_id')=? "
            "AND json_extract(value,'$.effective_from')<=?",
            ("T1", "E101", "2026-11"),
        ),
        "instruction_version": _plan(
            connection,
            "SELECT key FROM payroll_l1_records "
            "WHERE tenant=? AND key LIKE 'payroll.instruction:%' "
            "AND json_extract(value,'$.version_id')=?",
            ("T1", "IV-LOAN-1"),
        ),
        "draft_employee_month": _plan(
            connection,
            "SELECT * FROM payroll_draft_ledger "
            "WHERE tenant=? AND employee_id=? AND payroll_month=?",
            ("T1", "E101", "2026-11"),
        ),
        "posted_employee_month": _plan(
            connection,
            "SELECT * FROM payroll_ledger "
            "WHERE tenant=? AND employee_id=? AND payroll_month=?",
            ("T1", "E101", "2026-11"),
        ),
        "elr_allocations": _plan(
            connection,
            "SELECT SUM(amount_minor) "
            "FROM payroll_employer_liability_ledger "
            "WHERE tenant=? AND row_kind='allocation' "
            "AND obligation_entry_id=?",
            ("T1", "OB1"),
        ),
        "instruction_application_reverse_lookup": _plan(
            connection,
            "SELECT key FROM payroll_l1_records "
            "WHERE tenant=? AND key LIKE 'payroll.instruction.application:%' "
            "AND json_extract(value,'$.instruction_id')=? "
            "AND json_extract(value,'$.employee_id')=? "
            "AND json_extract(value,'$.payroll_month')=?",
            ("T1", "I-LOAN", "E101", "2026-11"),
        ),
        "operation_replay": _plan(
            connection,
            "SELECT key FROM payroll_l1_records "
            "WHERE tenant=? AND key LIKE 'payroll.operation.receipt:%' "
            "AND json_extract(value,'$.executor')=? "
            "AND json_extract(value,'$.operation')=? "
            "AND json_extract(value,'$.subject_id')=? "
            "AND json_extract(value,'$.idempotency_key')=?",
            ("T1", "U7", "payroll.commit", "D1", "commit-e101"),
        ),
    }

    def keys(kind):
        return [
            row["key"]
            for row in rows["payroll_l1_records"]
            if row["key"].startswith(kind + ":")
        ]

    components = keys("payroll.component")
    drafts = keys("payroll.draft")
    controls = keys("payroll.draft.control")
    reviews = keys("payroll.draft.review")
    applications = keys("payroll.instruction.application")
    resolutions = keys("payroll.instruction.resolution")
    receipts = keys("payroll.operation.receipt")
    instruction_receipts = [
        row["key"]
        for row in rows["payroll_l1_records"]
        if row["key"].startswith("payroll.operation.receipt:")
        and row["value"]["operation"].startswith("payroll.instruction.")
    ]
    role_mapping = [
        {"role": "payroll_fields", "status": "witnessed", "evidence": components},
        {
            "role": "payroll_component_versions",
            "status": "witnessed",
            "evidence": components,
        },
        {
            "role": "payroll_calculation_candidates",
            "status": "witnessed_combined",
            "evidence": drafts,
        },
        {
            "role": "payroll_draft_controls",
            "status": "witnessed",
            "evidence": controls,
        },
        {
            "role": "payroll_draft_control_events",
            "status": "witnessed_combined",
            "evidence": controls,
        },
        {
            "role": "payroll_employee_candidate_reviews",
            "status": "witnessed",
            "evidence": reviews,
        },
        {
            "role": "payroll_employee_finalization_receipts",
            "status": "witnessed",
            "evidence": receipts,
        },
        {
            "role": "payroll_instruction_applications",
            "status": "witnessed",
            "evidence": applications,
        },
        {
            "role": "payroll_instruction_application_effects",
            "status": "witnessed_combined",
            "evidence": applications,
        },
        {
            "role": "payroll_candidate_instruction_resolutions",
            "status": "witnessed",
            "evidence": resolutions,
        },
        {
            "role": "payroll_candidate_instruction_resolution_links",
            "status": "witnessed_combined",
            "evidence": resolutions,
        },
        {
            "role": "payroll_entry_batches",
            "status": "witnessed_combined",
            "evidence": receipts,
        },
        {
            "role": "payroll_candidate_batches",
            "status": "witnessed_combined",
            "evidence": drafts + receipts,
        },
        {
            "role": "payroll_source_authority_actions",
            "status": "witnessed_combined",
            "evidence": instruction_receipts,
        },
        {
            "role": "payroll_http_idempotency",
            "status": "explicit_gap",
            "evidence": [],
            "gap": "exact transport response replay unimplemented",
        },
        {
            "role": "payroll_mutation_evidence",
            "status": "witnessed_combined",
            "evidence": receipts,
        },
    ]
    replacement = {
        name: "payroll_l1_records"
        for name in (
            "payroll_instructions",
            "payroll_instruction_versions",
            "payroll_calculations",
            "payroll_calculation_revisions",
        )
    }
    replacement.update(
        {
            "payroll_draft_entries": "payroll_draft_ledger",
            "payroll_ledger_entries": "payroll_ledger",
            "payroll_statutory_obligations": (
                "payroll_employer_liability_ledger:obligation"
            ),
            "payroll_statutory_remittances": (
                "payroll_employer_liability_ledger:remittance"
            ),
            "payroll_statutory_allocations": (
                "payroll_employer_liability_ledger:allocation"
            ),
        }
    )
    page_size = connection.execute("PRAGMA page_size").fetchone()[0]
    pages = connection.execute("PRAGMA page_count").fetchone()[0]
    try:
        index_bytes = connection.execute(
            "SELECT COALESCE(SUM(pgsize),0) FROM dbstat "
            "WHERE name IN (SELECT name FROM sqlite_master "
            "WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%')"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        index_bytes = None
    result = {
        "scope": "SQLite three-ledger simulation; no L3",
        "runtime": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "source_revision": _source_revision(),
        "source_hashes": _source_hashes(),
        "outcomes": {
            "E101_november": {
                "totals": {
                    key: draft[key]
                    for key in ("gross_minor", "deductions_minor", "net_minor")
                },
                "commit": committed,
            },
            "one_time_earning": once,
            "employer_liability": elr,
        },
        "timings_ms": timings,
        "row_counts": {key: len(value) for key, value in rows.items()},
        "query_plans": plans,
        "storage": {
            "page_size": page_size,
            "page_count": pages,
            "database_bytes": database.stat().st_size,
            "measured_index_bytes": index_bytes,
        },
        "catalogue_coverage": catalog["coverage"],
        "role_mapping": role_mapping,
        "former_nine_table_replacement": replacement,
        "gaps": [
            "exact HTTP response replay",
            "PostgreSQL authority, migration, concurrency and load",
            "external employee, actor and policy referents",
        ],
    }
    connection.close()
    result["storage"]["database_bytes"] = database.stat().st_size
    return result,rows,catalog

def run_proof(output_dir=None):
    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix="payroll-three-ledger-") as directory:
            return _run(Path(directory) / "proof.sqlite3")[0]
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    names = (
        "proof.sqlite3",
        "evidence.json",
        "canonical-rows.json",
        "canonical-catalog.json",
    )
    if any((root / name).exists() for name in names):
        raise FileExistsError("refusing to overwrite simulation evidence")
    result, rows, catalog = _run(root / "proof.sqlite3")
    for name, data in (
        ("evidence.json", result),
        ("canonical-rows.json", rows),
        ("canonical-catalog.json", catalog),
    ):
        (root / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n"
        )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(run_proof(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

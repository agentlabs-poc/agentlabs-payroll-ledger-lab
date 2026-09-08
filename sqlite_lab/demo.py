"""Export the connected canonical payroll journey as actual SQLite snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

from .payroll import Payroll, PayrollError
from .records import RecordStore, connect


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


def _rows(connection: sqlite3.Connection, table: str) -> list[dict]:
    rows = [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")]
    if table in {"payroll_l1_records", "payroll_l2_records"}:
        for row in rows:
            row["value"] = json.loads(row["value"])
    return rows


def _summary(connection: sqlite3.Connection) -> dict:
    draft = connection.execute(
        "SELECT value FROM payroll_l1_records WHERE key='payroll.draft:D1:1'"
    ).fetchone()
    payroll = {"gross_minor": 0, "deductions_minor": 0, "net_minor": 0}
    if draft:
        value = json.loads(draft[0])
        payroll = {key: value[key] for key in payroll}
    liability = {"due_minor": 0, "paid_minor": 0, "allocated_minor": 0, "outstanding_minor": 0}
    for row in connection.execute(
        "SELECT row_kind, COALESCE(SUM(amount_minor),0) amount FROM payroll_employer_liability_ledger GROUP BY row_kind"
    ):
        if row["row_kind"] == "obligation":
            liability["due_minor"] = row["amount"]
        elif row["row_kind"] == "remittance":
            liability["paid_minor"] = row["amount"]
        else:
            liability["allocated_minor"] = row["amount"]
    liability["outstanding_minor"] = liability["due_minor"] - liability["allocated_minor"]
    return {"payroll": payroll, "liability": liability}


def build_demo() -> dict:
    root = Path(__file__).parent
    with tempfile.TemporaryDirectory() as directory:
        connection = connect(Path(directory) / "canonical-demo.db")
        payroll = Payroll(connection, "T1", "payroll-admin")
        stages = []

        def capture(stage_id: str, title: str, explanation: str, outcome: dict | None = None) -> None:
            stages.append({
                "id": stage_id,
                "title": title,
                "explanation": explanation,
                "outcome": outcome or {"status": "observed"},
                "summary": _summary(connection),
                "tables": {table: _rows(connection, table) for table in TABLES},
            })

        capture("empty", "Empty database", "A fresh schema has no payroll rows.")
        salary = payroll.define_component("SALARY", 1, "salary", "Salary", "earning", "IN")["key"]
        employer = payroll.define_component("EMPLOYER", 1, "employer", "Employer contribution", "employer_contribution", "IN")["key"]
        loan = payroll.define_component("LOAN", 1, "loan", "Loan recovery", "deduction", "IN")["key"]
        salary_earning = payroll.define_earning("EARN-SALARY", 1, "E101", salary, 5_000_000, "2026-01")["key"]
        employer_earning = payroll.define_earning("EARN-EMPLOYER", 1, "E101", employer, 300_000, "2026-01")["key"]
        instruction = payroll.add_instruction("I-LOAN", "opaque\\loan-nov-2026", 1, "E101", loan, 200_000, "monthly", "2026-10", "2027-02")
        RecordStore(connection).put_l2_settings("T1", {
            "schema_version": 1,
            "employee_id": "E101",
            "revision": 1,
            "effective_from": "2026-01",
            "policy_ref": {"id": "INDIA-PAYROLL", "revision": 1},
            "payslip_locale": "en-IN",
        })
        connection.commit()
        capture("sources", "Source records", "Components define meaning; earnings are entitlements, while instructions are monthly or one-time inputs. L2 settings are auxiliary.")

        draft = payroll.create_draft(
            "D1", "E101", "2026-11", [salary_earning, employer_earning], [instruction["value"]["version_id"]]
        )
        capture("draft", "Draft snapshot", "payroll.draft fixes source versions, content hash, and totals; payroll_draft_ledger holds its monetary effects. Resolution records describe candidate instruction treatment.")

        payroll.set_draft_control("D1", True, False, "payroll review hold", 1)
        try:
            payroll.commit("D1", "held-attempt", 2)
        except PayrollError as error:
            held_outcome = {"status": "rejected", "reason": str(error)}
        capture("held", "Commit blocked by hold", "The hold is a new payroll.draft.control revision. The rejected commit appends no monetary rows, application, or receipt.", held_outcome)

        payroll.set_draft_control("D1", False, False, "released for posting", 2)
        capture("released", "Hold released", "A later control revision releases the same immutable draft.")
        payroll.review_draft("D1", "REV1", draft["content_hash"], 3, "approved")
        capture("reviewed", "Optional exact review", "The review binds this draft content hash and control revision. This journey records it, although commit policy does not require approval.", {"status": "approved", "optional": True})

        committed = payroll.commit("D1", "commit-nov-2026", 3, approval_required=False)
        capture("committed", "Committed atomically", "Posted entries, the instruction application, and the durable payroll.commit receipt appear together. The draft and its resolution stay unchanged.", {**committed, "approval_required": False})
        payroll.record_obligation("OB1", committed["employer_liability_entry_id"], 300_000)
        capture("obligation", "Employer obligation", "The obligation references the exact posted employer-liability entry and establishes INR 3,000 due.")
        payroll.record_remittance("REM1", 200_000, "challan:IN-2026-11-001")
        capture("remittance", "Challan-backed remittance", "The remittance proves INR 2,000 was paid. It does not itself reduce the obligation's outstanding amount.")
        payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 200_000)
        capture("allocation", "Payment allocated", "Allocation connects the remittance to the obligation, reducing outstanding liability from INR 3,000 to INR 1,000.")
        connection.close()

    return {
        "source": {
            "revision": "canonical-three-ledger-v1",
            "sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ("demo.py", "schema.sql", "records.py", "payroll.py")},
        },
        "fixture": {"tenant": "T1", "employee_id": "E101", "payroll_month": "2026-11", "currency": "INR", "unit": "minor"},
        "tables": list(TABLES),
        "catalogue": {"record_types": [*L1_TYPES, "payroll.employee.settings"], "ledger_kinds": ["draft", "posted", "obligation", "remittance", "allocation"]},
        "stages": stages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_demo(), indent=2) + "\n")


if __name__ == "__main__":
    main()

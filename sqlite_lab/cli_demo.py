"""Run one retained payroll walkthrough through separate CLI processes."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.db.exists():
        parser.error("--db must name a fresh path")

    root = Path(__file__).parents[1]
    base = [sys.executable, "-m", "sqlite_lab.cli", "--db", str(args.db), "--tenant", "T1", "--actor", "payroll-admin"]
    timings = []
    walkthrough_started = time.perf_counter_ns()

    def invoke(arguments, payload=None, output_format="json"):
        command = [*base]
        if output_format != "json":
            command += ["--format", output_format]
        command += arguments
        started = time.perf_counter_ns()
        result = subprocess.run(
            command, cwd=root, text=True, input=None if payload is None else json.dumps(payload),
            capture_output=True,
        )
        timings.append({"command": " ".join(arguments[:2]), "elapsed_ms": round((time.perf_counter_ns() - started) / 1_000_000, 3)})
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        return json.loads(result.stdout) if output_format == "json" else result.stdout.rstrip()

    def l1(operation, **payload):
        return invoke(["l1", operation, "--input", "-"], payload)

    def rejected_l1(operation, **payload):
        try:
            l1(operation, **payload)
        except RuntimeError as error:
            return json.loads(str(error))
        raise AssertionError("operation should have been rejected")

    invoke(["init"])
    components = {}
    for component_id, code, kind in (
        ("BASIC", "BASIC", "earning"),
        ("HRA", "HRA", "earning"),
        ("EMPLOYER", "EMPLOYER", "employer_contribution"),
        ("LOAN", "LOAN", "deduction"),
        ("BONUS", "BONUS", "earning"),
    ):
        components[code] = l1(
            "define_component", component_id=component_id, revision=1, code=code,
            label=code.title(), kind=kind, country_code="IN",
        )["key"]

    employee = "E101"
    earnings = [
        l1("define_earning", earning_id="earning_9do1sj396nf9", revision=1, employee_id=employee, component_key=components["BASIC"], amount_minor=3_000_000, effective_from="2026-11")["key"],
        l1("define_earning", earning_id="earning_9do1sj396nfa", revision=1, employee_id=employee, component_key=components["HRA"], amount_minor=2_000_000, effective_from="2026-11")["key"],
        l1("define_earning", earning_id="earning_9do1sj396nfb", revision=1, employee_id=employee, component_key=components["EMPLOYER"], amount_minor=300_000, effective_from="2026-11")["key"],
    ]
    loan = l1(
        "add_instruction", instruction_id="instruction_9do1sj396nfc", version_id="LOAN-V1", revision=1,
        employee_id=employee, component_key=components["LOAN"], amount_minor=200_000,
        cadence="monthly", start_month="2026-11", end_month="2027-03",
    )
    bonus = l1(
        "add_instruction", instruction_id="instruction_9do1sj396nfd", version_id="BONUS-V1", revision=1,
        employee_id=employee, component_key=components["BONUS"], amount_minor=500_000,
        cadence="one_time", start_month="2026-11", end_month="2026-11",
    )
    invoke(["l2", "put_l2_settings", "--input", "-"], {
        "value": {"schema_version": 1, "employee_id": employee, "revision": 1, "effective_from": "2026-11", "policy_ref": {"id": "POLICY-DEMO", "revision": 1}, "payslip_locale": "en-IN"}
    })

    draft_id = "draft_9do1sj396nfe"
    draft = l1(
        "create_draft", draft_id=draft_id, employee_id=employee, payroll_month="2026-11",
        earning_keys=earnings, instruction_version_ids=[loan["value"]["version_id"], bonus["value"]["version_id"]],
    )
    l1("set_draft_control", draft_id=draft_id, employee_id=employee, held=True, cancelled=False, reason="manager hold", expected_revision=1)
    held = rejected_l1("commit", draft_id=draft_id, employee_id=employee, idempotency_key="held-probe", expected_control_revision=2)
    assert held["message"] == "draft held or cancelled"
    l1("set_draft_control", draft_id=draft_id, employee_id=employee, held=False, cancelled=False, reason="manager release", expected_revision=2)
    l1("review_draft", draft_id=draft_id, employee_id=employee, review_id="review_9do1sj396nff", content_hash=draft["content_hash"], control_revision=3, decision="approved")
    commit_input = {"draft_id": draft_id, "employee_id": employee, "idempotency_key": "commit-demo-1", "expected_control_revision": 3, "approval_required": True, "fresh_review_required": True}
    committed = l1("commit", **commit_input)
    replayed = l1("commit", **commit_input)
    assert committed == replayed and committed["status"] == "committed"
    assert l1("instruction_application", instruction_id="instruction_9do1sj396nfc", employee_id=employee, payroll_month="2026-11")
    assert l1("instruction_application", instruction_id="instruction_9do1sj396nfd", employee_id=employee, payroll_month="2026-11")

    liability_id = committed["employer_liability_entry_ids"][0]
    obligation_id, remittance_id, allocation_id = "liabilityentry_9do1sj396nfg", "liabilityentry_9do1sj396nfh", "liabilityentry_9do1sj396nfi"
    l1("record_obligation", entry_id=obligation_id, posted_liability_entry_id=liability_id, amount_minor=300_000, employer_id="EMPLOYER1", authority_id="AUTHORITY-A")
    l1("record_remittance", entry_id=remittance_id, amount_minor=300_000, proof_ref="challan:demo-1", employer_id="EMPLOYER1", authority_id="AUTHORITY-A", reporting_period="2026-11")
    partial_outstanding = l1("elr_outstanding", obligation_id=obligation_id)
    assert partial_outstanding == 300_000
    l1("allocate_remittance", entry_id=allocation_id, obligation_id=obligation_id, remittance_id=remittance_id, amount_minor=300_000)
    assert l1("elr_outstanding", obligation_id=obligation_id) == 0
    assert (draft["gross_minor"], draft["deductions_minor"], draft["net_minor"]) == (5_800_000, 500_000, 5_300_000)

    print(json.dumps({"database": str(args.db), "held_commit_rejected": True, "commit_replay_equal": True, "totals": {key: draft[key] for key in ("gross_minor", "deductions_minor", "net_minor")}, "outstanding_before_allocation_minor": partial_outstanding, "outstanding_minor": 0, "elapsed_ms": round((time.perf_counter_ns() - walkthrough_started) / 1_000_000, 3), "commands": timings}, indent=2, sort_keys=True))
    for ledger in ("payroll_draft_ledger", "payroll_ledger", "payroll_employer_liability_ledger"):
        print(f"\n{ledger}")
        print(invoke(["ledger", ledger], output_format="table"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

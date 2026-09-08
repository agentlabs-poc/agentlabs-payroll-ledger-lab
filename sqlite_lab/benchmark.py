"""Benchmark one Karnataka payroll month through the public CLI dispatcher."""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import math
import os
import platform
import resource
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from . import cli


MONTH = "2026-11"
TENANT = "T1"
ACTOR = "payroll-admin"
BASE_ID = 1_234_567_890_123_456_789
GROSS_MINOR = 15_680_000
DEDUCTIONS_MINOR = 1_845_334
NET_MINOR = 13_834_666
PAYABLE_MINOR = 1_645_334
COMPONENTS = (
    ("BASIC", "earning", False), ("HRA", "earning", False),
    ("SPECIAL_ALLOWANCE", "earning", False),
    ("EPF_EMPLOYEE", "deduction", True),
    ("EPF_EMPLOYER", "employer_contribution", False),
    ("EPS_EMPLOYER", "employer_contribution", False),
    ("PROFESSIONAL_TAX_KA", "deduction", True),
    ("INCOME_TAX_TDS", "deduction", True),
    ("LOAN", "deduction", False), ("BONUS", "earning", False),
)


def _base36(value):
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    while value:
        value, remainder = divmod(value, 36)
        result = digits[remainder] + result
    return result or "0"


def _identifier(prefix, seed):
    # Deterministic benchmark fixture identity, not a production ID generator.
    return f"{prefix}_{_base36(seed)}"


def _atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _percentiles(values):
    ordered = sorted(values)
    return {
        "min": round(ordered[0], 3),
        "p50": round(ordered[math.ceil(len(ordered) * .50) - 1], 3),
        "p95": round(ordered[math.ceil(len(ordered) * .95) - 1], 3),
        "max": round(ordered[-1], 3),
    }


def _host():
    cpu_model = None
    memory_total = None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                memory_total = int(line.split()[1]) * 1024
                break
    except OSError:
        pass
    return {
        "cpu_count": os.cpu_count(), "cpu_model": cpu_model,
        "memory_total_bytes": memory_total, "uname": platform.uname()._asdict(),
    }


class Driver:
    def __init__(self, mode, root, config):
        self.mode = mode
        self.root = root
        self.config = config
        self.environment = {
            **os.environ, "PATH": str(root) + os.pathsep + os.environ.get("PATH", ""),
            "PAYROLL_CLI_CONFIG": str(config),
        }
        self.commands = {}

    def invoke(self, arguments, payload=None):
        started = time.perf_counter_ns()
        if self.mode == "subprocess":
            result = subprocess.run(
                ["payroll-cli", *arguments], cwd=self.root, env=self.environment,
                text=True, input=None if payload is None else json.dumps(payload),
                capture_output=True,
            )
            status, output, error = result.returncode, result.stdout, result.stderr
        else:
            stdout, stderr = io.StringIO(), io.StringIO()
            previous_stdin = sys.stdin
            previous_config = os.environ.get("PAYROLL_CLI_CONFIG")
            sys.stdin = io.StringIO("" if payload is None else json.dumps(payload))
            os.environ["PAYROLL_CLI_CONFIG"] = str(self.config)
            try:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    status = cli.main(arguments)
            finally:
                sys.stdin = previous_stdin
                if previous_config is None:
                    os.environ.pop("PAYROLL_CLI_CONFIG", None)
                else:
                    os.environ["PAYROLL_CLI_CONFIG"] = previous_config
            output, error = stdout.getvalue(), stderr.getvalue()
        elapsed = (time.perf_counter_ns() - started) / 1_000_000
        name = " ".join(arguments[:2] if arguments[0] not in {"configure", "init"} else arguments[:1])
        metric = self.commands.setdefault(name, {"count": 0, "elapsed_ms": 0.0, "min_ms": None, "max_ms": 0.0})
        metric["count"] += 1
        metric["elapsed_ms"] += elapsed
        metric["min_ms"] = elapsed if metric["min_ms"] is None else min(metric["min_ms"], elapsed)
        metric["max_ms"] = max(metric["max_ms"], elapsed)
        if status:
            raise RuntimeError(error.strip())
        return json.loads(output)

    def operation(self, noun, verb, **payload):
        return self.invoke([noun, verb, "--input", "-"], payload)

    def metrics(self):
        return {
            name: {
                "count": value["count"],
                "elapsed_ms": round(value["elapsed_ms"], 3),
                "min_ms": round(value["min_ms"], 3),
                "max_ms": round(value["max_ms"], 3),
            }
            for name, value in sorted(self.commands.items())
        }


def _resource_usage(before_self, before_children):
    current_self = resource.getrusage(resource.RUSAGE_SELF)
    current_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "self": {
            "user_cpu_seconds": round(current_self.ru_utime - before_self.ru_utime, 6),
            "system_cpu_seconds": round(current_self.ru_stime - before_self.ru_stime, 6),
            "peak_rss_kb": current_self.ru_maxrss,
            "peak_rss_semantics": "maximum resident set of the benchmark process",
        },
        "children": {
            "user_cpu_seconds": round(current_children.ru_utime - before_children.ru_utime, 6),
            "system_cpu_seconds": round(current_children.ru_stime - before_children.ru_stime, 6),
            "peak_rss_kb": current_children.ru_maxrss,
            "peak_rss_semantics": "maximum resident set reported for one waited child, not the sum of sequential CLI children",
        },
    }


def _database_metrics(database):
    connection = sqlite3.connect(database)
    try:
        page_size = connection.execute("PRAGMA page_size").fetchone()[0]
        page_count = connection.execute("PRAGMA page_count").fetchone()[0]
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        synchronous_number = connection.execute("PRAGMA synchronous").fetchone()[0]
    finally:
        connection.close()
    synchronous = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}.get(synchronous_number, str(synchronous_number))
    stat = database.stat()
    return {
        "file_bytes": stat.st_size, "allocated_bytes": stat.st_blocks * 512,
        "page_count": page_count, "page_size": page_size,
        "journal_mode": journal_mode, "synchronous": synchronous,
    }


def _verify(database, employees):
    connection = sqlite3.connect(database)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        expected_tables = {"payroll_l1_records", "payroll_l2_records", "payroll_draft_ledger", "payroll_ledger", "payroll_employer_liability_ledger"}
        draft_good = connection.execute(
            "SELECT COUNT(*) FROM payroll_l1_records WHERE tenant=? AND key LIKE 'payroll.draft:%' AND json_extract(value,'$.payroll_month')=? AND json_extract(value,'$.gross_minor')=? AND json_extract(value,'$.deductions_minor')=? AND json_extract(value,'$.net_minor')=?",
            (TENANT, MONTH, GROSS_MINOR, DEDUCTIONS_MINOR, NET_MINOR),
        ).fetchone()[0]
        posted_good = connection.execute(
            "SELECT COUNT(*) FROM (SELECT employee_id,payroll_month,SUM(CASE WHEN direction IN ('earning','employer_expense') THEN amount_minor ELSE 0 END) gross,SUM(CASE WHEN direction IN ('deduction','employer_liability') THEN amount_minor ELSE 0 END) deductions FROM payroll_ledger WHERE tenant=? GROUP BY employee_id,payroll_month HAVING gross=? AND deductions=?)",
            (TENANT, GROSS_MINOR, DEDUCTIONS_MINOR),
        ).fetchone()[0]
        payable_good = connection.execute(
            "SELECT COUNT(*) FROM (SELECT p.employee_id,COUNT(*) count,SUM(e.amount_minor) amount FROM payroll_employer_liability_ledger e JOIN payroll_ledger p ON p.tenant=e.tenant AND p.ledger_entry_id=e.posted_liability_entry_id WHERE e.tenant=? AND e.row_kind='obligation' GROUP BY p.employee_id HAVING count=5 AND amount=?)",
            (TENANT, PAYABLE_MINOR),
        ).fetchone()[0]
        counts = {
            "l1_records": connection.execute("SELECT COUNT(*) FROM payroll_l1_records WHERE tenant=?", (TENANT,)).fetchone()[0],
            "l2_records": connection.execute("SELECT COUNT(*) FROM payroll_l2_records WHERE tenant=?", (TENANT,)).fetchone()[0],
            "draft_rows": connection.execute("SELECT COUNT(*) FROM payroll_draft_ledger WHERE tenant=?", (TENANT,)).fetchone()[0],
            "posted_rows": connection.execute("SELECT COUNT(*) FROM payroll_ledger WHERE tenant=?", (TENANT,)).fetchone()[0],
            "obligations": connection.execute("SELECT COUNT(*) FROM payroll_employer_liability_ledger WHERE tenant=? AND row_kind='obligation'", (TENANT,)).fetchone()[0],
            "remittances": connection.execute("SELECT COUNT(*) FROM payroll_employer_liability_ledger WHERE tenant=? AND row_kind='remittance'", (TENANT,)).fetchone()[0],
            "allocations": connection.execute("SELECT COUNT(*) FROM payroll_employer_liability_ledger WHERE tenant=? AND row_kind='allocation'", (TENANT,)).fetchone()[0],
        }
        sums = {
            "gross_minor": connection.execute("SELECT SUM(CASE WHEN direction IN ('earning','employer_expense') THEN amount_minor ELSE 0 END) FROM payroll_ledger WHERE tenant=?", (TENANT,)).fetchone()[0],
            "deductions_minor": connection.execute("SELECT SUM(CASE WHEN direction IN ('deduction','employer_liability') THEN amount_minor ELSE 0 END) FROM payroll_ledger WHERE tenant=?", (TENANT,)).fetchone()[0],
            "payable_minor": connection.execute("SELECT COALESCE(SUM(amount_minor),0) FROM payroll_employer_liability_ledger WHERE tenant=? AND row_kind='obligation'", (TENANT,)).fetchone()[0],
        }
        sums["net_minor"] = sums["gross_minor"] - sums["deductions_minor"]
    finally:
        connection.close()
    expected_counts = {"l1_records": employees * 29 + 10, "l2_records": employees, "draft_rows": employees * 12, "posted_rows": employees * 12, "obligations": employees * 5, "remittances": 0, "allocations": 0}
    expected_sums = {"gross_minor": employees * GROSS_MINOR, "deductions_minor": employees * DEDUCTIONS_MINOR, "net_minor": employees * NET_MINOR, "payable_minor": employees * PAYABLE_MINOR}
    passed = tables == expected_tables and draft_good == posted_good == payable_good == employees and counts == expected_counts and sums == expected_sums
    if not passed:
        raise AssertionError({"tables": sorted(tables), "draft_good": draft_good, "posted_good": posted_good, "payable_good": payable_good, "counts": counts, "sums": sums})
    return {"passed": True, "tables": sorted(tables), "employees_with_exact_draft": draft_good, "employees_with_exact_posted_totals": posted_good, "employees_with_five_payables": payable_good, "counts": counts, "sums": sums}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--employees", type=int, default=3000)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("subprocess", "inprocess"), default="subprocess")
    args = parser.parse_args(argv)
    if args.employees <= 0:
        parser.error("--employees must be positive")
    root = Path(__file__).parents[1].resolve()
    output = args.output_dir.resolve()
    if not output.is_relative_to(root.parent):
        parser.error("--output-dir must be on the workspace disk")
    if output.exists():
        parser.error("--output-dir must be fresh")
    output.mkdir(parents=True)
    database = output / "payroll.sqlite"
    config = output / "payroll.cli.json"
    progress_path = output / "progress.json"
    driver = Driver(args.mode, root, config)
    before_self = resource.getrusage(resource.RUSAGE_SELF)
    before_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    wall_started = time.perf_counter()
    stage_seconds = {}
    employee_rows = {f"E{index:06d}": {"employee_id": f"E{index:06d}"} for index in range(1, args.employees + 1)}
    state = {}
    checkpoint_interval = 10 if args.employees < 100 else 25

    def run_phase(name, worker):
        phase_started = time.perf_counter()
        last_print = phase_started
        for index, (employee, row) in enumerate(employee_rows.items(), 1):
            started = time.perf_counter_ns()
            worker(index, employee)
            row[f"{name}_ms"] = round((time.perf_counter_ns() - started) / 1_000_000, 3)
            now = time.perf_counter()
            if index % checkpoint_interval == 0 or index == args.employees:
                _atomic_json(progress_path, {"status": "running", "mode": args.mode, "phase": name, "completed": index, "total": args.employees, "rate_per_second": round(index / (now - phase_started), 3), "elapsed_seconds": round(now - wall_started, 3)})
            if index % 100 == 0 or now - last_print >= 30 or index == args.employees:
                print(json.dumps({"phase": name, "completed": index, "total": args.employees, "rate_per_second": round(index / (now - phase_started), 3)}), flush=True)
                last_print = now
        stage_seconds[name] = round(time.perf_counter() - phase_started, 6)

    setup_started = time.perf_counter()
    driver.invoke(["configure", "--db", str(database), "--tenant", TENANT, "--actor", ACTOR])
    driver.invoke(["init"])
    components = {}
    for code, kind, payable in COMPONENTS:
        components[code] = driver.operation("component", "define", component_id=code, revision=1, code=code, label=code.replace("_", " ").title(), kind=kind, country_code="IN", authority_payable=payable)["key"]
    stage_seconds["setup"] = round(time.perf_counter() - setup_started, 6)

    def sources(index, employee):
        seed = BASE_ID + index * 100
        driver.operation("settings", "set", value={"schema_version": 1, "employee_id": employee, "revision": 1, "effective_from": MONTH, "policy_ref": {"id": "KARNATAKA-PAYROLL-BENCHMARK", "revision": 1}, "payslip_locale": "en-IN", "tax": {"jurisdiction": "IN", "financial_year": "2026-27", "regime": "new"}})
        earning_specs = (("BASIC", 7_500_000), ("HRA", 3_000_000), ("SPECIAL_ALLOWANCE", 4_500_000), ("EPF_EMPLOYER", 55_000), ("EPS_EMPLOYER", 125_000))
        earnings = [driver.operation("earning", "define", earning_id=_identifier("earning", seed + offset), revision=1, employee_id=employee, component_key=components[code], amount_minor=amount, effective_from=MONTH)["key"] for offset, (code, amount) in enumerate(earning_specs)]
        instruction_specs = (("EPF_EMPLOYEE", 180_000, "monthly", "EPF-V1", "2027-03"), ("PROFESSIONAL_TAX_KA", 20_000, "monthly", "PT-NOV-V1", "2027-01"), ("INCOME_TAX_TDS", 1_265_334, "one_time", "TDS-NOV-V1", MONTH), ("LOAN", 200_000, "monthly", "LOAN-V1", "2027-03"), ("BONUS", 500_000, "one_time", "BONUS-V1", MONTH))
        versions = [driver.operation("instruction", "add", instruction_id=_identifier("instruction", seed + 10 + offset), version_id=f"{version}-{employee}", revision=1, employee_id=employee, component_key=components[code], amount_minor=amount, cadence=cadence, start_month=MONTH, end_month=end)["value"]["version_id"] for offset, (code, amount, cadence, version, end) in enumerate(instruction_specs)]
        state[employee] = {"seed": seed, "earnings": earnings, "versions": versions}

    def drafts(index, employee):
        item = state[employee]
        item["draft_id"] = _identifier("draft", item["seed"] + 20)
        draft = driver.operation("draft", "create", draft_id=item["draft_id"], employee_id=employee, payroll_month=MONTH, earning_keys=item["earnings"], instruction_version_ids=item["versions"])
        driver.operation("draft", "review", draft_id=item["draft_id"], employee_id=employee, review_id=_identifier("review", item["seed"] + 21), content_hash=draft["content_hash"], control_revision=1, decision="approved")

    def commits(index, employee):
        item = state[employee]
        outcome = driver.operation("draft", "commit", draft_id=item["draft_id"], employee_id=employee, idempotency_key=f"benchmark-{employee}", expected_control_revision=1, approval_required=True, fresh_review_required=True)
        item["payables"] = outcome["payable_entry_ids"]

    authority = {components["EPF_EMPLOYEE"]: "EPFO", components["EPF_EMPLOYER"]: "EPFO", components["EPS_EMPLOYER"]: "EPFO", components["PROFESSIONAL_TAX_KA"]: "KA_COMMERCIAL_TAX", components["INCOME_TAX_TDS"]: "INCOME_TAX"}
    def liabilities(index, employee):
        item = state[employee]
        posted = driver.invoke(["ledger", "payroll", "--employee", employee, "--month", MONTH])
        by_id = {row["ledger_entry_id"]: row for row in posted}
        for offset, posted_id in enumerate(item["payables"]):
            row = by_id[posted_id]
            driver.operation("liability", "obligation", entry_id=_identifier("liabilityentry", item["seed"] + 30 + offset), posted_liability_entry_id=posted_id, amount_minor=row["amount_minor"], employer_id="EMPLOYER-KA-BENCHMARK", authority_id=authority[row["component_key"]], reporting_period=MONTH)

    run_phase("sources", sources)
    run_phase("drafts", drafts)
    run_phase("commits", commits)
    run_phase("liabilities", liabilities)
    for row in employee_rows.values():
        row["total_ms"] = round(sum(row[f"{name}_ms"] for name in ("sources", "drafts", "commits", "liabilities")), 3)
    with (output / "employee-stage-timings.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("employee_id", "sources_ms", "drafts_ms", "commits_ms", "liabilities_ms", "total_ms"))
        writer.writeheader(); writer.writerows(employee_rows.values())

    verification_started = time.perf_counter()
    verified = _verify(database, args.employees)
    verification_seconds = round(time.perf_counter() - verification_started, 6)
    wall_seconds = round(time.perf_counter() - wall_started, 6)
    metrics = {
        "workload": {"employees": args.employees, "payroll_month": MONTH, "mode": args.mode, "tax_regime": "new", "sequential": True},
        "expected": {"cli_calls": args.employees * 20 + 12, "counts": {"l1_records": args.employees * 29 + 10, "l2_records": args.employees, "draft_rows": args.employees * 12, "posted_rows": args.employees * 12, "obligations": args.employees * 5, "remittances": 0, "allocations": 0}, "sums": {"gross_minor": args.employees * GROSS_MINOR, "deductions_minor": args.employees * DEDUCTIONS_MINOR, "net_minor": args.employees * NET_MINOR, "payable_minor": args.employees * PAYABLE_MINOR}},
        "verified": verified,
        "wall_seconds": wall_seconds, "verification_seconds": verification_seconds,
        "stages": {name: {"seconds": seconds, **({"per_employee_ms": _percentiles([row[f"{name}_ms"] for row in employee_rows.values()])} if name != "setup" else {})} for name, seconds in stage_seconds.items()},
        "per_employee_total_ms": _percentiles([row["total_ms"] for row in employee_rows.values()]),
        "commands": driver.metrics(), "cli_call_count": sum(value["count"] for value in driver.commands.values()),
        "resources": _resource_usage(before_self, before_children), "database": _database_metrics(database), "host": _host(),
    }
    if metrics["cli_call_count"] != metrics["expected"]["cli_calls"]:
        raise AssertionError("CLI call count mismatch")
    _atomic_json(output / "metrics.json", metrics)
    _atomic_json(progress_path, {"status": "complete", "mode": args.mode, "phase": "verified", "completed": args.employees, "total": args.employees, "elapsed_seconds": wall_seconds})
    print(json.dumps({"status": "complete", "metrics": str(output / "metrics.json"), "wall_seconds": wall_seconds, "verified": verified["passed"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

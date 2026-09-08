"""Run an illustrative Karnataka payroll through separate CLI processes."""
from __future__ import annotations

import argparse, json, shlex, subprocess, sys, time
from pathlib import Path


def _tax_projection(regime):
    annual_cash = 1_805_000
    taxable = annual_cash - (75_000 if regime == "new" else 50_000 + 21_600 + 2_500)
    slabs = (
        ((400_000, 0), (800_000, 5), (1_200_000, 10), (1_600_000, 15), (2_000_000, 20), (2_400_000, 25), (10**12, 30))
        if regime == "new" else
        ((250_000, 0), (500_000, 5), (1_000_000, 20), (10**12, 30))
    )
    tax = lower = 0
    for upper, rate in slabs:
        tax += max(0, min(taxable, upper) - lower) * rate // 100
        lower = upper
        if taxable <= upper:
            break
    annual_tax = (((tax * 104 // 100) + 5) // 10) * 10
    annual_minor = annual_tax * 100
    prior_monthly_minor = (annual_minor + 6) // 12
    prior_withholding_minor = prior_monthly_minor * 7
    current_tds_minor = (annual_minor - prior_withholding_minor + 2) // 5
    return {
        "regime": regime,
        "annual_cash_income_minor": annual_cash * 100,
        "taxable_income_minor": taxable * 100,
        "annual_tax_minor": annual_minor,
        "prior_months": 7,
        "prior_withholding_minor": prior_withholding_minor,
        "remaining_months": 5,
        "current_tds_minor": current_tds_minor,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--step", action="store_true", help="pause before every CLI subprocess and show its input and result")
    parser.add_argument("--tax-regime", choices=("old", "new"), default="new", help="illustrative L2 tax choice (default: new)")
    parser.add_argument("--settle", action="store_true", help="append supplied remittances and allocations; default leaves obligations unpaid")
    args = parser.parse_args(argv)
    if args.db.exists():
        parser.error("--db must name a fresh path")

    root = Path(__file__).parents[1]
    base = [sys.executable, "-m", "sqlite_lab.cli", "--db", str(args.db), "--tenant", "T1", "--actor", "payroll-admin"]
    timings = []
    started_all = time.perf_counter_ns()

    def invoke(arguments, payload=None, output_format="json"):
        command = [*base]
        if output_format != "json": command += ["--format", output_format]
        command += arguments
        if args.step:
            if payload is None:
                print(f"\n$ {shlex.join(command)}")
            else:
                print(f"\n$ {shlex.join(command)} <<'JSON'")
                print(json.dumps(payload, indent=2, sort_keys=True)); print("JSON")
            input("Press Enter to run… ")
        started = time.perf_counter_ns()
        result = subprocess.run(command, cwd=root, text=True, input=None if payload is None else json.dumps(payload), capture_output=True)
        timings.append({"command": " ".join(arguments[:2]), "elapsed_ms": round((time.perf_counter_ns() - started) / 1_000_000, 3)})
        if args.step: print((result.stdout if result.returncode == 0 else result.stderr).rstrip())
        if result.returncode: raise RuntimeError(result.stderr.strip())
        return json.loads(result.stdout) if output_format == "json" else result.stdout.rstrip()

    def l1(operation, **payload): return invoke(["l1", operation, "--input", "-"], payload)
    def rejected_l1(operation, **payload):
        try: l1(operation, **payload)
        except RuntimeError as error: return json.loads(str(error))
        raise AssertionError("operation should have been rejected")

    invoke(["init"])
    employee = "E101"
    invoke(["l2", "put_l2_settings", "--input", "-"], {"value": {
        "schema_version": 1, "employee_id": employee, "revision": 1, "effective_from": "2026-11",
        "policy_ref": {"id": "KARNATAKA-PAYROLL-DEMO", "revision": 1}, "payslip_locale": "en-IN",
        "tax": {"jurisdiction": "IN", "financial_year": "2026-27", "regime": args.tax_regime},
    }})
    settings = invoke(["l2", "effective_l2_settings", "--input", "-"], {"employee_id": employee, "payroll_month": "2026-11"})
    tax = _tax_projection(settings["value"]["tax"]["regime"])
    if args.step:
        print("\nIllustrative L3 annual projection (prior withholding supplied)")
        print(json.dumps(tax, indent=2, sort_keys=True))

    component_specs = (
        ("BASIC", "earning", False), ("HRA", "earning", False), ("SPECIAL_ALLOWANCE", "earning", False),
        ("EPF_EMPLOYEE", "deduction", True), ("EPF_EMPLOYER", "employer_contribution", False),
        ("EPS_EMPLOYER", "employer_contribution", False), ("PROFESSIONAL_TAX_KA", "deduction", True),
        ("INCOME_TAX_TDS", "deduction", True), ("LOAN", "deduction", False), ("BONUS", "earning", False),
    )
    components = {}
    for code, kind, payable in component_specs:
        components[code] = l1("define_component", component_id=code, revision=1, code=code, label=code.replace("_", " ").title(), kind=kind, country_code="IN", authority_payable=payable)["key"]

    earning_specs = (
        ("earning_9do1sj396nf9", "BASIC", 7_500_000),
        ("earning_9do1sj396nfa", "HRA", 3_000_000),
        ("earning_9do1sj396nfb", "SPECIAL_ALLOWANCE", 4_500_000),
        ("earning_9do1sj396nfc", "EPF_EMPLOYER", 55_000),
        ("earning_9do1sj396nfd", "EPS_EMPLOYER", 125_000),
    )
    earnings = [l1("define_earning", earning_id=eid, revision=1, employee_id=employee, component_key=components[code], amount_minor=amount, effective_from="2026-11")["key"] for eid, code, amount in earning_specs]
    instruction_specs = (
        ("instruction_9do1sj396nfe", "EPF-V1", "EPF_EMPLOYEE", 180_000, "monthly", "2026-11", "2027-03"),
        ("instruction_9do1sj396nff", "PT-NOV-V1", "PROFESSIONAL_TAX_KA", 20_000, "monthly", "2026-11", "2027-01"),
        ("instruction_9do1sj396nfg", "TDS-NOV-V1", "INCOME_TAX_TDS", tax["current_tds_minor"], "one_time", "2026-11", "2026-11"),
        ("instruction_9do1sj396nfh", "LOAN-V1", "LOAN", 200_000, "monthly", "2026-11", "2027-03"),
        ("instruction_9do1sj396nfi", "BONUS-V1", "BONUS", 500_000, "one_time", "2026-11", "2026-11"),
    )
    instructions = [l1("add_instruction", instruction_id=iid, version_id=vid, revision=1, employee_id=employee, component_key=components[code], amount_minor=amount, cadence=cadence, start_month=start, end_month=end) for iid, vid, code, amount, cadence, start, end in instruction_specs]

    draft_id = "draft_9do1sj396nfj"
    draft = l1("create_draft", draft_id=draft_id, employee_id=employee, payroll_month="2026-11", earning_keys=earnings, instruction_version_ids=[row["value"]["version_id"] for row in instructions])
    l1("set_draft_control", draft_id=draft_id, employee_id=employee, held=True, cancelled=False, reason="manager hold", expected_revision=1)
    held = rejected_l1("commit", draft_id=draft_id, employee_id=employee, idempotency_key="held-probe", expected_control_revision=2)
    assert held["message"] == "draft held or cancelled"
    l1("set_draft_control", draft_id=draft_id, employee_id=employee, held=False, cancelled=False, reason="manager release", expected_revision=2)
    l1("review_draft", draft_id=draft_id, employee_id=employee, review_id="review_9do1sj396nfk", content_hash=draft["content_hash"], control_revision=3, decision="approved")
    commit_input = {"draft_id": draft_id, "employee_id": employee, "idempotency_key": "karnataka-demo-commit", "expected_control_revision": 3, "approval_required": True, "fresh_review_required": True}
    committed = l1("commit", **commit_input); assert committed == l1("commit", **commit_input)

    posted = invoke(["ledger", "payroll_ledger", "--employee", employee, "--month", "2026-11"])
    posted_by_id = {row["ledger_entry_id"]: row for row in posted}
    authority = {
        components["EPF_EMPLOYEE"]: "EPFO", components["EPF_EMPLOYER"]: "EPFO", components["EPS_EMPLOYER"]: "EPFO",
        components["PROFESSIONAL_TAX_KA"]: "KA_COMMERCIAL_TAX", components["INCOME_TAX_TDS"]: "INCOME_TAX",
    }
    obligation_ids = [f"liabilityentry_9do1sj396n{suffix}" for suffix in ("fm", "fn", "fo", "fp", "fq")]
    obligations = []
    assert len(committed["payable_entry_ids"]) == 5
    for obligation_id, posted_id in zip(obligation_ids, committed["payable_entry_ids"]):
        row = posted_by_id[posted_id]
        obligations.append((obligation_id, authority[row["component_key"]], row["amount_minor"]))
        l1("record_obligation", entry_id=obligation_id, posted_liability_entry_id=posted_id, amount_minor=row["amount_minor"], employer_id="EMPLOYER-KA-DEMO", authority_id=authority[row["component_key"]], reporting_period="2026-11")
    outstanding_before = sum(l1("elr_outstanding", obligation_id=oid) for oid, _, _ in obligations)

    if args.settle:
        remittance_ids = dict(zip(("EPFO", "KA_COMMERCIAL_TAX", "INCOME_TAX"), ("liabilityentry_9do1sj396nfr", "liabilityentry_9do1sj396nfs", "liabilityentry_9do1sj396nft")))
        allocation_ids = iter(f"liabilityentry_9do1sj396n{suffix}" for suffix in ("fu", "fv", "fw", "fx", "fy"))
        for name, remittance_id in remittance_ids.items():
            amount = sum(value for _, owner, value in obligations if owner == name)
            l1("record_remittance", entry_id=remittance_id, amount_minor=amount, proof_ref=f"challan:{name.lower()}:demo", employer_id="EMPLOYER-KA-DEMO", authority_id=name, reporting_period="2026-11")
        for obligation_id, name, amount in obligations:
            l1("allocate_remittance", entry_id=next(allocation_ids), obligation_id=obligation_id, remittance_id=remittance_ids[name], amount_minor=amount)
    outstanding_after = sum(l1("elr_outstanding", obligation_id=oid) for oid, _, _ in obligations)

    expected_deductions = 580_000 + tax["current_tds_minor"]
    assert (draft["gross_minor"], draft["deductions_minor"], draft["net_minor"]) == (15_680_000, expected_deductions, 15_680_000 - expected_deductions)
    expected_payable = 380_000 + tax["current_tds_minor"]
    assert outstanding_before == expected_payable
    assert outstanding_after == (0 if args.settle else expected_payable)
    elapsed = round((time.perf_counter_ns() - started_all) / 1_000_000, 3)
    timing = {"interactive_elapsed_ms": elapsed, "active_subprocess_ms": round(sum(item["elapsed_ms"] for item in timings), 3)} if args.step else {"elapsed_ms": elapsed}
    print(json.dumps({
        "database": str(args.db), "employee": employee, "payroll_month": "2026-11", "tax_projection": tax,
        "assumptions": {"resident_india": True, "age_band": "under_60", "eps_existing_member": True, "pf_wage_cap_minor": 1_500_000, "higher_pf_contribution": False, "hra_exemption_minor": 0, "other_income_minor": 0, "professional_tax_annual_minor": 250_000},
        "held_commit_rejected": True, "commit_replay_equal": True, "settled": args.settle,
        "totals": {key: draft[key] for key in ("gross_minor", "deductions_minor", "net_minor")},
        "payable_entry_count": len(committed["payable_entry_ids"]), "outstanding_before_remittance_minor": outstanding_before,
        "outstanding_minor": outstanding_after, **timing, "commands": timings,
    }, indent=2, sort_keys=True))
    for ledger in ("payroll_draft_ledger", "payroll_ledger", "payroll_employer_liability_ledger"):
        print(f"\n{ledger}"); result = invoke(["ledger", ledger], output_format="table")
        if not args.step: print(result)
    return 0


if __name__ == "__main__": raise SystemExit(main())

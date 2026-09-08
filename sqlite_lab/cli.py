"""Thin command line access to the SQLite payroll prototype."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .payroll import Payroll
from .records import RecordStore, SCHEMAS, connect


PAYROLL_OPS = {
    "define_component": Payroll.define_component,
    "disable_component": Payroll.disable_component,
    "define_earning": Payroll.define_earning,
    "add_instruction": Payroll.add_instruction,
    "add_instruction_version": Payroll.add_instruction_version,
    "create_draft": Payroll.create_draft,
    "set_draft_control": Payroll.set_draft_control,
    "review_draft": Payroll.review_draft,
    "commit": Payroll.commit,
    "instruction_application": Payroll.instruction_application,
    "record_obligation": Payroll.record_obligation,
    "record_remittance": Payroll.record_remittance,
    "allocate_remittance": Payroll.allocate_remittance,
    "elr_outstanding": Payroll.elr_outstanding,
}
L1_READS = {
    "get_l1": RecordStore.get_l1,
    "effective_l1_source": RecordStore.effective_l1_source,
}
L2_OPS = {
    "put_l2_settings": RecordStore.put_l2_settings,
    "get_l2": RecordStore.get_l2,
    "current_l2_settings": RecordStore.current_l2_settings,
    "effective_l2_settings": RecordStore.effective_l2_settings,
}
L1_HISTORY = {"history_l1": False, "current_l1": True}
LEDGERS = (
    "payroll_draft_ledger",
    "payroll_ledger",
    "payroll_employer_liability_ledger",
)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _parser():
    parser = Parser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--format", choices=("json", "table"), default="json")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="create a fresh payroll database")
    commands.add_parser("operations", help="list the explicit operation inventory")
    for layer, choices in (
        ("l1", (*PAYROLL_OPS, *L1_READS, *L1_HISTORY)),
        ("l2", tuple(L2_OPS)),
    ):
        operation = commands.add_parser(layer, help=f"run an allowlisted {layer.upper()} operation")
        operation.add_argument("operation", choices=choices)
        operation.add_argument("--input", required=True, help="JSON object file, or - for stdin")
    records = commands.add_parser("records", help="list tenant-scoped record rows")
    records.add_argument("layer", choices=("l1", "l2"))
    ledger = commands.add_parser("ledger", help="list tenant-scoped ledger rows")
    ledger.add_argument("name", choices=LEDGERS)
    ledger.add_argument("--employee")
    ledger.add_argument("--month")
    return parser


def _input(source):
    text = sys.stdin.read() if source == "-" else Path(source).read_text()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("operation input must be a JSON object")
    return value


def _history(store, tenant, payload, current):
    payload = dict(payload)
    record_type = payload.pop("record_type", None)
    schema = SCHEMAS.get(record_type)
    if not schema or record_type == "payroll.employee.settings" or schema["identity"][-1][1] != "revision":
        raise ValueError("record_type must be a versioned L1 type")
    names = [name for name, _ in schema["identity"][:-1]]
    if set(payload) != set(names):
        raise ValueError("history input fields must match the record identity")
    identity = [payload[name] for name in names]
    method = RecordStore.current_l1 if current else RecordStore.history_l1
    return method(store, tenant, record_type, *identity)


def _record_rows(db, tenant, layer):
    table = f"payroll_{layer}_records"
    rows = [dict(row) for row in db.execute(
        f"SELECT tenant,key,value,ts,state FROM {table} WHERE tenant=? ORDER BY rowid",
        (tenant,),
    )]
    for row in rows:
        row["value"] = json.loads(row["value"])
    return rows


def _ledger_rows(db, tenant, name, employee, month):
    if name not in LEDGERS:
        raise ValueError("ledger is not allowlisted")
    clauses = ["tenant=?"]
    values = [tenant]
    if employee:
        if name == "payroll_employer_liability_ledger":
            raise ValueError("employee filter is unavailable for the employer liability ledger")
        clauses.append("employee_id=?"); values.append(employee)
    if month:
        clauses.append(("reporting_period" if name == "payroll_employer_liability_ledger" else "payroll_month") + "=?")
        values.append(month)
    return [dict(row) for row in db.execute(
        f"SELECT * FROM {name} WHERE {' AND '.join(clauses)} ORDER BY rowid", values
    )]


def _rows(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return [{"result": value}]


def _print(value, output_format):
    if output_format == "json":
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    rows = _rows(value)
    if not rows:
        print("(no rows)")
        return
    columns = list(dict.fromkeys(key for row in rows for key in row))
    cells = [[json.dumps(row.get(key), sort_keys=True) if isinstance(row.get(key), (dict, list)) else str(row.get(key) if row.get(key) is not None else "") for key in columns] for row in rows]
    widths = [max(len(columns[index]), *(len(row[index]) for row in cells)) for index in range(len(columns))]
    print(" | ".join(name.ljust(widths[index]) for index, name in enumerate(columns)))
    print("-+-".join("-" * width for width in widths))
    for row in cells:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def run(args):
    if args.command == "init":
        if args.db.exists():
            raise FileExistsError("database already exists")
        args.db.parent.mkdir(parents=True, exist_ok=True)
        connect(args.db).close()
        return {"status": "initialized", "database": str(args.db)}
    if not args.db.is_file():
        raise FileNotFoundError("database does not exist; run init first")
    probe = sqlite3.connect(args.db.resolve().as_uri() + "?mode=rw", uri=True)
    try:
        if not probe.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='payroll_l1_records'"
        ).fetchone():
            raise RuntimeError("database is not initialized; run init first")
    finally:
        probe.close()
    db = connect(args.db)
    try:
        if args.command == "operations":
            return {"l1": [*PAYROLL_OPS, *L1_READS, *L1_HISTORY], "l2": list(L2_OPS), "ledgers": list(LEDGERS)}
        if args.command == "records":
            return _record_rows(db, args.tenant, args.layer)
        if args.command == "ledger":
            return _ledger_rows(db, args.tenant, args.name, args.employee, args.month)
        payload = _input(args.input)
        store = RecordStore(db)
        if args.command == "l2":
            return L2_OPS[args.operation](store, args.tenant, **payload)
        if args.operation in L1_HISTORY:
            return _history(store, args.tenant, payload, L1_HISTORY[args.operation])
        if args.operation in L1_READS:
            return L1_READS[args.operation](store, args.tenant, **payload)
        return PAYROLL_OPS[args.operation](Payroll(db, args.tenant, args.actor), **payload)
    finally:
        db.close()


def main(argv=None):
    try:
        args = _parser().parse_args(argv)
        _print(run(args), args.format)
        return 0
    except Exception as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

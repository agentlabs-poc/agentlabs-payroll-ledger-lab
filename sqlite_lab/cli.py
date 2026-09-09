"""Thin command line access to the SQLite payroll prototype."""
from __future__ import annotations

import argparse
import json
import os
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
    "record_reversal": Payroll.record_reversal,
    "post_elr": Payroll.post_elr,
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
LEDGER_ALIASES = {"draft": "payroll_draft_ledger", "payroll": "payroll_ledger", "liability": "payroll_employer_liability_ledger"}
LEDGER_POSTS = {"payroll_draft_ledger": "create_draft", "payroll_ledger": "commit", "payroll_employer_liability_ledger": "post_elr"}
NATURAL_OPS = {
    "component": {"define": ("l1", "define_component"), "disable": ("l1", "disable_component")},
    "earning": {"define": ("l1", "define_earning")},
    "instruction": {"add": ("l1", "add_instruction"), "revise": ("l1", "add_instruction_version"), "application": ("l1", "instruction_application")},
    "draft": {"create": ("l1", "create_draft"), "control": ("l1", "set_draft_control"), "review": ("l1", "review_draft"), "commit": ("l1", "commit")},
    "liability": {"post": ("l1", "post_elr"), "reverse": ("l1", "record_reversal"), "obligation": ("l1", "record_obligation"), "remittance": ("l1", "record_remittance"), "allocate": ("l1", "allocate_remittance"), "outstanding": ("l1", "elr_outstanding")},
    "settings": {"set": ("l2", "put_l2_settings"), "get": ("l2", "get_l2"), "current": ("l2", "current_l2_settings"), "effective": ("l2", "effective_l2_settings")},
    "record": {"get": ("l1", "get_l1"), "history": ("l1", "history_l1"), "current": ("l1", "current_l1"), "effective": ("l1", "effective_l1_source")},
}
CONFIG_FIELDS = {"database", "tenant", "actor", "format"}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _parser():
    parser = Parser(description=__doc__)
    parser.add_argument("--config", type=Path, help="config file (default: .payroll-cli.json)")
    parser.add_argument("--db", type=Path, help="payroll SQLite database")
    parser.add_argument("--tenant", help="tenant identifier")
    parser.add_argument("--actor", help="actor identifier")
    parser.add_argument("--format", choices=("json", "table"), help="output format")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("configure", help="save database, tenant, actor, and output defaults")
    commands.add_parser("init", help="create a fresh payroll database")
    commands.add_parser("reset", help="clear and recreate a known payroll database")
    commands.add_parser("operations", help="list the explicit operation inventory")
    for layer, choices in (
        ("l1", (*PAYROLL_OPS, *L1_READS, *L1_HISTORY)),
        ("l2", tuple(L2_OPS)),
    ):
        operation = commands.add_parser(layer, help=f"run an allowlisted {layer.upper()} operation")
        operation.add_argument("operation", choices=choices)
        operation.add_argument("--input", required=True, help="JSON object file, or - for stdin")
    for noun, verbs in NATURAL_OPS.items():
        operation = commands.add_parser(noun, help=f"run a {noun} operation")
        operation.add_argument("verb", choices=tuple(verbs))
        operation.add_argument("--input", required=True, help="JSON object file, or - for stdin")
    records = commands.add_parser("records", help="list tenant-scoped record rows")
    records.add_argument("layer", choices=("l1", "l2"))
    ledger = commands.add_parser("ledger", help="list tenant-scoped ledger rows")
    ledger.add_argument("name", choices=(*LEDGERS, *LEDGER_ALIASES))
    ledger.add_argument("--employee")
    ledger.add_argument("--month")
    ledger.add_argument("--view", choices=("entries", "outstanding"), default="entries")
    ledger_post = commands.add_parser("ledger-post", help="invoke one canonical ledger append operation")
    ledger_post.add_argument("name", choices=(*LEDGERS, *LEDGER_ALIASES))
    ledger_post.add_argument("--input", required=True, help="JSON object file, or - for stdin")
    return parser


def _normalize_common_args(argv):
    """Let common flags appear before or after the command."""
    values = list(sys.argv[1:] if argv is None else argv)
    common, command = [], []
    index = 0
    names = {"--config", "--db", "--tenant", "--actor", "--format"}
    while index < len(values):
        item = values[index]
        name = item.split("=", 1)[0]
        if name in names:
            common.append(item)
            if "=" not in item:
                if index + 1 >= len(values):
                    common.append("")
                else:
                    index += 1
                    common.append(values[index])
        else:
            command.append(item)
        index += 1
    return [*common, *command]


def _config_path(explicit):
    return (explicit or Path(os.environ.get("PAYROLL_CLI_CONFIG", ".payroll-cli.json"))).resolve()


def _load_config(path):
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid config JSON: {error.msg}") from error
    if not isinstance(value, dict) or not set(value) <= CONFIG_FIELDS:
        raise ValueError("config must be an object containing only database, tenant, actor, and format")
    if any(not isinstance(item, str) or not item for item in value.values()):
        raise ValueError("config values must be nonempty strings")
    if value.get("format", "json") not in {"json", "table"}:
        raise ValueError("config format must be json or table")
    if "database" in value:
        database = Path(value["database"])
        value["database"] = str(database if database.is_absolute() else path.parent / database)
    return value


def _scope(args, config):
    args.db = args.db or (Path(config["database"]) if "database" in config else None)
    args.tenant = args.tenant or config.get("tenant")
    args.actor = args.actor or config.get("actor")
    args.format = args.format or config.get("format", "json")
    missing = [name for name, value in (("database", args.db), ("tenant", args.tenant), ("actor", args.actor)) if not value]
    if missing:
        raise ValueError("missing " + ", ".join(missing) + "; run payroll-cli configure --db PATH --tenant TENANT --actor ACTOR")
    probe = sqlite3.connect(":memory:")
    try:
        Payroll(probe, args.tenant, args.actor)
    finally:
        probe.close()


def _configure(args, path, config):
    _scope(args, config)
    value = {"database": str(args.db.expanduser().resolve()), "tenant": args.tenant, "actor": args.actor, "format": args.format}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return {"status": "configured", "config": str(path), **value}


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


def _ledger_rows(db, tenant, name, employee, month, view):
    name = LEDGER_ALIASES.get(name, name)
    if name not in LEDGERS:
        raise ValueError("ledger is not allowlisted")
    if view == "outstanding" and name != "payroll_employer_liability_ledger":
        raise ValueError("outstanding view is available only for the employer liability ledger")
    if name != "payroll_employer_liability_ledger":
        clauses,values=["tenant=?"],[tenant]
        if employee: clauses.append("employee_id=?"); values.append(employee)
        if month: clauses.append("payroll_month=?"); values.append(month)
        return [dict(row) for row in db.execute(f"SELECT * FROM {name} WHERE {' AND '.join(clauses)} ORDER BY rowid",values)]
    period=" AND e.reporting_period=?" if month else ""
    if view=="outstanding":
        owner=" AND p.employee_id=?" if employee else ""
        sql=f"""SELECT e.*,e.amount_minor-COALESCE((SELECT SUM(a.amount_minor) FROM payroll_employer_liability_ledger a WHERE a.tenant=e.tenant AND a.row_kind='allocation' AND a.obligation_entry_id=e.entry_id AND NOT EXISTS(SELECT 1 FROM payroll_employer_liability_ledger av WHERE av.tenant=a.tenant AND av.row_kind='reversal' AND av.reversal_of_entry_id=a.entry_id)),0) AS outstanding_minor FROM payroll_employer_liability_ledger e JOIN payroll_ledger p ON p.tenant=e.tenant AND p.ledger_entry_id=e.posted_liability_entry_id{owner} WHERE e.tenant=? AND e.row_kind='obligation' AND NOT EXISTS(SELECT 1 FROM payroll_employer_liability_ledger v WHERE v.tenant=e.tenant AND v.row_kind='reversal' AND v.reversal_of_entry_id=e.entry_id){period} ORDER BY e.rowid"""
        values=([employee] if employee else [])+[tenant]+([month] if month else [])
        return [dict(row) for row in db.execute(sql,values)]
    if not employee:
        return [dict(row) for row in db.execute(f"SELECT e.* FROM payroll_employer_liability_ledger e WHERE e.tenant=?{period} ORDER BY e.rowid",[tenant]+([month] if month else []))]
    sql=f"""SELECT e.* FROM payroll_employer_liability_ledger e LEFT JOIN payroll_employer_liability_ledger target ON target.tenant=e.tenant AND e.row_kind='reversal' AND target.entry_id=e.reversal_of_entry_id LEFT JOIN payroll_employer_liability_ledger obligation ON obligation.tenant=e.tenant AND obligation.entry_id=CASE WHEN e.row_kind='allocation' THEN e.obligation_entry_id WHEN e.row_kind='reversal' AND target.row_kind='allocation' THEN target.obligation_entry_id END JOIN payroll_ledger p ON p.tenant=e.tenant AND p.ledger_entry_id=CASE WHEN e.row_kind='obligation' THEN e.posted_liability_entry_id WHEN e.row_kind='reversal' AND target.row_kind='obligation' THEN target.posted_liability_entry_id ELSE obligation.posted_liability_entry_id END AND p.employee_id=? WHERE e.tenant=?{period} ORDER BY e.rowid"""
    return [dict(row) for row in db.execute(sql,[employee,tenant]+([month] if month else []))]


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
    if args.command == "reset":
        args.db.parent.mkdir(parents=True, exist_ok=True)
        existed = args.db.exists()
        db = connect(args.db)
        try:
            if existed:
                schema = Path(__file__).with_name("schema.sql").read_text()
                drops = "\n".join(f"DROP TABLE {name};" for name in (
                    "payroll_employer_liability_ledger", "payroll_ledger",
                    "payroll_draft_ledger", "payroll_l2_records", "payroll_l1_records",
                ))
                db.executescript(f"BEGIN IMMEDIATE;\n{drops}\n{schema}\nCOMMIT;")
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
        return {"status": "reset", "database": str(args.db)}
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
            return {"l1": [*PAYROLL_OPS, *L1_READS, *L1_HISTORY], "l2": list(L2_OPS), "aliases": NATURAL_OPS, "ledgers": list(LEDGERS)}
        if args.command == "records":
            return _record_rows(db, args.tenant, args.layer)
        if args.command == "ledger":
            return _ledger_rows(db, args.tenant, args.name, args.employee, args.month, args.view)
        payload = _input(args.input)
        if args.command == "ledger-post":
            name=LEDGER_ALIASES.get(args.name,args.name)
            return PAYROLL_OPS[LEDGER_POSTS[name]](Payroll(db,args.tenant,args.actor),**payload)
        if args.command in NATURAL_OPS:
            args.command, args.operation = NATURAL_OPS[args.command][args.verb]
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
        args = _parser().parse_args(_normalize_common_args(argv))
        config_path = _config_path(args.config)
        config = _load_config(config_path)
        if args.command == "configure":
            value = _configure(args, config_path, config)
        else:
            _scope(args, config)
            value = run(args)
        _print(value, args.format)
        return 0
    except Exception as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

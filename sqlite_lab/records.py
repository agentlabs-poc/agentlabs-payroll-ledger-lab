"""Validated storage mechanics for the SQLite payroll folding proof."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class RecordError(ValueError):
    pass


IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
MONTH = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
STATES = {"enabled", "disabled", "deleted"}

SCHEMAS = {
    "payroll.component": {
        "fields": {"schema_version", "component_id", "revision", "code", "label", "kind", "country_code"},
        "identity": (("component_id", "text"), ("revision", "revision")),
    },
    "payroll.earning": {
        "fields": {"schema_version", "earning_id", "revision", "employee_id", "component_key", "amount_minor", "effective_from", "effective_until"},
        "identity": (("employee_id", "text"), ("earning_id", "text"), ("revision", "revision")), "optional": {"effective_until"},
    },
    "payroll.instruction": {
        "fields": {"schema_version", "instruction_id", "revision", "version_id", "employee_id", "component_key", "amount_minor", "cadence", "effective_from", "effective_until", "adjustment_of"},
        "identity": (("employee_id", "text"), ("instruction_id", "text"), ("revision", "revision")), "optional": {"effective_until", "adjustment_of"},
    },
    "payroll.draft": {
        "fields": {"schema_version", "draft_id", "revision", "employee_id", "payroll_month", "earning_keys", "instruction_keys", "source_basis", "content_hash", "gross_minor", "deductions_minor", "net_minor"},
        "identity": (("employee_id", "text"), ("draft_id", "text"), ("revision", "revision")),
    },
    "payroll.draft.control": {
        "fields": {"schema_version", "draft_id", "revision", "employee_id", "payroll_month", "actor", "held", "cancelled", "reason"},
        "identity": (("employee_id", "text"), ("draft_id", "text"), ("revision", "revision")),
    },
    "payroll.draft.review": {
        "fields": {"schema_version", "employee_id", "review_id", "draft_id", "draft_content_hash", "control_revision", "actor", "decision"},
        "identity": (("employee_id", "text"), ("draft_id", "text"), ("review_id", "text")),
    },
    "payroll.instruction.resolution": {
        "fields": {"schema_version", "employee_id", "resolution_id", "draft_id", "instruction_id", "instruction_key", "disposition", "effects"},
        "identity": (("employee_id", "text"), ("draft_id", "text"), ("resolution_id", "text")),
    },
    "payroll.instruction.application": {
        "fields": {"schema_version", "application_id", "instruction_id", "instruction_key", "version_id", "employee_id", "payroll_month", "draft_id", "cadence", "effects"},
        "identity": (("employee_id", "text"), ("instruction_id", "text"), ("application_id", "text")),
    },
    "payroll.operation.receipt": {
        "fields": {"schema_version", "employee_id", "receipt_id", "operation", "subject_id", "executor", "idempotency_key", "request_hash", "outcome", "before", "after"},
        "identity": (("employee_id", "text"), ("subject_id", "text"), ("receipt_id", "text")),
    },
    "payroll.employee.settings": {
        "fields": {"schema_version", "employee_id", "revision", "effective_from", "policy_ref", "payslip_locale"},
        "identity": (("employee_id", "text"), ("revision", "revision")),
    },
}


def _identifier(value, label="identifier", identity=False):
    valid = isinstance(value, str) and 1 <= len(value) <= 64 and value[0].isalnum()
    if identity:
        valid = valid and value.isascii() and all(
            character.isalnum() or character in "._-:\\" for character in value
        )
    else:
        valid = valid and bool(IDENTIFIER.fullmatch(value))
    if not valid:
        raise RecordError(f"invalid {label}")
    return value


def _revision(value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RecordError("revision must be a positive integer")
    return value


def canonical_key(record_type: str, *identity) -> str:
    if record_type not in SCHEMAS:
        raise RecordError("unknown record type")
    fields = SCHEMAS[record_type]["identity"]
    if len(identity) != len(fields):
        raise RecordError("canonical key has wrong identity arity")
    encoded = []
    for value, (name, kind) in zip(identity, fields):
        encoded.append(
            str(_revision(value if isinstance(value, int) else _parse_revision(value)))
            if kind == "revision" else _encode_identity(value, name)
        )
    return f"{record_type}:" + ":".join(encoded)


def _encode_identity(value, label):
    _identifier(value, label, identity=True)
    return value.replace("\\", "\\\\").replace(":", "\\:")


def _parse_revision(value):
    if not isinstance(value, str) or not value.isascii() or not value.isdigit() or value.startswith("0"):
        raise RecordError("revision must be canonical")
    return int(value)


def parse_key(key: str):
    if not isinstance(key, str) or ":" not in key:
        raise RecordError("invalid canonical key")
    record_type, encoded = key.split(":", 1)
    if record_type not in SCHEMAS:
        raise RecordError("unknown record type")
    segments = [""]
    index = 0
    while index < len(encoded):
        character = encoded[index]
        if character == "\\":
            index += 1
            if index >= len(encoded) or encoded[index] not in {":", "\\"}:
                raise RecordError("unknown or trailing identity escape")
            segments[-1] += encoded[index]
        elif character == ":":
            segments.append("")
        else:
            segments[-1] += character
        index += 1
    fields = SCHEMAS[record_type]["identity"]
    if len(segments) != len(fields):
        raise RecordError("canonical key has wrong identity arity")
    parsed = []
    for segment, (name, kind) in zip(segments, fields):
        parsed.append(_parse_revision(segment) if kind == "revision"
                      else _identifier(segment, name, identity=True))
    return record_type, *parsed


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=1, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        connection.close()
        raise RuntimeError("SQLite foreign keys could not be enabled")
    names = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )}
    expected = {"payroll_l1_records", "payroll_l2_records", "payroll_draft_ledger",
                "payroll_ledger", "payroll_employer_liability_ledger"}
    if not names:
        schema = Path(__file__).with_name("schema.sql").read_text()
        connection.executescript(schema)
    elif names != expected:
        connection.close()
        raise RuntimeError("incompatible payroll SQLite prototype; create a fresh database")
    return connection


def _validate(record_type, identity, value):
    if not isinstance(value, dict):
        raise RecordError("record value must be a JSON object")
    schema = SCHEMAS[record_type]
    optional = schema.get("optional", set())
    if not schema["fields"] - optional <= set(value) <= schema["fields"] or any(
            item is None and name not in optional for name, item in value.items()):
        raise RecordError("payload fields do not match closed schema")
    if value["schema_version"] != 1:
        raise RecordError("unsupported schema version")
    for key_value, (name, kind) in zip(identity, schema["identity"]):
        payload_value = _revision(value[name]) if kind == "revision" else value[name]
        if payload_value != key_value:
            raise RecordError(f"key and payload {name} disagree")
    if record_type == "payroll.component":
        if value["kind"] not in {"earning", "deduction", "employer_contribution"}:
            raise RecordError("invalid component kind")
        for name in ("component_id", "code", "country_code"):
            _identifier(value[name], name, identity=name == "component_id")
        if not isinstance(value["label"], str) or not value["label"]:
            raise RecordError("label is required")
    elif record_type in {"payroll.earning", "payroll.instruction"}:
        for name in ("earning_id" if record_type == "payroll.earning" else "instruction_id", "employee_id"):
            _identifier(value[name], name, identity=True)
        if type(value["amount_minor"]) is not int or value["amount_minor"] <= 0:
            raise RecordError("source amount must be positive integer minor units")
        if not MONTH.fullmatch(value["effective_from"]):
            raise RecordError("invalid source effective month")
        if value["effective_until"] is not None and (
                not MONTH.fullmatch(value["effective_until"]) or value["effective_until"] < value["effective_from"]):
            raise RecordError("invalid source expiry month")
        component_type, _, _ = parse_key(value["component_key"])
        if component_type != "payroll.component":
            raise RecordError("source component reference has wrong type")
        if record_type == "payroll.instruction":
            _identifier(value["version_id"], "version id", identity=True)
            if value["cadence"] not in {"monthly", "one_time"}:
                raise RecordError("invalid instruction cadence")
            if "adjustment_of" in value:
                _identifier(value["adjustment_of"], "adjustment entry", identity=True)
                if value["cadence"] != "one_time":
                    raise RecordError("adjustment instruction must be one-time")
    elif record_type == "payroll.draft":
        _identifier(value["employee_id"], "employee", identity=True)
        if not MONTH.fullmatch(value["payroll_month"]):
            raise RecordError("invalid payroll month")
        if not isinstance(value["earning_keys"], list) or not isinstance(value["instruction_keys"], list) or not isinstance(value["source_basis"], list):
            raise RecordError("draft source keys must be arrays")
        if any(parse_key(key)[:2] != ("payroll.earning", value["employee_id"])
               for key in value["earning_keys"]):
            raise RecordError("draft earning reference has wrong type")
        if any(parse_key(key)[:2] != ("payroll.instruction", value["employee_id"])
               for key in value["instruction_keys"]):
            raise RecordError("draft instruction reference has wrong type")
        if any(type(value[name]) is not int or value[name] < 0 for name in ("gross_minor", "deductions_minor", "net_minor")):
            raise RecordError("draft totals must be integer minor units")
        if value["net_minor"] != value["gross_minor"] - value["deductions_minor"]:
            raise RecordError("draft totals do not balance")
    elif record_type == "payroll.employee.settings":
        if not MONTH.fullmatch(value["effective_from"]):
            raise RecordError("invalid effective month")
        policy = value["policy_ref"]
        if not isinstance(policy, dict) or set(policy) != {"id", "revision"}:
            raise RecordError("invalid policy reference")
        _identifier(policy["id"], "policy id", identity=True)
        _revision(policy["revision"])
        if not isinstance(value["payslip_locale"], str) or not value["payslip_locale"]:
            raise RecordError("locale is required")
    elif record_type in {"payroll.instruction.resolution", "payroll.instruction.application"}:
        instruction = parse_key(value["instruction_key"])
        if (instruction[0], instruction[1], instruction[2]) != (
                "payroll.instruction", value["employee_id"], value["instruction_id"]):
            raise RecordError("instruction reference is outside owner scope")
        if not isinstance(value["effects"], list) or not value["effects"]:
            raise RecordError("effects must be a non-empty array")
        for effect in value["effects"]:
            required = ({"draft_entry_id", "amount_minor", "currency"}
                        if record_type.endswith("resolution")
                        else {"ledger_entry_id", "amount_minor", "currency"})
            if not isinstance(effect, dict) or set(effect) != required:
                raise RecordError("invalid effect")
            if isinstance(effect["amount_minor"], bool) or not isinstance(effect["amount_minor"], int) or effect["amount_minor"] < 0:
                raise RecordError("effect amount must use integer minor units")
            if effect["currency"] != "INR":
                raise RecordError("prototype supports INR effects")
    return value


def _row(row):
    if row is None:
        return None
    return {"tenant": row["tenant"], "key": row["key"],
            "value": json.loads(row["value"]), "ts": row["ts"], "state": row["state"]}


class RecordStore:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def _put(self, table, tenant, key, value, state="enabled"):
        _identifier(tenant, "tenant")
        if state not in STATES:
            raise RecordError("invalid state")
        parsed = parse_key(key)
        record_type, identity = parsed[0], parsed[1:]
        _validate(record_type, identity, value)
        self.connection.execute(
            f"INSERT INTO {table}(tenant,key,value,ts,state) VALUES(?,?,?,?,?)",
            (tenant, key, json.dumps(value, sort_keys=True, separators=(",", ":")),
             datetime.now(timezone.utc).isoformat(), state),
        )
        return self.get_l1(tenant, key) if table == "payroll_l1_records" else self.get_l2(tenant, key)

    def _put_l1(self, tenant, key, value, state="enabled"):
        if parse_key(key)[0] == "payroll.employee.settings":
            raise RecordError("L2 type cannot be written to L1")
        return self._put("payroll_l1_records", tenant, key, value, state)

    def put_l2_settings(self, tenant, value, state="enabled"):
        key = canonical_key("payroll.employee.settings", value.get("employee_id"), value.get("revision"))
        return self._put("payroll_l2_records", tenant, key, value, state)

    def _get(self, table, tenant, key):
        parse_key(key)
        return _row(self.connection.execute(
            f"SELECT tenant,key,value,ts,state FROM {table} WHERE tenant=? AND key=?",
            (tenant, key),
        ).fetchone())

    def get_l1(self, tenant, key):
        return self._get("payroll_l1_records", tenant, key)

    def get_l2(self, tenant, key):
        return self._get("payroll_l2_records", tenant, key)

    def history_l1(self, tenant, record_type, *identity):
        if record_type not in SCHEMAS or SCHEMAS[record_type]["identity"][-1][1] != "revision":
            raise RecordError("history requires a versioned record type")
        fields = SCHEMAS[record_type]["identity"][:-1]
        if len(identity) != len(fields):
            raise RecordError("history has wrong identity arity")
        for value, (name, _) in zip(identity, fields):
            _identifier(value, name, identity=True)
        predicates = " AND ".join(f"json_extract(value,'$.{name}')=?" for name, _ in fields)
        return [_row(row) for row in self.connection.execute(
            f"SELECT tenant,key,value,ts,state FROM payroll_l1_records "
            f"WHERE tenant=? AND key LIKE '{record_type}:%' "
            f"AND {predicates} "
            "ORDER BY CAST(json_extract(value,'$.revision') AS INTEGER)",
            (tenant, *identity),
        )]

    def current_l1(self, tenant, record_type, *identity):
        history = self.history_l1(tenant, record_type, *identity)
        if not history or history[-1]["state"] != "enabled":
            return None
        return history[-1]

    def effective_l1_source(self, tenant, record_type, employee_id, subject, payroll_month):
        if record_type not in {"payroll.earning", "payroll.instruction"}:
            raise RecordError("effective source requires an employee source type")
        _identifier(employee_id, "employee", identity=True)
        _identifier(subject, "subject", identity=True)
        if not MONTH.fullmatch(payroll_month):
            raise RecordError("invalid payroll month")
        subject_field = "earning_id" if record_type == "payroll.earning" else "instruction_id"
        return _row(self.connection.execute(
            f"SELECT tenant,key,value,ts,state FROM payroll_l1_records "
            f"WHERE tenant=? AND key LIKE '{record_type}:%' "
            "AND json_extract(value,'$.employee_id')=? "
            f"AND json_extract(value,'$.{subject_field}')=? "
            "AND json_extract(value,'$.effective_from')<=? "
            "ORDER BY CAST(json_extract(value,'$.revision') AS INTEGER) DESC LIMIT 1",
            (tenant, employee_id, subject, payroll_month),
        ).fetchone())

    def current_l2_settings(self, tenant, employee_id):
        _identifier(employee_id, "employee", identity=True)
        return _row(self.connection.execute(
            "SELECT tenant,key,value,ts,state FROM payroll_l2_records "
            "WHERE tenant=? AND json_extract(value,'$.employee_id')=? "
            "ORDER BY CAST(json_extract(value,'$.revision') AS INTEGER) DESC LIMIT 1",
            (tenant, employee_id),
        ).fetchone())

    def effective_l2_settings(self, tenant, employee_id, payroll_month):
        _identifier(employee_id, "employee", identity=True)
        if not MONTH.fullmatch(payroll_month):
            raise RecordError("invalid payroll month")
        row = _row(self.connection.execute(
            "SELECT tenant,key,value,ts,state FROM payroll_l2_records "
            "WHERE tenant=? AND key LIKE 'payroll.employee.settings:%' "
            "AND json_extract(value,'$.employee_id')=? "
            "AND json_extract(value,'$.effective_from')<=? "
            "ORDER BY json_extract(value,'$.effective_from') DESC, "
            "CAST(json_extract(value,'$.revision') AS INTEGER) DESC LIMIT 1",
            (tenant, employee_id, payroll_month),
        ).fetchone())
        return row if row and row["state"] == "enabled" else None

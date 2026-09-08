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
        "subject": "component_id", "revision": True,
    },
    "payroll.draft.control": {
        "fields": {"schema_version", "draft_id", "revision", "employee_id", "payroll_month", "actor", "held", "cancelled", "reason"},
        "subject": "draft_id", "revision": True,
    },
    "payroll.draft.review": {
        "fields": {"schema_version", "review_id", "draft_id", "draft_content_hash", "control_revision", "actor", "decision"},
        "subject": "draft_id", "record": "review_id",
    },
    "payroll.instruction.resolution": {
        "fields": {"schema_version", "resolution_id", "draft_id", "instruction_version_id", "disposition", "effects"},
        "subject": "draft_id", "record": "resolution_id",
    },
    "payroll.instruction.application": {
        "fields": {"schema_version", "application_id", "instruction_id", "instruction_version_id", "employee_id", "payroll_month", "draft_id", "cadence", "effects"},
        "subject": "instruction_version_id", "record": "application_id",
    },
    "payroll.operation.receipt": {
        "fields": {"schema_version", "receipt_id", "operation", "subject_id", "executor", "idempotency_key", "request_hash", "outcome", "before", "after"},
        "subject": "subject_id", "record": "receipt_id",
    },
    "payroll.employee.settings": {
        "fields": {"schema_version", "employee_id", "revision", "effective_from", "policy_ref", "payslip_locale"},
        "subject": "employee_id", "revision": True,
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


def canonical_key(record_type: str, subject: str, record) -> str:
    if record_type not in SCHEMAS:
        raise RecordError("unknown record type")
    subject = _encode_identity(subject, "subject")
    if SCHEMAS[record_type].get("revision"):
        record = str(_revision(record if isinstance(record, int) else _parse_revision(record)))
    else:
        record = _encode_identity(record, "record")
    return f"{record_type}:{subject}:{record}"


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
    if len(segments) != 2:
        raise RecordError("canonical key must contain three segments")
    subject, record = segments
    _identifier(subject, "subject", identity=True)
    if SCHEMAS[record_type].get("revision"):
        parsed_record = _parse_revision(record)
    else:
        _identifier(record, "record", identity=True)
        parsed_record = record
    return record_type, subject, parsed_record


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=1, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        connection.close()
        raise RuntimeError("SQLite foreign keys could not be enabled")
    initialized = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='payroll_l1_records'"
    ).fetchone()
    if initialized is None:
        schema = Path(__file__).with_name("schema.sql").read_text()
        connection.executescript(schema)
    return connection


def _validate(record_type, subject, record, value):
    if not isinstance(value, dict):
        raise RecordError("record value must be a JSON object")
    schema = SCHEMAS[record_type]
    if set(value) != schema["fields"] or any(item is None for item in value.values()):
        raise RecordError("payload fields do not match closed schema")
    if value["schema_version"] != 1:
        raise RecordError("unsupported schema version")
    if value[schema["subject"]] != subject:
        raise RecordError("key and payload subject disagree")
    if schema.get("revision"):
        if _revision(value["revision"]) != record:
            raise RecordError("key and payload revision disagree")
    elif value[schema["record"]] != record:
        raise RecordError("key and payload record identity disagree")
    if record_type == "payroll.component":
        if value["kind"] not in {"earning", "deduction", "employer_contribution"}:
            raise RecordError("invalid component kind")
        for name in ("component_id", "code", "country_code"):
            _identifier(value[name], name, identity=name == "component_id")
        if not isinstance(value["label"], str) or not value["label"]:
            raise RecordError("label is required")
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
        record_type, subject, record = parse_key(key)
        _validate(record_type, subject, record, value)
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

    def history_l1(self, tenant, record_type, subject):
        if record_type not in SCHEMAS or not SCHEMAS[record_type].get("revision"):
            raise RecordError("history requires a versioned record type")
        _identifier(subject, "subject", identity=True)
        subject_field = SCHEMAS[record_type]["subject"]
        return [_row(row) for row in self.connection.execute(
            f"SELECT tenant,key,value,ts,state FROM payroll_l1_records "
            f"WHERE tenant=? AND key LIKE '{record_type}:%' "
            f"AND json_extract(value,'$.{subject_field}')=? "
            "ORDER BY CAST(json_extract(value,'$.revision') AS INTEGER)",
            (tenant, subject),
        )]

    def current_l1(self, tenant, record_type, subject):
        history = self.history_l1(tenant, record_type, subject)
        if not history or history[-1]["state"] != "enabled":
            return None
        return history[-1]

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

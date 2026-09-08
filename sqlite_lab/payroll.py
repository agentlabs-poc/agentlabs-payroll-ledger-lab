"""Named payroll operations over the consolidated SQLite record stores."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager

from .records import MONTH, RecordError, RecordStore, canonical_key, _identifier


class PayrollError(RuntimeError):
    pass


class Conflict(PayrollError):
    pass


def _hash(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _stable_id(prefix, *parts):
    return prefix + hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:20]


def _positive_minor_units(value):
    if type(value) is not int or value <= 0:
        raise PayrollError("amount must be a positive integer number of minor units")
    return value


@contextmanager
def _write(connection):
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        connection.rollback()
        raise
    else:
        connection.commit()


class Payroll:
    def __init__(self, connection: sqlite3.Connection, tenant: str, actor: str):
        self.connection = connection
        self.tenant = _identifier(tenant, "tenant")
        self.actor = _identifier(actor, "actor")
        self.records = RecordStore(connection)

    def define_component(self, component_id, revision, code, label, kind, country_code):
        value = {
            "schema_version": 1, "component_id": component_id, "revision": revision,
            "code": code, "label": label, "kind": kind, "country_code": country_code,
        }
        with _write(self.connection):
            history = self.records.history_l1(self.tenant, "payroll.component", component_id)
            if history:
                original = history[0]["value"]
                if any(value[field] != original[field] for field in ("code", "kind", "country_code")):
                    raise Conflict("component identity fields cannot change across revisions")
            collision = self.connection.execute(
                "SELECT 1 FROM payroll_l1_records WHERE tenant=? "
                "AND key LIKE 'payroll.component:%' "
                "AND json_extract(value,'$.country_code')=? "
                "AND json_extract(value,'$.code')=? "
                "AND json_extract(value,'$.component_id')<>? LIMIT 1",
                (self.tenant, country_code, code, component_id),
            ).fetchone()
            if collision:
                raise Conflict("component code is already owned in tenant/country scope")
            try:
                return self.records._put_l1(
                    self.tenant, canonical_key("payroll.component", component_id, revision), value
                )
            except sqlite3.IntegrityError as exc:
                raise Conflict("component definition conflicts with existing identity") from exc

    def disable_component(self, component_id, expected_revision, reason="disabled"):
        with _write(self.connection):
            current = self.records.history_l1(self.tenant, "payroll.component", component_id)
            if not current or current[-1]["value"]["revision"] != expected_revision:
                raise Conflict("stale component revision")
            value = dict(current[-1]["value"])
            value["revision"] = expected_revision + 1
            value["label"] = value["label"]
            return self.records._put_l1(
                self.tenant,
                canonical_key("payroll.component", component_id, expected_revision + 1),
                value,
                state="disabled",
            )

    def add_instruction(self, instruction_id, version_id, revision, employee_id,
                        component_id, amount_minor, cadence, start_month, end_month=None):
        for value, label in ((instruction_id, "instruction"), (version_id, "instruction version"),
                             (employee_id, "employee"), (component_id, "component")):
            _identifier(value, label, identity=True)
        if cadence not in {"monthly", "one_time"} or not MONTH.fullmatch(start_month):
            raise PayrollError("invalid instruction cadence or month")
        if end_month is not None and (not MONTH.fullmatch(end_month) or end_month < start_month):
            raise PayrollError("invalid instruction end month")
        if isinstance(amount_minor, bool) or not isinstance(amount_minor, int) or amount_minor < 0:
            raise PayrollError("instruction amount must use integer minor units")
        request = {"instruction_id": instruction_id, "version_id": version_id,
                   "revision": revision, "employee_id": employee_id,
                   "component_id": component_id, "amount_minor": amount_minor,
                   "cadence": cadence, "start_month": start_month, "end_month": end_month}
        request_hash = _hash(request)
        with _write(self.connection):
            prior = self._receipt("payroll.instruction.create", instruction_id, version_id)
            if prior:
                if prior["value"]["request_hash"] != request_hash:
                    raise Conflict("instruction retry changed input")
                return prior["value"]["outcome"]
            if self.records.current_l1(self.tenant, "payroll.component", component_id) is None:
                raise PayrollError("component is not currently available")
            self.connection.execute(
                "INSERT INTO payroll_instructions(tenant,instruction_id,employee_id,cadence,start_month,end_month) VALUES(?,?,?,?,?,?)",
                (self.tenant, instruction_id, employee_id, cadence, start_month, end_month),
            )
            self.connection.execute(
                "INSERT INTO payroll_instruction_versions(tenant,instruction_version_id,instruction_id,revision,component_id,amount_minor) VALUES(?,?,?,?,?,?)",
                (self.tenant, version_id, instruction_id, revision, component_id, amount_minor),
            )
            outcome = {"status": "created", "instruction_id": instruction_id,
                       "instruction_version_id": version_id, "revision": revision}
            self._store_receipt(
                "payroll.instruction.create", instruction_id, version_id, request_hash, outcome,
                {"instruction_exists": False},
                {"instruction_exists": True, "latest_revision": revision},
            )
            return outcome

    def add_instruction_version(self, instruction_id, version_id, revision, component_id, amount_minor):
        for value, label in ((instruction_id, "instruction"), (version_id, "instruction version"),
                             (component_id, "component")):
            _identifier(value, label, identity=True)
        if isinstance(revision, bool) or not isinstance(revision, int) or revision <= 0:
            raise PayrollError("revision must be a positive integer")
        if isinstance(amount_minor, bool) or not isinstance(amount_minor, int) or amount_minor < 0:
            raise PayrollError("instruction amount must use integer minor units")
        request = {"instruction_id": instruction_id, "version_id": version_id,
                   "revision": revision, "component_id": component_id,
                   "amount_minor": amount_minor}
        request_hash = _hash(request)
        with _write(self.connection):
            prior = self._receipt("payroll.instruction.version", instruction_id, version_id)
            if prior:
                if prior["value"]["request_hash"] != request_hash:
                    raise Conflict("instruction-version retry changed input")
                return prior["value"]["outcome"]
            latest = self.connection.execute(
                "SELECT MAX(revision) FROM payroll_instruction_versions WHERE tenant=? AND instruction_id=?",
                (self.tenant, instruction_id),
            ).fetchone()[0]
            if latest is None or revision != latest + 1:
                raise Conflict("instruction revision is not the next revision")
            if self.records.current_l1(self.tenant, "payroll.component", component_id) is None:
                raise PayrollError("component is not currently available")
            self.connection.execute(
                "INSERT INTO payroll_instruction_versions(tenant,instruction_version_id,instruction_id,revision,component_id,amount_minor) VALUES(?,?,?,?,?,?)",
                (self.tenant, version_id, instruction_id, revision, component_id, amount_minor),
            )
            outcome = {"status": "version_created", "instruction_id": instruction_id,
                       "instruction_version_id": version_id, "revision": revision}
            self._store_receipt(
                "payroll.instruction.version", instruction_id, version_id, request_hash, outcome,
                {"latest_revision": latest}, {"latest_revision": revision},
            )
            return outcome

    def create_draft(self, calculation_id, draft_id, employee_id, payroll_month,
                     salary_minor, instruction_version_ids, employer_contribution_minor=0):
        for value, label in ((calculation_id, "calculation"), (draft_id, "draft"),
                             (employee_id, "employee")):
            _identifier(value, label, identity=True)
        if not MONTH.fullmatch(payroll_month):
            raise PayrollError("invalid payroll month")
        for amount in (salary_minor, employer_contribution_minor):
            if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
                raise PayrollError("amount must use integer minor units")
        with _write(self.connection):
            if self.records.current_l1(self.tenant, "payroll.component", "SALARY") is None:
                raise PayrollError("salary component is not currently available")
            if (employer_contribution_minor and
                    self.records.current_l1(self.tenant, "payroll.component", "EMPLOYER") is None):
                raise PayrollError("employer component is not currently available")
            entries = [{"entry_id": f"{draft_id}.salary", "component_id": "SALARY",
                        "direction": "earning", "amount_minor": salary_minor,
                        "instruction_version_id": None}]
            instructions = []
            for version_id in instruction_version_ids:
                row = self.connection.execute(
                    "SELECT v.instruction_version_id,v.instruction_id,v.component_id,v.amount_minor,"
                    "i.employee_id,i.cadence,i.start_month,i.end_month "
                    "FROM payroll_instruction_versions v JOIN payroll_instructions i "
                    "ON i.tenant=v.tenant AND i.instruction_id=v.instruction_id "
                    "WHERE v.tenant=? AND v.instruction_version_id=?",
                    (self.tenant, version_id),
                ).fetchone()
                if row is None or row["employee_id"] != employee_id:
                    raise PayrollError("instruction is outside employee scope")
                if payroll_month < row["start_month"] or (row["end_month"] and payroll_month > row["end_month"]):
                    continue
                if self.records.current_l1(self.tenant, "payroll.component", row["component_id"]) is None:
                    raise PayrollError("instruction component is not currently available")
                entry_id = f"{draft_id}.instruction.{len(instructions) + 1}"
                entries.append({"entry_id": entry_id, "component_id": row["component_id"],
                                "direction": "deduction", "amount_minor": row["amount_minor"],
                                "instruction_version_id": row["instruction_version_id"]})
                instructions.append(dict(row))
            if employer_contribution_minor:
                entries.extend([
                    {"entry_id": f"{draft_id}.employer.expense", "component_id": "EMPLOYER",
                     "direction": "employer_expense", "amount_minor": employer_contribution_minor,
                     "instruction_version_id": None},
                    {"entry_id": f"{draft_id}.employer.liability", "component_id": "EMPLOYER",
                     "direction": "employer_liability", "amount_minor": employer_contribution_minor,
                     "instruction_version_id": None},
                ])
            deductions = sum(entry["amount_minor"] for entry in entries if entry["direction"] == "deduction")
            candidate = {"employee_id": employee_id, "payroll_month": payroll_month,
                         "external_salary_minor": salary_minor, "entries": entries}
            content_hash = _hash(candidate)
            self.connection.execute(
                "INSERT INTO payroll_calculations(tenant,calculation_id,employee_id,payroll_month,status) VALUES(?,?,?,?, 'draft')",
                (self.tenant, calculation_id, employee_id, payroll_month),
            )
            self.connection.execute(
                "INSERT INTO payroll_calculation_revisions(tenant,calculation_id,revision,draft_id,candidate_identity,content_hash,gross_minor,deductions_minor,net_minor) VALUES(?,?,?,?,?,?,?,?,?)",
                (self.tenant, calculation_id, 1, draft_id, _hash({"calculation_id": calculation_id, "revision": 1}),
                 content_hash, salary_minor, deductions, salary_minor - deductions),
            )
            for entry in entries:
                self.connection.execute(
                    "INSERT INTO payroll_draft_entries(tenant,draft_id,entry_id,component_id,direction,amount_minor,instruction_version_id) VALUES(?,?,?,?,?,?,?)",
                    (self.tenant, draft_id, entry["entry_id"], entry["component_id"], entry["direction"],
                     entry["amount_minor"], entry["instruction_version_id"]),
                )
            control = {"schema_version": 1, "draft_id": draft_id, "revision": 1,
                       "employee_id": employee_id, "payroll_month": payroll_month,
                       "actor": self.actor, "held": False, "cancelled": False, "reason": "created"}
            self.records._put_l1(self.tenant, canonical_key("payroll.draft.control", draft_id, 1), control)
            for index, instruction in enumerate(instructions, 1):
                resolution_id = f"RES{index}"
                value = {"schema_version": 1, "resolution_id": resolution_id, "draft_id": draft_id,
                         "instruction_version_id": instruction["instruction_version_id"], "disposition": "applied",
                         "effects": [{"draft_entry_id": f"{draft_id}.instruction.{index}",
                                      "amount_minor": instruction["amount_minor"], "currency": "INR"}]}
                self._validate_draft_effects(draft_id, value["effects"])
                self.records._put_l1(
                    self.tenant, canonical_key("payroll.instruction.resolution", draft_id, resolution_id), value
                )
            return {"draft_id": draft_id, "content_hash": content_hash,
                    "gross_minor": salary_minor, "deductions_minor": deductions,
                    "net_minor": salary_minor - deductions, "entries": entries}

    def set_draft_control(self, draft_id, held, cancelled, reason, expected_revision):
        with _write(self.connection):
            current = self.records.history_l1(self.tenant, "payroll.draft.control", draft_id)
            if not current or current[-1]["value"]["revision"] != expected_revision:
                raise Conflict("stale control revision")
            previous = current[-1]["value"]
            value = {**previous, "revision": expected_revision + 1, "actor": self.actor,
                     "held": bool(held), "cancelled": bool(cancelled), "reason": reason}
            return self.records._put_l1(
                self.tenant, canonical_key("payroll.draft.control", draft_id, value["revision"]), value
            )["value"]

    def review_draft(self, draft_id, review_id, content_hash, control_revision, decision):
        if decision not in {"approved", "rejected"}:
            raise PayrollError("invalid review decision")
        value = {"schema_version": 1, "review_id": review_id, "draft_id": draft_id,
                 "draft_content_hash": content_hash, "control_revision": control_revision,
                 "actor": self.actor, "decision": decision}
        with _write(self.connection):
            draft = self._draft(draft_id)
            if draft["content_hash"] != content_hash:
                raise PayrollError("review does not bind exact draft content")
            control = self.records.current_l1(self.tenant, "payroll.draft.control", draft_id)
            if control is None or control["value"]["revision"] != control_revision:
                raise Conflict("review control revision is stale")
            return self.records._put_l1(
                self.tenant, canonical_key("payroll.draft.review", draft_id, review_id), value
            )

    def commit(self, draft_id, idempotency_key, expected_control_revision, approval_required=False):
        request = {"draft_id": draft_id, "idempotency_key": idempotency_key,
                   "expected_control_revision": expected_control_revision,
                   "approval_required": bool(approval_required)}
        request_hash = _hash(request)
        with _write(self.connection):
            prior = self._receipt("payroll.commit", draft_id, idempotency_key)
            if prior:
                if prior["value"]["request_hash"] != request_hash:
                    raise Conflict("idempotency key was used with changed input")
                return prior["value"]["outcome"]
            draft = self._draft(draft_id)
            if draft["status"] != "draft":
                raise Conflict("draft was already committed")
            control_record = self.records.current_l1(self.tenant, "payroll.draft.control", draft_id)
            if control_record is None or control_record["value"]["revision"] != expected_control_revision:
                raise Conflict("control revision changed")
            control = control_record["value"]
            if control["held"] or control["cancelled"]:
                raise PayrollError("draft is held or cancelled")
            if approval_required:
                review = self.connection.execute(
                    "SELECT 1 FROM payroll_l1_records WHERE tenant=? "
                    "AND key LIKE 'payroll.draft.review:%' "
                    "AND json_extract(value,'$.draft_id')=? "
                    "AND json_extract(value,'$.draft_content_hash')=? "
                    "AND json_extract(value,'$.control_revision')=? "
                    "AND json_extract(value,'$.decision')='approved'",
                    (self.tenant, draft_id, draft["content_hash"], expected_control_revision),
                ).fetchone()
                if review is None:
                    raise PayrollError("exact draft approval is required")
            draft_entries = self.connection.execute(
                "SELECT * FROM payroll_draft_entries WHERE tenant=? AND draft_id=? ORDER BY rowid",
                (self.tenant, draft_id),
            ).fetchall()
            posted_ids = []
            liability_entry_id = None
            entry_map = {}
            for entry in draft_entries:
                posted_id = _stable_id("PE", draft_id, entry["entry_id"])
                posted_direction = entry["direction"]
                self.connection.execute(
                    "INSERT INTO payroll_ledger_entries(tenant,ledger_entry_id,draft_id,employee_id,payroll_month,component_id,direction,amount_minor) VALUES(?,?,?,?,?,?,?,?)",
                    (self.tenant, posted_id, draft_id, draft["employee_id"], draft["payroll_month"],
                     entry["component_id"], posted_direction, entry["amount_minor"]),
                )
                posted_ids.append(posted_id)
                entry_map[entry["entry_id"]] = posted_id
                if entry["direction"] == "employer_liability":
                    liability_entry_id = posted_id
            resolutions = self.connection.execute(
                "SELECT value FROM payroll_l1_records WHERE tenant=? "
                "AND key LIKE 'payroll.instruction.resolution:%' "
                "AND json_extract(value,'$.draft_id')=?",
                (self.tenant, draft_id),
            ).fetchall()
            for row in resolutions:
                resolution = json.loads(row["value"])
                instruction = self.connection.execute(
                    "SELECT v.instruction_id,i.cadence FROM payroll_instruction_versions v "
                    "JOIN payroll_instructions i ON i.tenant=v.tenant AND i.instruction_id=v.instruction_id "
                    "WHERE v.tenant=? AND v.instruction_version_id=?",
                    (self.tenant, resolution["instruction_version_id"]),
                ).fetchone()
                effects = [{"ledger_entry_id": entry_map[item["draft_entry_id"]],
                            "amount_minor": item["amount_minor"], "currency": item["currency"]}
                           for item in resolution["effects"]]
                self._validate_posted_effects(draft_id, effects)
                application_id = _stable_id("APP", instruction["instruction_id"], draft["employee_id"],
                                            draft["payroll_month"] if instruction["cadence"] == "monthly" else "one-time")
                application = {"schema_version": 1, "application_id": application_id,
                               "instruction_id": instruction["instruction_id"],
                               "instruction_version_id": resolution["instruction_version_id"],
                               "employee_id": draft["employee_id"], "payroll_month": draft["payroll_month"],
                               "draft_id": draft_id, "cadence": instruction["cadence"], "effects": effects}
                try:
                    self.records._put_l1(
                        self.tenant,
                        canonical_key("payroll.instruction.application", resolution["instruction_version_id"], application_id),
                        application,
                    )
                except sqlite3.IntegrityError as exc:
                    raise Conflict("instruction was already consumed in its stable scope") from exc
            self.connection.execute(
                "UPDATE payroll_calculations SET status='committed' WHERE tenant=? AND calculation_id=? AND status='draft'",
                (self.tenant, draft["calculation_id"]),
            )
            outcome = {"status": "committed", "draft_id": draft_id,
                       "posted_entry_ids": posted_ids,
                       "employer_liability_entry_id": liability_entry_id}
            receipt_id = _stable_id("RCPT", self.tenant, self.actor, "payroll.commit", draft_id, idempotency_key)
            receipt = {"schema_version": 1, "receipt_id": receipt_id, "operation": "payroll.commit",
                       "subject_id": draft_id, "executor": self.actor,
                       "idempotency_key": idempotency_key, "request_hash": request_hash,
                       "outcome": outcome,
                       "before": {"calculation_status": "draft", "control_revision": expected_control_revision},
                       "after": {"calculation_status": "committed", "posted_entry_ids": posted_ids}}
            self.records._put_l1(
                self.tenant, canonical_key("payroll.operation.receipt", draft_id, receipt_id), receipt
            )
            return outcome

    def instruction_application(self, instruction_id, employee_id, payroll_month):
        row = self.connection.execute(
            "SELECT tenant,key,value,ts,state FROM payroll_l1_records WHERE tenant=? "
            "AND key LIKE 'payroll.instruction.application:%' "
            "AND json_extract(value,'$.instruction_id')=? "
            "AND json_extract(value,'$.employee_id')=? "
            "AND json_extract(value,'$.payroll_month')=?",
            (self.tenant, instruction_id, employee_id, payroll_month),
        ).fetchone()
        if row is None:
            return None
        return {"tenant": row["tenant"], "key": row["key"], "value": json.loads(row["value"]),
                "ts": row["ts"], "state": row["state"]}

    def record_obligation(self, obligation_id, ledger_entry_id, amount_minor):
        _identifier(obligation_id, "obligation", identity=True)
        _identifier(ledger_entry_id, "ledger entry", identity=True)
        _positive_minor_units(amount_minor)
        with _write(self.connection):
            entry = self.connection.execute(
                "SELECT direction,amount_minor FROM payroll_ledger_entries "
                "WHERE tenant=? AND ledger_entry_id=?",
                (self.tenant, ledger_entry_id),
            ).fetchone()
            if (entry is None or entry["direction"] != "employer_liability" or
                    entry["amount_minor"] != amount_minor):
                raise PayrollError("obligation must exactly match a posted employer liability")
            if self.connection.execute(
                "SELECT 1 FROM payroll_statutory_obligations WHERE tenant=? AND ledger_entry_id=?",
                (self.tenant, ledger_entry_id),
            ).fetchone():
                raise Conflict("posted employer liability already has an obligation")
            self.connection.execute(
                "INSERT INTO payroll_statutory_obligations(tenant,obligation_id,ledger_entry_id,amount_minor) VALUES(?,?,?,?)",
                (self.tenant, obligation_id, ledger_entry_id, amount_minor),
            )

    def record_remittance(self, remittance_id, amount_minor, proof_ref):
        _identifier(remittance_id, "remittance", identity=True)
        _positive_minor_units(amount_minor)
        if not isinstance(proof_ref, str) or not proof_ref.strip():
            raise PayrollError("remittance requires a nonempty proof reference")
        with _write(self.connection):
            self.connection.execute(
                "INSERT INTO payroll_statutory_remittances(tenant,remittance_id,amount_minor,proof_ref) VALUES(?,?,?,?)",
                (self.tenant, remittance_id, amount_minor, proof_ref),
            )

    def allocate_remittance(self, allocation_id, obligation_id, remittance_id, amount_minor):
        for value, label in ((allocation_id, "allocation"), (obligation_id, "obligation"),
                             (remittance_id, "remittance")):
            _identifier(value, label, identity=True)
        _positive_minor_units(amount_minor)
        with _write(self.connection):
            obligation = self.connection.execute(
                "SELECT amount_minor FROM payroll_statutory_obligations WHERE tenant=? AND obligation_id=?",
                (self.tenant, obligation_id),
            ).fetchone()
            remittance = self.connection.execute(
                "SELECT amount_minor FROM payroll_statutory_remittances WHERE tenant=? AND remittance_id=?",
                (self.tenant, remittance_id),
            ).fetchone()
            if obligation is None or remittance is None:
                raise PayrollError("invalid allocation")
            allocated_obligation = self.connection.execute(
                "SELECT COALESCE(SUM(amount_minor),0) FROM payroll_statutory_allocations WHERE tenant=? AND obligation_id=?",
                (self.tenant, obligation_id),
            ).fetchone()[0]
            allocated_remittance = self.connection.execute(
                "SELECT COALESCE(SUM(amount_minor),0) FROM payroll_statutory_allocations WHERE tenant=? AND remittance_id=?",
                (self.tenant, remittance_id),
            ).fetchone()[0]
            if allocated_obligation + amount_minor > obligation["amount_minor"] or allocated_remittance + amount_minor > remittance["amount_minor"]:
                raise PayrollError("allocation exceeds obligation or remittance")
            self.connection.execute(
                "INSERT INTO payroll_statutory_allocations(tenant,allocation_id,obligation_id,remittance_id,amount_minor) VALUES(?,?,?,?,?)",
                (self.tenant, allocation_id, obligation_id, remittance_id, amount_minor),
            )

    def elr_outstanding(self, obligation_id):
        row = self.connection.execute(
            "SELECT o.amount_minor-COALESCE(SUM(a.amount_minor),0) outstanding "
            "FROM payroll_statutory_obligations o LEFT JOIN payroll_statutory_allocations a "
            "ON a.tenant=o.tenant AND a.obligation_id=o.obligation_id "
            "WHERE o.tenant=? AND o.obligation_id=? GROUP BY o.amount_minor",
            (self.tenant, obligation_id),
        ).fetchone()
        if row is None:
            raise PayrollError("unknown obligation")
        return row["outstanding"]

    def _draft(self, draft_id):
        row = self.connection.execute(
            "SELECT c.calculation_id,c.employee_id,c.payroll_month,c.status,r.content_hash "
            "FROM payroll_calculations c JOIN payroll_calculation_revisions r "
            "ON r.tenant=c.tenant AND r.calculation_id=c.calculation_id "
            "WHERE c.tenant=? AND r.draft_id=?",
            (self.tenant, draft_id),
        ).fetchone()
        if row is None:
            raise PayrollError("unknown draft")
        return dict(row)

    def _receipt(self, operation, subject_id, idempotency_key):
        row = self.connection.execute(
            "SELECT tenant,key,value,ts,state FROM payroll_l1_records WHERE tenant=? "
            "AND key LIKE 'payroll.operation.receipt:%' "
            "AND json_extract(value,'$.executor')=? AND json_extract(value,'$.operation')=? "
            "AND json_extract(value,'$.subject_id')=? AND json_extract(value,'$.idempotency_key')=?",
            (self.tenant, self.actor, operation, subject_id, idempotency_key),
        ).fetchone()
        if row is None:
            return None
        return {"value": json.loads(row["value"]), "state": row["state"]}

    def _store_receipt(self, operation, subject_id, idempotency_key, request_hash,
                       outcome, before, after):
        receipt_id = _stable_id(
            "RCPT", self.tenant, self.actor, operation, subject_id, idempotency_key
        )
        value = {"schema_version": 1, "receipt_id": receipt_id, "operation": operation,
                 "subject_id": subject_id, "executor": self.actor,
                 "idempotency_key": idempotency_key, "request_hash": request_hash,
                 "outcome": outcome, "before": before, "after": after}
        self.records._put_l1(
            self.tenant,
            canonical_key("payroll.operation.receipt", subject_id, receipt_id),
            value,
        )

    def _validate_draft_effects(self, draft_id, effects):
        for effect in effects:
            row = self.connection.execute(
                "SELECT amount_minor FROM payroll_draft_entries WHERE tenant=? AND draft_id=? AND entry_id=?",
                (self.tenant, draft_id, effect["draft_entry_id"]),
            ).fetchone()
            if row is None or row["amount_minor"] != effect["amount_minor"]:
                raise PayrollError("resolution effect does not match canonical draft entry")

    def _validate_posted_effects(self, draft_id, effects):
        for effect in effects:
            row = self.connection.execute(
                "SELECT amount_minor FROM payroll_ledger_entries WHERE tenant=? AND draft_id=? AND ledger_entry_id=?",
                (self.tenant, draft_id, effect["ledger_entry_id"]),
            ).fetchone()
            if row is None or row["amount_minor"] != effect["amount_minor"]:
                raise PayrollError("application effect does not match canonical posted entry")

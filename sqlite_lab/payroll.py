"""Named payroll operations for the three-ledger SQLite simulation."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from .records import MONTH, RecordStore, canonical_key, parse_key, _identifier

class PayrollError(RuntimeError):
    pass


class Conflict(PayrollError):
    pass

def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def _stable(prefix,*parts): return prefix+hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:20]
def _money(value):
    if type(value) is not int or value <= 0: raise PayrollError("amount must be positive integer minor units")
    return value
@contextmanager
def _write(connection):
    connection.execute("BEGIN IMMEDIATE")
    try: yield
    except BaseException:
        connection.rollback()
        raise
    else:
        connection.commit()

class Payroll:
    def __init__(self,connection,tenant,actor):
        self.connection = connection
        self.tenant = _identifier(tenant, "tenant")
        self.actor = _identifier(actor, "actor")
        self.records = RecordStore(connection)

    def define_component(self,component_id,revision,code,label,kind,country_code):
        value={"schema_version":1,"component_id":component_id,"revision":revision,"code":code,"label":label,"kind":kind,"country_code":country_code}
        with _write(self.connection):
            history=self.records.history_l1(self.tenant,"payroll.component",component_id)
            if history and any(value[f]!=history[0]["value"][f] for f in ("code","kind","country_code")):
                raise Conflict("component identity fields cannot change")
            collision=self.connection.execute("SELECT 1 FROM payroll_l1_records WHERE tenant=? AND key LIKE 'payroll.component:%' AND json_extract(value,'$.country_code')=? AND json_extract(value,'$.code')=? AND json_extract(value,'$.component_id')<>?",(self.tenant,country_code,code,component_id)).fetchone()
            if collision: raise Conflict("component code already owned in tenant/country scope")
            try: return self.records._put_l1(self.tenant,canonical_key("payroll.component",component_id,revision),value)
            except sqlite3.IntegrityError as exc: raise Conflict("component identity conflict") from exc

    def disable_component(self,component_id,expected_revision,reason="disabled"):
        with _write(self.connection):
            history=self.records.history_l1(self.tenant,"payroll.component",component_id)
            if not history or history[-1]["value"]["revision"]!=expected_revision: raise Conflict("stale component revision")
            value = dict(history[-1]["value"])
            value["revision"] = expected_revision + 1
            return self.records._put_l1(self.tenant,canonical_key("payroll.component",component_id,value["revision"]),value,"disabled")

    def define_earning(self,earning_id,revision,employee_id,component_key,amount_minor,effective_from,effective_until=None):
        value={"schema_version":1,"earning_id":earning_id,"revision":revision,"employee_id":employee_id,"component_key":component_key,"amount_minor":amount_minor,"effective_from":effective_from,"effective_until":effective_until}
        with _write(self.connection):
            self._component(component_key, require_available=True)
            _money(amount_minor)
            return self.records._put_l1(self.tenant,canonical_key("payroll.earning",earning_id,revision),value)

    def add_instruction(self,instruction_id,version_id,revision,employee_id,component_key,amount_minor,cadence,start_month,end_month=None):
        value={"schema_version":1,"instruction_id":instruction_id,"revision":revision,"version_id":version_id,"employee_id":employee_id,"component_key":component_key,"amount_minor":amount_minor,"cadence":cadence,"effective_from":start_month,"effective_until":end_month}
        request_hash=_hash(value)
        with _write(self.connection):
            prior=self._receipt("payroll.instruction.create",instruction_id,version_id)
            if prior:
                if prior["value"]["request_hash"]!=request_hash: raise Conflict("instruction retry changed input")
                return self.records.get_l1(self.tenant,prior["value"]["outcome"]["instruction_key"])
            self._component(component_key, True)
            _money(amount_minor)
            row=self.records._put_l1(self.tenant,canonical_key("payroll.instruction",instruction_id,revision),value)
            outcome={"status":"created","instruction_key":row["key"],"version_id":version_id}
            self._store_receipt("payroll.instruction.create",instruction_id,version_id,request_hash,outcome,{"instruction_exists":False},{"instruction_key":row["key"]})
            return row

    def add_instruction_version(self,instruction_id,version_id,revision,component_key,amount_minor):
        history=self.records.history_l1(self.tenant,"payroll.instruction",instruction_id)
        if not history or revision!=history[-1]["value"]["revision"]+1: raise Conflict("instruction revision is not next")
        old=history[-1]["value"]
        value={**old,"revision":revision,"version_id":version_id,"component_key":component_key,"amount_minor":amount_minor}
        request_hash=_hash(value)
        with _write(self.connection):
            prior=self._receipt("payroll.instruction.version",instruction_id,version_id)
            if prior:
                if prior["value"]["request_hash"]!=request_hash: raise Conflict("instruction version retry changed input")
                return self.records.get_l1(self.tenant,prior["value"]["outcome"]["instruction_key"])
            self._component(component_key, True)
            _money(amount_minor)
            row=self.records._put_l1(self.tenant,canonical_key("payroll.instruction",instruction_id,revision),value)
            self._store_receipt("payroll.instruction.version",instruction_id,version_id,request_hash,{"status":"version_created","instruction_key":row["key"],"version_id":version_id},{"latest_revision":revision-1},{"latest_revision":revision})
            return row

    def create_draft(self,draft_id,employee_id,payroll_month,earning_keys,instruction_version_ids):
        _identifier(draft_id, "draft", True)
        _identifier(employee_id, "employee", True)
        if not MONTH.fullmatch(payroll_month): raise PayrollError("invalid payroll month")
        with _write(self.connection):
            sources=[]
            for key in earning_keys:
                sources.append(
                    (self._source(key, "payroll.earning", employee_id, payroll_month), False)
                )
            instruction_keys=[]
            for identity in instruction_version_ids:
                key=self._instruction_key(identity)
                record=self._source(key,"payroll.instruction",employee_id,payroll_month,allow_expired=True)
                if payroll_month<record["effective_from"] or (record["effective_until"] and payroll_month>record["effective_until"]): continue
                sources.append((record, True))
                instruction_keys.append(key)
            lines = []
            resolutions = []
            for source,is_instruction in sources:
                component=self._component(source["component_key"],True)["value"]
                kind = component["kind"]
                amount = source["amount_minor"]
                source_key = canonical_key(
                    "payroll.instruction" if is_instruction else "payroll.earning",
                    source["instruction_id"] if is_instruction else source["earning_id"],
                    source["revision"],
                )
                directions=("employer_expense","employer_liability") if kind=="employer_contribution" else (("deduction",) if kind=="deduction" else ("earning",))
                effect_ids=[]
                for direction in directions:
                    entry_id = _stable("DE", draft_id, source_key, direction)
                    effect_ids.append(entry_id)
                    lines.append({"entry_id":entry_id,"source_key":source_key,"component_key":source["component_key"],"direction":direction,"amount_minor":amount})
                if is_instruction: resolutions.append((source,effect_ids))
            gross=sum(x["amount_minor"] for x in lines if x["direction"] in {"earning","employer_expense"})
            deductions=sum(x["amount_minor"] for x in lines if x["direction"] in {"deduction","employer_liability"})
            content={"employee_id":employee_id,"payroll_month":payroll_month,"earning_keys":list(earning_keys),"instruction_keys":instruction_keys,"lines":lines}
            value={"schema_version":1,"draft_id":draft_id,"revision":1,"employee_id":employee_id,"payroll_month":payroll_month,"earning_keys":list(earning_keys),"instruction_keys":instruction_keys,"content_hash":_hash(content),"gross_minor":gross,"deductions_minor":deductions,"net_minor":gross-deductions}
            draft = self.records._put_l1(
                self.tenant, canonical_key("payroll.draft", draft_id, 1), value
            )
            for line in lines:
                self.connection.execute("INSERT INTO payroll_draft_ledger(tenant,draft_key,entry_id,employee_id,payroll_month,source_key,component_key,direction,amount_minor,currency) VALUES(?,?,?,?,?,?,?,?,?,'INR')",(self.tenant,draft["key"],line["entry_id"],employee_id,payroll_month,line["source_key"],line["component_key"],line["direction"],line["amount_minor"]))
            control={"schema_version":1,"draft_id":draft_id,"revision":1,"employee_id":employee_id,"payroll_month":payroll_month,"actor":self.actor,"held":False,"cancelled":False,"reason":"created"}
            self.records._put_l1(self.tenant,canonical_key("payroll.draft.control",draft_id,1),control)
            for index,(source,effect_ids) in enumerate(resolutions,1):
                effects=[{"draft_entry_id":eid,"amount_minor":source["amount_minor"],"currency":"INR"} for eid in effect_ids]
                value2={"schema_version":1,"resolution_id":f"RES{index}","draft_id":draft_id,"instruction_id":source["instruction_id"],"instruction_key":canonical_key("payroll.instruction",source["instruction_id"],source["revision"]),"disposition":"applied","effects":effects}
                self.records._put_l1(self.tenant,canonical_key("payroll.instruction.resolution",draft_id,f"RES{index}"),value2)
            return {**draft,**value,"entries":lines}

    def set_draft_control(self,draft_id,held,cancelled,reason,expected_revision):
        with _write(self.connection):
            h=self.records.history_l1(self.tenant,"payroll.draft.control",draft_id)
            if not h or h[-1]["value"]["revision"]!=expected_revision: raise Conflict("stale control revision")
            value={**h[-1]["value"],"revision":expected_revision+1,"actor":self.actor,"held":bool(held),"cancelled":bool(cancelled),"reason":reason}
            return self.records._put_l1(self.tenant,canonical_key("payroll.draft.control",draft_id,value["revision"]),value)["value"]

    def review_draft(self,draft_id,review_id,content_hash,control_revision,decision):
        if decision not in {"approved","rejected"}: raise PayrollError("invalid review")
        with _write(self.connection):
            draft = self._draft(draft_id)
            control = self.records.current_l1(
                self.tenant, "payroll.draft.control", draft_id
            )
            if draft["content_hash"]!=content_hash: raise PayrollError("review does not bind draft")
            if not control or control["value"]["revision"]!=control_revision: raise Conflict("stale review control")
            value={"schema_version":1,"review_id":review_id,"draft_id":draft_id,"draft_content_hash":content_hash,"control_revision":control_revision,"actor":self.actor,"decision":decision}
            return self.records._put_l1(self.tenant,canonical_key("payroll.draft.review",draft_id,review_id),value)

    def commit(self,draft_id,idempotency_key,expected_control_revision,approval_required=False):
        request = {
            "draft_id": draft_id,
            "idempotency_key": idempotency_key,
            "expected_control_revision": expected_control_revision,
            "approval_required": bool(approval_required),
        }
        request_hash = _hash(request)
        with _write(self.connection):
            prior=self._receipt("payroll.commit",draft_id,idempotency_key)
            if prior:
                if prior["value"]["request_hash"] != request_hash:
                    raise Conflict("retry changed input")
                return prior["value"]["outcome"]
            draft = self._draft(draft_id)
            draft_key = canonical_key("payroll.draft", draft_id, 1)
            if self.connection.execute("SELECT 1 FROM payroll_ledger WHERE tenant=? AND draft_key=?",(self.tenant,draft_key)).fetchone(): raise Conflict("draft already committed")
            control=self.records.current_l1(self.tenant,"payroll.draft.control",draft_id)
            if not control or control["value"]["revision"]!=expected_control_revision: raise Conflict("control changed")
            if control["value"]["held"] or control["value"]["cancelled"]: raise PayrollError("draft held or cancelled")
            if approval_required and not self.connection.execute("SELECT 1 FROM payroll_l1_records WHERE tenant=? AND key LIKE 'payroll.draft.review:%' AND json_extract(value,'$.draft_id')=? AND json_extract(value,'$.draft_content_hash')=? AND json_extract(value,'$.control_revision')=? AND json_extract(value,'$.decision')='approved'",(self.tenant,draft_id,draft["content_hash"],expected_control_revision)).fetchone(): raise PayrollError("approval required")
            rows = self.connection.execute(
                "SELECT * FROM payroll_draft_ledger "
                "WHERE tenant=? AND draft_key=? ORDER BY rowid",
                (self.tenant, draft_key),
            ).fetchall()
            posted = []
            mapping = {}
            liability = None
            for row in rows:
                posted_id = _stable("PE", draft_id, row["entry_id"])
                mapping[row["entry_id"]] = posted_id
                posted.append(posted_id)
                self.connection.execute("INSERT INTO payroll_ledger(tenant,ledger_entry_id,draft_key,draft_entry_id,employee_id,payroll_month,source_key,component_key,direction,amount_minor,currency) VALUES(?,?,?,?,?,?,?,?,?,?,'INR')",(self.tenant,posted_id,draft_key,row["entry_id"],row["employee_id"],row["payroll_month"],row["source_key"],row["component_key"],row["direction"],row["amount_minor"]))
                if row["direction"] == "employer_liability":
                    liability = posted_id
            for rr in self.connection.execute("SELECT value FROM payroll_l1_records WHERE tenant=? AND key LIKE 'payroll.instruction.resolution:%' AND json_extract(value,'$.draft_id')=?",(self.tenant,draft_id)):
                resolution = json.loads(rr[0])
                instruction = self.records.get_l1(
                    self.tenant, resolution["instruction_key"]
                )["value"]
                effects=[{"ledger_entry_id":mapping[e["draft_entry_id"]],"amount_minor":e["amount_minor"],"currency":"INR"} for e in resolution["effects"]]
                aid=_stable("APP",instruction["instruction_id"],draft["employee_id"],draft["payroll_month"] if instruction["cadence"]=="monthly" else "one-time")
                app={"schema_version":1,"application_id":aid,"instruction_id":instruction["instruction_id"],"instruction_key":resolution["instruction_key"],"version_id":instruction["version_id"],"employee_id":draft["employee_id"],"payroll_month":draft["payroll_month"],"draft_id":draft_id,"cadence":instruction["cadence"],"effects":effects}
                try: self.records._put_l1(self.tenant,canonical_key("payroll.instruction.application",instruction["version_id"],aid),app)
                except sqlite3.IntegrityError as exc: raise Conflict("instruction already consumed") from exc
            outcome={"status":"committed","draft_id":draft_id,"draft_key":draft_key,"posted_entry_ids":posted,"employer_liability_entry_id":liability}
            self._store_receipt(
                "payroll.commit",
                draft_id,
                idempotency_key,
                request_hash,
                outcome,
                {"committed": False, "control_revision": expected_control_revision},
                {"committed": True, "posted_entry_ids": posted},
            )
            return outcome

    def instruction_application(self,instruction_id,employee_id,payroll_month):
        row=self.connection.execute("SELECT tenant,key,value,ts,state FROM payroll_l1_records WHERE tenant=? AND key LIKE 'payroll.instruction.application:%' AND json_extract(value,'$.instruction_id')=? AND json_extract(value,'$.employee_id')=? AND json_extract(value,'$.payroll_month')=?",(self.tenant,instruction_id,employee_id,payroll_month)).fetchone()
        return None if row is None else {"tenant":row[0],"key":row[1],"value":json.loads(row[2]),"ts":row[3],"state":row[4]}

    def record_obligation(self,entry_id,posted_liability_entry_id,amount_minor):
        _identifier(entry_id, "obligation entry", True)
        _identifier(posted_liability_entry_id, "posted liability entry", True)
        _money(amount_minor)
        with _write(self.connection):
            try: self.connection.execute("INSERT INTO payroll_employer_liability_ledger(tenant,entry_id,row_kind,amount_minor,posted_liability_entry_id) VALUES(?,?,'obligation',?,?)",(self.tenant,entry_id,amount_minor,posted_liability_entry_id))
            except sqlite3.IntegrityError as exc: raise Conflict("invalid or duplicate liability obligation") from exc
    def record_remittance(self,entry_id,amount_minor,proof_ref):
        _identifier(entry_id, "remittance entry", True)
        _money(amount_minor)
        if not isinstance(proof_ref,str) or not proof_ref.strip(): raise PayrollError("remittance proof required")
        with _write(self.connection): self.connection.execute("INSERT INTO payroll_employer_liability_ledger(tenant,entry_id,row_kind,amount_minor,proof_ref) VALUES(?,?,'remittance',?,?)",(self.tenant,entry_id,amount_minor,proof_ref))
    def allocate_remittance(self,entry_id,obligation_id,remittance_id,amount_minor):
        _identifier(entry_id, "allocation entry", True)
        _identifier(obligation_id, "obligation entry", True)
        _identifier(remittance_id, "remittance entry", True)
        _money(amount_minor)
        with _write(self.connection):
            o = self.connection.execute("SELECT amount_minor FROM payroll_employer_liability_ledger WHERE tenant=? AND entry_id=? AND row_kind='obligation'",(self.tenant,obligation_id)).fetchone()
            r = self.connection.execute("SELECT amount_minor FROM payroll_employer_liability_ledger WHERE tenant=? AND entry_id=? AND row_kind='remittance'",(self.tenant,remittance_id)).fetchone()
            oa = self.connection.execute("SELECT COALESCE(SUM(amount_minor),0) FROM payroll_employer_liability_ledger WHERE tenant=? AND row_kind='allocation' AND obligation_entry_id=?",(self.tenant,obligation_id)).fetchone()[0]
            ra = self.connection.execute("SELECT COALESCE(SUM(amount_minor),0) FROM payroll_employer_liability_ledger WHERE tenant=? AND row_kind='allocation' AND remittance_entry_id=?",(self.tenant,remittance_id)).fetchone()[0]
            if not o or not r or oa+amount_minor>o[0] or ra+amount_minor>r[0]: raise PayrollError("allocation exceeds obligation or remittance")
            self.connection.execute("INSERT INTO payroll_employer_liability_ledger(tenant,entry_id,row_kind,amount_minor,obligation_entry_id,remittance_entry_id) VALUES(?,?,'allocation',?,?,?)",(self.tenant,entry_id,amount_minor,obligation_id,remittance_id))
    def elr_outstanding(self,obligation_id):
        row=self.connection.execute("SELECT o.amount_minor-COALESCE(SUM(a.amount_minor),0) FROM payroll_employer_liability_ledger o LEFT JOIN payroll_employer_liability_ledger a ON a.tenant=o.tenant AND a.row_kind='allocation' AND a.obligation_entry_id=o.entry_id WHERE o.tenant=? AND o.entry_id=? AND o.row_kind='obligation' GROUP BY o.amount_minor",(self.tenant,obligation_id)).fetchone()
        if not row: raise PayrollError("unknown obligation")
        return row[0]

    def _component(self,key,require_available=False):
        if parse_key(key)[0]!="payroll.component": raise PayrollError("wrong component reference type")
        row=self.records.get_l1(self.tenant,key)
        if not row: raise PayrollError("missing component")
        if require_available:
            subject = parse_key(key)[1]
            current = self.records.current_l1(
                self.tenant, "payroll.component", subject
            )
            if not current or current["key"]!=key: raise PayrollError("component not currently available")
        return row
    def _source(self,key,kind,employee,month,allow_expired=False):
        record_type, subject, _ = parse_key(key)
        if record_type!=kind: raise PayrollError("source reference type mismatch")
        row=self.records.get_l1(self.tenant,key)
        if not row or row["state"]!="enabled": raise PayrollError("missing source")
        current = self.records.current_l1(self.tenant, kind, subject)
        if not current or current["key"] != key:
            raise PayrollError("source is not current authority")
        value=row["value"]
        if value["employee_id"]!=employee: raise PayrollError("source outside employee scope")
        if not allow_expired and (month<value["effective_from"] or (value["effective_until"] and month>value["effective_until"])): raise PayrollError("earning outside effective period")
        return value
    def _instruction_key(self,identity):
        _identifier(identity, "instruction version", True)
        row=self.connection.execute("SELECT key FROM payroll_l1_records WHERE tenant=? AND key LIKE 'payroll.instruction:%' AND json_extract(value,'$.version_id')=?",(self.tenant,identity)).fetchone()
        if not row: raise PayrollError("unknown instruction version")
        return row[0]
    def _draft(self,draft_id):
        row=self.records.get_l1(self.tenant,canonical_key("payroll.draft",draft_id,1))
        if not row: raise PayrollError("unknown draft")
        return row["value"]
    def _receipt(self,operation,subject,idempotency):
        row=self.connection.execute("SELECT value FROM payroll_l1_records WHERE tenant=? AND key LIKE 'payroll.operation.receipt:%' AND json_extract(value,'$.executor')=? AND json_extract(value,'$.operation')=? AND json_extract(value,'$.subject_id')=? AND json_extract(value,'$.idempotency_key')=?",(self.tenant,self.actor,operation,subject,idempotency)).fetchone()
        return None if not row else {"value":json.loads(row[0])}
    def _store_receipt(self,operation,subject,idempotency,request_hash,outcome,before,after):
        rid = _stable("RCPT", self.tenant, self.actor, operation, subject, idempotency)
        value = {
            "schema_version": 1,
            "receipt_id": rid,
            "operation": operation,
            "subject_id": subject,
            "executor": self.actor,
            "idempotency_key": idempotency,
            "request_hash": request_hash,
            "outcome": outcome,
            "before": before,
            "after": after,
        }
        self.records._put_l1(self.tenant,canonical_key("payroll.operation.receipt",subject,rid),value)

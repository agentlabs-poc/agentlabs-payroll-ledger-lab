"""Export a six-month payroll journey as actual SQLite snapshots."""
from __future__ import annotations

import argparse, hashlib, json, sqlite3, tempfile
from pathlib import Path
from .payroll import Payroll, PayrollError
from .records import RecordStore, connect

TABLES=("payroll_l1_records","payroll_l2_records","payroll_draft_ledger","payroll_ledger","payroll_employer_liability_ledger")
L1_TYPES=("payroll.component","payroll.earning","payroll.instruction","payroll.draft","payroll.draft.control","payroll.draft.review","payroll.instruction.resolution","payroll.instruction.application","payroll.operation.receipt")
MONTHS=("2026-10","2026-11","2026-12","2027-01","2027-02","2027-03")
EXPECTED={
 ("E101","2026-10"):(5_550_000,600_000,4_950_000),("E101","2026-11"):(6_150_000,650_000,5_500_000),
 ("E101","2026-12"):(5_850_000,650_000,5_200_000),("E101","2027-01"):(5_850_000,600_000,5_250_000),
 ("E101","2027-02"):(5_850_000,600_000,5_250_000),("E101","2027-03"):(5_850_000,400_000,5_450_000),
 ("E102","2026-10"):(3_800_000,200_000,3_600_000),("E102","2026-11"):(3_800_000,200_000,3_600_000),
 ("E102","2026-12"):(3_840_000,200_000,3_640_000),("E102","2027-01"):(3_820_000,200_000,3_620_000),
 ("E102","2027-02"):(3_820_000,200_000,3_620_000),("E102","2027-03"):(3_820_000,200_000,3_620_000),
}

def _rows(db,table):
 rows=[dict(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
 if table in TABLES[:2]:
  for row in rows: row["value"]=json.loads(row["value"])
 return rows

def _liability(db):
 result={"due_minor":0,"paid_minor":0,"allocated_minor":0}
 names={"obligation":"due_minor","remittance":"paid_minor","allocation":"allocated_minor"}
 for row in db.execute("SELECT row_kind,SUM(amount_minor) amount FROM payroll_employer_liability_ledger GROUP BY row_kind"):
  result[names[row["row_kind"]]]=row["amount"]
 return {**result,"outstanding_minor":result["due_minor"]-result["allocated_minor"]}

def _totals(draft):
 return None if draft is None else {key:draft[key] for key in ("gross_minor","deductions_minor","net_minor")}

def build_demo():
 root=Path(__file__).parent
 with tempfile.TemporaryDirectory() as directory:
  db=connect(Path(directory)/"demo.sqlite3"); payroll=Payroll(db,"T1","payroll-admin")
  stages=[]; obligations={}; posted_sources={}
  def capture(id,title,explanation,employee=None,month=None,draft=None,outcome=None):
   context={"employee_id":employee,"payroll_month":month}
   if draft: context["draft_key"]=draft["key"]
   stages.append({"id":id,"title":title,"explanation":explanation,"context":context,
    "outcome":outcome or {"status":"observed"},"summary":{"payroll":_totals(draft),"liability":_liability(db)},
    "tables":{table:_rows(db,table) for table in TABLES}})
  def reject(call):
   try: call()
   except PayrollError as error: return {"status":"rejected","reason":str(error)}
   raise AssertionError("expected rejection")
  def after_commit(employee,month,outcome):
   marks=",".join("?"*len(outcome["posted_entry_ids"]))
   for row in db.execute(f"SELECT ledger_entry_id,source_key FROM payroll_ledger WHERE tenant='T1' AND ledger_entry_id IN ({marks})",outcome["posted_entry_ids"]):
    posted_sources[(employee,month,row["source_key"])]=row["ledger_entry_id"]
   for posted_id in outcome["employer_liability_entry_ids"]:
    row=db.execute("SELECT component_key,amount_minor FROM payroll_ledger WHERE tenant='T1' AND ledger_entry_id=?",(posted_id,)).fetchone()
    family="A" if ":EMPLOYER-A:" in row["component_key"] else "B"; oid=f"OB-{family}-{employee}-{month}"
    payroll.record_obligation(oid,posted_id,row["amount_minor"],employer_id="EMPLOYER1",authority_id=f"AUTHORITY-{family}",currency="INR",reporting_period=month)
    obligations[(family,employee,month)]=oid

  capture("empty","Fresh SQLite database","The five canonical tables begin empty.")
  components={}
  for cid,kind in (("BASIC","earning"),("HRA","earning"),("EMPLOYER-A","employer_contribution"),("EMPLOYER-B","employer_contribution"),("ALLOWANCE","earning"),("LOAN","deduction"),("BONUS","earning"),("RECOVERY","deduction")):
   components[cid]=payroll.define_component(cid,1,cid.lower(),cid.replace("-"," ").title(),kind,"IN")["key"]
  earnings={"E101":{},"E102":{}}
  for employee,amounts in (("E101",(3_000_000,2_000_000,300_000,100_000)),("E102",(2_500_000,1_000_000,150_000,50_000))):
   for eid,cid,amount in zip(("EARN-BASIC","EARN-HRA","EARN-EMPLOYER","EARN-EMPLOYER-B"),("BASIC","HRA","EMPLOYER-A","EMPLOYER-B"),amounts):
    earnings[employee][eid]=payroll.define_earning(eid,1,employee,components[cid],amount,"2026-10")["key"]
  allowance={
   "E101":payroll.add_instruction("I-ALLOWANCE","ALLOW-E101-1",1,"E101",components["ALLOWANCE"],150_000,"monthly","2026-10"),
   "E102":payroll.add_instruction("I-ALLOWANCE","ALLOW-E102-1",1,"E102",components["ALLOWANCE"],100_000,"monthly","2026-10"),
  }
  loan=payroll.add_instruction("I-LOAN","LOAN-E101-1",1,"E101",components["LOAN"],200_000,"monthly","2026-10","2027-02")
  future_allowance=payroll.add_instruction_version("I-ALLOWANCE","ALLOW-E101-2",2,"E101",components["ALLOWANCE"],150_000,effective_from="2027-01")
  same_retry=payroll.add_instruction_version("I-ALLOWANCE","ALLOW-E101-2",2,"E101",components["ALLOWANCE"],150_000,effective_from="2027-01")
  changed_retry=reject(lambda:payroll.add_instruction_version("I-ALLOWANCE","ALLOW-E101-2",2,"E101",components["ALLOWANCE"],160_000,effective_from="2027-01"))
  RecordStore(db).put_l2_settings("T1",{"schema_version":1,"employee_id":"E101","revision":1,"effective_from":"2026-10","policy_ref":{"id":"INDIA-PAYROLL","revision":1},"payslip_locale":"en-IN"}); db.commit()
  capture("sources","Manager-supplied source records","Shared component meanings and employee-owned amounts are explicit. Both employees reuse local IDs safely.",outcome={"status":"created","same_instruction_retry":same_retry["key"],"changed_instruction_retry":changed_retry})

  def make(employee,month,ids,draft_id=None,earning_keys=None):
   return payroll.create_draft(draft_id or f"D-{month}",employee,month,earning_keys or list(earnings[employee].values()),ids)
  draft=make("E101","2026-10",[allowance["E101"]["value"]["version_id"],loan["value"]["version_id"]])
  payroll.review_draft("D-2026-10","E101","REV-INITIAL",draft["content_hash"],1,"approved")
  payroll.set_draft_control("D-2026-10","E101",True,False,"manager hold",1)
  held=reject(lambda:payroll.commit("D-2026-10","E101","COMMIT-2026-10",2,approval_required=True))
  payroll.set_draft_control("D-2026-10","E101",False,False,"manager release",2)
  outcome=payroll.commit("D-2026-10","E101","COMMIT-2026-10",3,approval_required=True,fresh_review_required=False); after_commit("E101","2026-10",outcome)
  capture("oct-e101","October · retained exact review","E101 is held, excluded, released, then committed with its earlier exact-content approval retained.","E101","2026-10",draft,{**outcome,"held_attempt":held,"review_policy":"retained"})
  draft=make("E102","2026-10",[allowance["E102"]["value"]["version_id"]])
  payroll.review_draft("D-2026-10","E102","REV-INITIAL",draft["content_hash"],1,"approved")
  payroll.set_draft_control("D-2026-10","E102",True,False,"manager hold",1); payroll.set_draft_control("D-2026-10","E102",False,False,"manager release",2)
  stale=reject(lambda:payroll.commit("D-2026-10","E102","COMMIT-2026-10",3,approval_required=True,fresh_review_required=True))
  payroll.review_draft("D-2026-10","E102","REV-FRESH",draft["content_hash"],3,"approved")
  outcome=payroll.commit("D-2026-10","E102","COMMIT-2026-10",3,approval_required=True,fresh_review_required=True); after_commit("E102","2026-10",outcome)
  capture("oct-e102","October · fresh review after release","E102's stale review is rejected; a review at the release revision permits commit.","E102","2026-10",draft,{**outcome,"stale_review_attempt":stale,"review_policy":"fresh"})

  old_basic=earnings["E101"]["EARN-BASIC"]
  earnings["E101"]["EARN-BASIC"]=payroll.define_earning("EARN-BASIC",2,"E101",components["BASIC"],3_300_000,"2026-12")["key"]
  bonus1=payroll.add_instruction("I-BONUS","BONUS-E101-1",1,"E101",components["BONUS"],500_000,"one_time","2026-11","2026-11")
  nov_earnings=[old_basic,*list(earnings["E101"].values())[1:]]
  old_draft=make("E101","2026-11",[allowance["E101"]["value"]["version_id"],loan["value"]["version_id"],bonus1["value"]["version_id"]],earning_keys=nov_earnings)
  deduction=payroll.add_instruction("I-RECOVERY","RECOVERY-E101-NOV",1,"E101",components["RECOVERY"],50_000,"one_time","2026-11","2026-11")
  bonus2=payroll.add_instruction_version("I-BONUS","BONUS-E101-2",2,"E101",components["BONUS"],600_000)
  freshness=reject(lambda:payroll.commit("D-2026-11","E101","COMMIT-OLD-2026-11",1,reconcile_sources=True))
  payroll.set_draft_control("D-2026-11","E101",False,True,"source basis changed; rebuild",1)
  capture("nov-e101-rejected","November · reconciliation rejects stale basis","An added deduction and revised bonus invalidate the protected draft. Cancellation is terminal.","E101","2026-11",old_draft,{"status":"cancelled","freshness_attempt":freshness})
  draft=make("E101","2026-11",[allowance["E101"]["value"]["version_id"],loan["value"]["version_id"],bonus2["value"]["version_id"],deduction["value"]["version_id"]],"D-2026-11-R1",nov_earnings)
  payroll.review_draft("D-2026-11-R1","E101","REV-FINAL",draft["content_hash"],1,"approved")
  outcome=payroll.commit("D-2026-11-R1","E101","COMMIT-2026-11",1,approval_required=True,reconcile_sources=True); after_commit("E101","2026-11",outcome)
  capture("nov-e101","November · cancelled and rebuilt","The replacement uses final one-time facts; the December salary version does not replace November authority.","E101","2026-11",draft,outcome)
  draft=make("E102","2026-11",[allowance["E102"]["value"]["version_id"]])
  allowance["E102"]=payroll.add_instruction_version("I-ALLOWANCE","ALLOW-E102-2",2,"E102",components["ALLOWANCE"],120_000,effective_from="2026-11")
  outcome=payroll.commit("D-2026-11","E102","COMMIT-2026-11",1,reconcile_sources=False); after_commit("E102","2026-11",outcome)
  capture("nov-e102","November · fixed snapshot policy","E102 commits fixed INR 1,000 allowance after its source changes; the difference is corrected next month.","E102","2026-11",draft,{**outcome,"source_policy":"fixed_snapshot"})

  bonus_posted=posted_sources[("E101","2026-11",bonus2["key"])]
  allowance_posted=posted_sources[("E102","2026-11","payroll.instruction:E102:I-ALLOWANCE:1")]
  correction1=payroll.add_instruction("I-CORRECTION","CORRECT-E101-DEC",1,"E101",components["RECOVERY"],50_000,"one_time","2026-12","2026-12",adjustment_of=bonus_posted)
  correction2=payroll.add_instruction("I-CORRECTION","CORRECT-E102-DEC",1,"E102",components["ALLOWANCE"],20_000,"one_time","2026-12","2026-12",adjustment_of=allowance_posted)
  def run_month(employee,month,ids):
   draft=make(employee,month,ids); outcome=payroll.commit(f"D-{month}",employee,f"COMMIT-{month}",1); after_commit(employee,month,outcome)
   capture(f"{month}-{employee.lower()}",f"{month} · {employee}","A separate employee operation commits the exact draft and records one obligation per liability entry.",employee,month,draft,outcome)
  run_month("E101","2026-12",[allowance["E101"]["value"]["version_id"],loan["value"]["version_id"],correction1["value"]["version_id"]])
  run_month("E102","2026-12",[allowance["E102"]["value"]["version_id"],correction2["value"]["version_id"]])
  for month in MONTHS[3:]:
   run_month("E101",month,[future_allowance["value"]["version_id"],loan["value"]["version_id"]])
   run_month("E102",month,[allowance["E102"]["value"]["version_id"]])

  payroll.record_remittance("REM-A-1",1_000_000,"challan:A-1",employer_id="EMPLOYER1",authority_id="AUTHORITY-A",currency="INR")
  first=(("E101","2026-10",300_000),("E102","2026-10",150_000),("E101","2026-11",300_000),("E102","2026-11",150_000),("E101","2026-12",100_000))
  for i,(employee,month,amount) in enumerate(first,1): payroll.allocate_remittance(f"ALLOC-A1-{i}",obligations[("A",employee,month)],"REM-A-1",amount)
  capture("partial-settlement","Shared remittance · partial settlement","One authority-A remittance spans selected obligations; INR 26,000 remains outstanding.",outcome={"status":"partially_allocated","allocation_count":5})
  payroll.record_remittance("REM-A-2",1_700_000,"challan:A-2",employer_id="EMPLOYER1",authority_id="AUTHORITY-A",currency="INR")
  payroll.record_remittance("REM-B-1",900_000,"challan:B-1",employer_id="EMPLOYER1",authority_id="AUTHORITY-B",currency="INR")
  allocated={k:a for k,a in ((('E101','2026-10'),300_000),(('E102','2026-10'),150_000),(('E101','2026-11'),300_000),(('E102','2026-11'),150_000),(('E101','2026-12'),100_000))}
  i=0
  for (family,employee,month),oid in obligations.items():
   if family=="A":
    amount=(300_000 if employee=="E101" else 150_000)-allocated.get((employee,month),0)
    if amount: i+=1; payroll.allocate_remittance(f"ALLOC-A2-{i}",oid,"REM-A-2",amount)
  for i,((family,employee,month),oid) in enumerate(((k,v) for k,v in obligations.items() if k[0]=="B"),1):
   payroll.allocate_remittance(f"ALLOC-B1-{i}",oid,"REM-B-1",100_000 if employee=="E101" else 50_000)
  capture("full-settlement","Authority remittances · fully allocated","Explicit A and B allocations close all INR 36,000; no allocation order is inferred.",outcome={"status":"settled","outstanding_minor":0})
  capture("accounting-handoff","After-exit correction handoff","A correction discovered after payroll eligibility is handed to external accounting; no payroll state is invented.",outcome={"status":"external_accounting_handoff"})
  db.close()
 return {"source":{"revision":"canonical-three-ledger-v2","sha256":{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ("demo.py","schema.sql","records.py","payroll.py")}},
  "fixture":{"tenant":"T1","employees":["E101","E102"],"months":list(MONTHS),"currency":"INR","unit":"minor"},"tables":list(TABLES),
  "catalogue":{"record_types":[*L1_TYPES,"payroll.employee.settings"],"ledger_kinds":["draft","posted","obligation","remittance","allocation"]},"stages":stages}

def main():
 parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
 args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(build_demo(),indent=2)+"\n")

if __name__=="__main__": main()

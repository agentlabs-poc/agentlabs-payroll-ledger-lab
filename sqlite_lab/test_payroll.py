import copy, json, sqlite3, tempfile, threading, unittest
from pathlib import Path
from sqlite_lab.payroll import Conflict, Payroll, PayrollError
from sqlite_lab.prove import _catalogue, run_proof
from sqlite_lab.records import canonical_key, connect

class PayrollTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.path=Path(self.temp.name)/"payroll.sqlite3"
        self.connection=connect(self.path); self.payroll=Payroll(self.connection,"T1","U7")
        self.salary=self.payroll.define_component("SALARY",1,"salary","Salary","earning","IN")["key"]
        self.loan=self.payroll.define_component("LOAN",1,"loan","Loan","deduction","IN")["key"]
        self.employer=self.payroll.define_component("EMPLOYER",1,"employer","Employer","employer_contribution","IN")["key"]
        self.salary_earning=self.payroll.define_earning("EARN-SALARY",1,"E101",self.salary,5_000_000,"2026-01")["key"]
        self.employer_earning=self.payroll.define_earning("EARN-EMPLOYER",1,"E101",self.employer,300_000,"2026-01")["key"]
        self.loan_version_id="IV-LOAN-1"
        self.loan_instruction=self.payroll.add_instruction("I-LOAN",self.loan_version_id,1,"E101",self.loan,200_000,"monthly","2026-10","2027-02")["key"]
    def tearDown(self): self.connection.close(); self.temp.cleanup()
    def make_draft(self,month="2026-11",draft_id="D1",with_employer=False,instructions=None):
        earnings=[self.salary_earning]+([self.employer_earning] if with_employer else [])
        return self.payroll.create_draft(draft_id,"E101",month,earnings,[self.loan_version_id] if instructions is None else list(instructions))

    def test_explicit_sources_and_fixed_draft_metadata(self):
        draft=self.make_draft()
        self.assertEqual(draft["key"],"payroll.draft:E101:D1:1")
        self.assertEqual(draft["value"]["earning_keys"],[self.salary_earning])
        self.assertEqual(draft["value"]["instruction_keys"],[self.loan_instruction])
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM payroll_draft_ledger WHERE tenant='T1' AND draft_key=?",(draft["key"],)).fetchone()[0],2)
        with self.assertRaises(sqlite3.IntegrityError): self.make_draft()
        with self.assertRaises(sqlite3.IntegrityError):
            self.payroll.add_instruction("I-DUP","IV-LOAN-1",1,"E101",self.loan,1,"monthly","2026-11")

    def test_connected_e101_totals_include_contribution_and_loan(self):
        draft=self.make_draft(with_employer=True)
        self.assertEqual((draft["gross_minor"],draft["deductions_minor"],draft["net_minor"]),(5_300_000,500_000,4_800_000))
        self.assertEqual([x["direction"] for x in draft["entries"]],["earning","employer_expense","employer_liability","deduction"])

    def test_two_employees_can_reuse_local_source_and_draft_ids(self):
        other_earning=self.payroll.define_earning("EARN-SALARY",1,"E102",self.salary,700_000,"2026-01")["key"]
        other_instruction=self.payroll.add_instruction("I-LOAN","IV-E102-LOAN-1",1,"E102",self.loan,10_000,"monthly","2026-01")["key"]
        first=self.payroll.create_draft("D1","E101","2026-11",[self.salary_earning],[self.loan_version_id])
        second=self.payroll.create_draft("D1","E102","2026-11",[other_earning],["IV-E102-LOAN-1"])
        self.assertEqual(first["key"],"payroll.draft:E101:D1:1")
        self.assertEqual(second["key"],"payroll.draft:E102:D1:1")
        self.assertNotEqual(first["entries"][0]["entry_id"],second["entries"][0]["entry_id"])
        self.assertEqual(self.payroll.commit("D1","E101","commit",1)["status"],"committed")
        self.assertEqual(self.payroll.commit("D1","E102","commit",1)["status"],"committed")
        self.assertIn(":E102:I-LOAN:1",other_instruction)

    def test_cross_owner_sources_and_draft_operations_are_rejected(self):
        other=self.payroll.define_earning("EARN-SALARY",1,"E102",self.salary,700_000,"2026-01")["key"]
        with self.assertRaises(PayrollError):
            self.payroll.create_draft("D-X","E101","2026-11",[other],[])
        self.make_draft(instructions=[])
        for operation in (
            lambda: self.payroll.set_draft_control("D1","E102",True,False,"wrong owner",1),
            lambda: self.payroll.review_draft("D1","E102","R-X","missing",1,"approved"),
            lambda: self.payroll.commit("D1","E102","wrong-owner",1),
        ):
            with self.assertRaises(PayrollError):
                operation()

    def test_future_source_revision_applies_only_from_its_month_without_disabled_fallback(self):
        first=self.payroll.define_earning("PERIOD",1,"E101",self.salary,100_000,"2026-01")
        future=self.payroll.define_earning("PERIOD",2,"E101",self.salary,200_000,"2026-12")
        november=self.payroll.create_draft("D-NOV","E101","2026-11",[first["key"]],[])
        self.assertEqual(november["gross_minor"],100_000)
        with self.assertRaises(PayrollError):
            self.payroll.create_draft("D-WRONG","E101","2026-11",[future["key"]],[])
        december=self.payroll.create_draft("D-DEC","E101","2026-12",[future["key"]],[])
        self.assertEqual(december["gross_minor"],200_000)
        disabled={**future["value"],"revision":3,"effective_from":"2027-01"}
        self.payroll.records._put_l1("T1",canonical_key("payroll.earning","E101","PERIOD",3),disabled,"disabled")
        with self.assertRaises(PayrollError):
            self.payroll.create_draft("D-JAN","E101","2027-01",[future["key"]],[])

    def test_monthly_instruction_endpoints_and_expiry(self):
        self.assertEqual(self.make_draft("2026-10","D-OCT")["net_minor"],4_800_000)
        self.assertEqual(self.make_draft("2027-02","D-FEB")["net_minor"],4_800_000)
        self.assertEqual(self.make_draft("2027-03","D-MAR")["net_minor"],5_000_000)

    def test_one_time_earning_instruction_adds_gross_and_cannot_reconsume_new_version(self):
        bonus=self.payroll.define_component("BONUS",1,"bonus","Bonus","earning","IN")["key"]
        first=self.payroll.add_instruction("I-BONUS","IV-BONUS-1",1,"E101",bonus,50_000,"one_time","2026-11","2026-11")
        draft=self.make_draft(draft_id="D-B1",instructions=[first["value"]["version_id"]])
        self.assertEqual((draft["gross_minor"],draft["deductions_minor"],draft["net_minor"]),(5_050_000,0,5_050_000))
        self.payroll.commit("D-B1","E101","bonus-first",1)
        second=self.payroll.add_instruction_version("I-BONUS","IV-BONUS-2",2,"E101",bonus,50_000)
        self.make_draft(draft_id="D-B2",instructions=[second["value"]["version_id"]])
        with self.assertRaises(Conflict): self.payroll.commit("D-B2","E101","bonus-second",1)

    def test_hold_release_optional_exact_review_and_immutable_draft(self):
        draft=self.make_draft()
        with self.assertRaises(sqlite3.IntegrityError): self.connection.execute("UPDATE payroll_draft_ledger SET amount_minor=1")
        self.payroll.set_draft_control("D1","E101",True,False,"check",1)
        with self.assertRaises(PayrollError): self.payroll.commit("D1","E101","held",2)
        self.payroll.set_draft_control("D1","E101",False,False,"release",2)
        with self.assertRaises(PayrollError): self.payroll.commit("D1","E101","review",3,True)
        self.payroll.review_draft("D1","E101","R1",draft["content_hash"],3,"approved")
        self.assertEqual(self.payroll.commit("D1","E101","review",3,True)["status"],"committed")

    def test_commit_is_atomic_on_injected_receipt_failure(self):
        self.make_draft(); self.connection.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON payroll_l1_records WHEN NEW.key LIKE 'payroll.operation.receipt:%' BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.payroll.commit("D1","E101","fail",1)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM payroll_ledger").fetchone()[0],0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM payroll_l1_records WHERE key LIKE 'payroll.instruction.application:%'").fetchone()[0],0)

    def test_commit_reopen_replay_and_changed_retry(self):
        self.make_draft(); first=self.payroll.commit("D1","E101","durable",1); self.connection.close(); self.connection=connect(self.path)
        reopened=Payroll(self.connection,"T1","U7"); self.assertEqual(reopened.commit("D1","E101","durable",1),first)
        with self.assertRaises(Conflict): reopened.commit("D1","E101","durable",1,True)

    def test_two_connections_commit_one_posted_set(self):
        self.make_draft(); barrier=threading.Barrier(2); results=[]
        def attempt(actor):
            c=connect(self.path); p=Payroll(c,"T1",actor); barrier.wait()
            try: results.append(("ok",p.commit("D1","E101","race-"+actor,1)))
            except Exception as exc: results.append(("error",type(exc).__name__))
            finally: c.close()
        threads=[threading.Thread(target=attempt,args=(x,)) for x in ("U8","U9")]
        [x.start() for x in threads]; [x.join() for x in threads]
        self.assertEqual(sorted(x[0] for x in results),["error","ok"])
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM payroll_ledger WHERE draft_key='payroll.draft:E101:D1:1'").fetchone()[0],2)

    def test_stale_control_disabled_component_and_reference_guards(self):
        self.make_draft(); self.payroll.set_draft_control("D1","E101",True,False,"held",1)
        with self.assertRaises(Conflict): self.payroll.set_draft_control("D1","E101",False,False,"stale",1)
        self.payroll.disable_component("LOAN",1)
        with self.assertRaises(PayrollError): self.make_draft(draft_id="D2")
        with self.assertRaises(PayrollError): self.payroll.define_earning("BAD",1,"E101",self.loan_instruction,1,"2026-01")
        with self.assertRaises(sqlite3.IntegrityError): self.connection.execute("INSERT INTO payroll_draft_ledger(tenant,draft_key,entry_id,employee_id,payroll_month,source_key,component_key,direction,amount_minor,currency) VALUES('T2','payroll.draft:E101:D1:1','X','E101','2026-11',?,?,'earning',1,'INR')",(self.salary_earning,self.salary))

    def test_disabled_current_earning_and_instruction_cannot_resurrect_history(self):
        earning_v1=self.payroll.define_earning("OLD-EARNING",1,"E101",self.salary,10_000,"2026-01")
        earning_v2={**earning_v1["value"],"revision":2}
        self.payroll.records._put_l1("T1",canonical_key("payroll.earning","E101","OLD-EARNING",2),earning_v2,"disabled")
        instruction_v2={**self.payroll.records.get_l1("T1",self.loan_instruction)["value"],"revision":2,"version_id":"IV-LOAN-2"}
        self.payroll.records._put_l1("T1",canonical_key("payroll.instruction","E101","I-LOAN",2),instruction_v2,"disabled")
        with self.assertRaises(PayrollError):
            self.payroll.create_draft("D-OLD-E","E101","2026-11",[earning_v1["key"]],[])
        with self.assertRaises(PayrollError):
            self.payroll.create_draft("D-OLD-I","E101","2026-11",[self.salary_earning],[self.loan_version_id])

    def test_existing_draft_snapshot_commits_after_source_is_superseded(self):
        self.make_draft(instructions=[])
        old=self.payroll.records.get_l1("T1",self.salary_earning)["value"]
        self.payroll.records._put_l1(
            "T1",canonical_key("payroll.earning","E101",old["earning_id"],2),
            {**old,"revision":2},"disabled",
        )
        self.assertEqual(self.payroll.commit("D1","E101","snapshot",1)["status"],"committed")

    def test_instruction_selection_is_strictly_by_opaque_version_id(self):
        prefix_id="payroll.instruction:opaque\\:version"
        instruction=self.payroll.add_instruction("PREFIX",prefix_id,1,"E101",self.loan,1_000,"monthly","2026-01")
        draft=self.payroll.create_draft("D-PREFIX","E101","2026-11",[self.salary_earning],[prefix_id])
        self.assertEqual(draft["value"]["instruction_keys"],[instruction["key"]])
        with self.assertRaises(PayrollError):
            self.payroll.create_draft("D-KEY","E101","2026-11",[self.salary_earning],[instruction["key"]])

    def test_schema_binds_draft_and_posted_rows_to_exact_references(self):
        draft=self.make_draft()
        unselected=self.payroll.define_earning("UNSELECTED",1,"E101",self.salary,5_000_000,"2026-01")["key"]
        base=("T1",draft["key"],"MISMATCH","E101","2026-11",self.salary_earning,self.salary,"earning",5_000_000)
        mismatches=[
            base[:3]+("E102",)+base[4:],
            base[:4]+("2026-12",)+base[5:],
            base[:5]+(unselected,)+base[6:],
            base[:6]+(self.loan,)+base[7:],
            base[:7]+("deduction",)+base[8:],
            base[:8]+(4_999_999,),
        ]
        sql="INSERT INTO payroll_draft_ledger(tenant,draft_key,entry_id,employee_id,payroll_month,source_key,component_key,direction,amount_minor,currency) VALUES(?,?,?,?,?,?,?,?,?,'INR')"
        for values in mismatches:
            with self.assertRaises(sqlite3.IntegrityError):
                self.connection.execute(sql,values)
        draft_row=self.connection.execute("SELECT * FROM payroll_draft_ledger WHERE draft_key=? LIMIT 1",(draft["key"],)).fetchone()
        posted=("T1","BAD-POSTED",draft["key"],draft_row["entry_id"],draft_row["employee_id"],draft_row["payroll_month"],draft_row["source_key"],draft_row["component_key"],draft_row["direction"],draft_row["amount_minor"])
        for index in range(4,10):
            values=list(posted); values[1]+=str(index)
            values[index] = ({4:"E102",5:"2026-12",6:unselected,7:self.loan,8:"deduction",9:draft_row["amount_minor"]+1})[index]
            with self.assertRaises(sqlite3.IntegrityError):
                self.connection.execute("INSERT INTO payroll_ledger(tenant,ledger_entry_id,draft_key,draft_entry_id,employee_id,payroll_month,source_key,component_key,direction,amount_minor,currency) VALUES(?,?,?,?,?,?,?,?,?,?,'INR')",values)

    def test_component_scope_and_stable_identity(self):
        self.payroll.define_component("A",1,"stable","A","earning","IN")
        with self.assertRaises(Conflict): self.payroll.define_component("B",1,"stable","B","earning","IN")
        self.payroll.define_component("A",2,"stable","new label","earning","IN")
        with self.assertRaises(Conflict): self.payroll.define_component("A",3,"changed","A","earning","IN")

    def test_escaped_source_and_draft_keys_work_end_to_end(self):
        component=self.payroll.define_component("SIDE:ID\\1",1,"side","Side","earning","IN")
        earning=self.payroll.define_earning("EARN:ID\\1",1,"EMP:1\\A",component["key"],123_456,"2026-01")
        draft=self.payroll.create_draft("D:1\\A","EMP:1\\A","2026-11",[earning["key"]],[])
        self.assertEqual(draft["net_minor"],123_456)
        self.assertEqual(self.payroll.commit("D:1\\A","EMP:1\\A","escaped",1)["status"],"committed")

    def test_elr_one_remittance_spans_obligations_and_caps(self):
        one=self.make_draft("2026-11","D1",True,[]); c1=self.payroll.commit("D1","E101","c1",1)
        two=self.make_draft("2026-12","D2",True,[]); c2=self.payroll.commit("D2","E101","c2",1)
        self.payroll.record_obligation("OB1",c1["employer_liability_entry_ids"][0],300_000,employer_id="ORG1",authority_id="EPFO"); self.payroll.record_obligation("OB2",c2["employer_liability_entry_ids"][0],300_000,employer_id="ORG1",authority_id="EPFO")
        self.payroll.record_remittance("REM1",400_000,"challan:REM1",employer_id="ORG1",authority_id="EPFO"); self.payroll.allocate_remittance("A1","OB1","REM1",200_000); self.payroll.allocate_remittance("A2","OB2","REM1",200_000)
        self.assertEqual((self.payroll.elr_outstanding("OB1"),self.payroll.elr_outstanding("OB2")),(100_000,100_000))
        with self.assertRaises(PayrollError): self.payroll.allocate_remittance("A3","OB1","REM1",1)

    def test_elr_rejects_noninteger_wrong_entry_and_missing_proof(self):
        self.make_draft(with_employer=True,instructions=[]); committed=self.payroll.commit("D1","E101","elr",1)
        salary=self.connection.execute("SELECT ledger_entry_id FROM payroll_ledger WHERE draft_key='payroll.draft:E101:D1:1' AND direction='earning'").fetchone()[0]
        for amount in (True,1.5):
            with self.assertRaises(PayrollError): self.payroll.record_remittance("BAD",amount,"proof",employer_id="ORG1",authority_id="EPFO")
        with self.assertRaises(PayrollError): self.payroll.record_remittance("BAD",1," ",employer_id="ORG1",authority_id="EPFO")
        with self.assertRaises(PayrollError): self.payroll.record_obligation("BAD",salary,5_000_000,employer_id="ORG1",authority_id="EPFO")
        self.payroll.record_obligation("OB1",committed["employer_liability_entry_ids"][0],300_000,employer_id="ORG1",authority_id="EPFO")
        with self.assertRaises(Conflict): self.payroll.record_obligation("OB2",committed["employer_liability_entry_ids"][0],300_000,employer_id="ORG1",authority_id="EPFO")

    def test_elr_rejects_malformed_own_and_reference_identities(self):
        for call in (
            lambda: self.payroll.record_remittance("",1,"proof",employer_id="ORG1",authority_id="EPFO"),
            lambda: self.payroll.record_obligation("BAD/ID","POSTED",1,employer_id="ORG1",authority_id="EPFO"),
            lambda: self.payroll.allocate_remittance("A1","BAD/OB","REM1",1),
            lambda: self.payroll.allocate_remittance("A1","OB1","BAD/REM",1),
        ):
            with self.assertRaises(ValueError):
                call()

class ProofRunnerTest(unittest.TestCase):
    def test_proof_exports_all_rows_and_complete_typed_catalogue(self):
        with tempfile.TemporaryDirectory() as directory:
            result=run_proof(Path(directory)); root=Path(directory)
            self.assertEqual(result["catalogue_coverage"],{"covered":15,"required":15})
            rows=json.loads((root/"canonical-rows.json").read_text()); catalog=json.loads((root/"canonical-catalog.json").read_text())
            self.assertEqual(set(rows),{"payroll_draft_ledger","payroll_ledger","payroll_employer_liability_ledger","payroll_l1_records","payroll_l2_records"})
            self.assertEqual(len(catalog["entries"]),15)
            self.assertTrue(all(entry["example"] for entry in catalog["entries"]))
            self.assertEqual({entry["kind"] for entry in catalog["entries"]},{
                "payroll.component","payroll.earning","payroll.instruction","payroll.draft",
                "payroll.draft.control","payroll.draft.review","payroll.instruction.resolution",
                "payroll.instruction.application","payroll.operation.receipt",
                "payroll.employee.settings","draft","posted","obligation","remittance","allocation"})
            l1_keys={row["key"] for row in rows["payroll_l1_records"]}
            for row in rows["payroll_draft_ledger"]:
                self.assertTrue({row["draft_key"],row["source_key"],row["component_key"]} <= l1_keys)
            draft_ids={(row["tenant"],row["draft_key"],row["entry_id"]) for row in rows["payroll_draft_ledger"]}
            for row in rows["payroll_ledger"]:
                self.assertIn((row["tenant"],row["draft_key"],row["draft_entry_id"]),draft_ids)
            posted_ids={(row["tenant"],row["ledger_entry_id"]) for row in rows["payroll_ledger"]}
            liability_ids={(row["tenant"],row["entry_id"],row["row_kind"]) for row in rows["payroll_employer_liability_ledger"]}
            for row in rows["payroll_employer_liability_ledger"]:
                if row["row_kind"]=="obligation": self.assertIn((row["tenant"],row["posted_liability_entry_id"]),posted_ids)
                if row["row_kind"]=="allocation":
                    self.assertIn((row["tenant"],row["obligation_entry_id"],"obligation"),liability_ids)
                    self.assertIn((row["tenant"],row["remittance_entry_id"],"remittance"),liability_ids)
            self.assertEqual(result["outcomes"]["E101_november"]["totals"],{"gross_minor":5_300_000,"deductions_minor":500_000,"net_minor":4_800_000})
            self.assertEqual(result["outcomes"]["employer_liability"]["outstanding_minor"],100_000)
            self.assertNotIn("payroll_l3_records",result["row_counts"])
            self.assertEqual(len(result["former_nine_table_replacement"]),9)
            self.assertTrue(result["source_revision"])
            self.assertEqual(len(result["role_mapping"]),16)
            self.assertTrue(all(item["evidence"] for item in result["role_mapping"] if item["status"]!="explicit_gap"))
            self.assertTrue(all(any("INDEX" in detail for detail in plan) for plan in result["query_plans"].values()))
            by_kind={entry["kind"]:entry for entry in catalog["entries"]}
            self.assertIn("earning_keys and instruction_keys",by_kind["payroll.draft"]["references"])
            self.assertIn("stable instruction_id",by_kind["payroll.instruction.application"]["validation"])
            self.assertIn("liability_allocations",by_kind["allocation"]["indexed_queries"])

            missing_component=copy.deepcopy(rows)
            component=next(row for row in missing_component["payroll_l1_records"] if row["key"]==self._source_key(rows,"component_key"))
            missing_component["payroll_l1_records"].remove(component)
            with self.assertRaisesRegex(ValueError,"component_key"):
                _catalogue(missing_component)

            bad_effect=copy.deepcopy(rows)
            application=next(row for row in bad_effect["payroll_l1_records"] if row["key"].startswith("payroll.instruction.application:"))
            application["value"]["effects"][0]["ledger_entry_id"]="MISSING"
            with self.assertRaisesRegex(ValueError,"application effect"):
                _catalogue(bad_effect)

            bad_stable_link=copy.deepcopy(rows)
            application=next(row for row in bad_stable_link["payroll_l1_records"] if row["key"].startswith("payroll.instruction.application:"))
            application["value"]["instruction_id"]="OTHER"
            with self.assertRaisesRegex(ValueError,"stable instruction"):
                _catalogue(bad_stable_link)

    @staticmethod
    def _source_key(rows, field):
        return next(row[field] for row in rows["payroll_draft_ledger"])
    def test_proof_refuses_existing_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/"canonical-rows.json").write_text("user")
            with self.assertRaises(FileExistsError): run_proof(Path(directory))

    def test_catalogue_rejects_unresolved_review_and_receipt_references(self):
        with tempfile.TemporaryDirectory() as directory:
            run_proof(Path(directory))
            rows=json.loads((Path(directory)/"canonical-rows.json").read_text())

        for label,change in (
            ("review control",lambda rs: next(r for r in rs if r["key"].startswith("payroll.draft.review:"))["value"].__setitem__("control_revision",99)),
            ("receipt control",lambda rs: next(r for r in rs if r["value"].get("operation")=="payroll.commit")["value"]["before"].__setitem__("control_revision",99)),
            ("receipt liability",lambda rs: next(r for r in rs if r["value"].get("outcome",{}).get("employer_liability_entry_id"))["value"]["outcome"].__setitem__("employer_liability_entry_id","MISSING")),
            ("receipt after posted entry",lambda rs: next(r for r in rs if r["value"].get("operation")=="payroll.commit")["value"]["after"]["posted_entry_ids"].__setitem__(0,"MISSING")),
        ):
            broken=copy.deepcopy(rows); change(broken["payroll_l1_records"])
            with self.subTest(label=label), self.assertRaisesRegex(ValueError,label):
                _catalogue(broken)

if __name__=="__main__": unittest.main()

import tempfile
import unittest
from pathlib import Path

from sqlite_lab.payroll import Conflict, Payroll, PayrollError
from sqlite_lab.records import connect


class PayrollEdgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "payroll.sqlite")
        self.payroll = Payroll(self.connection, "T1", "tester")
        self.earning_component = self.payroll.define_component("SALARY", 1, "salary", "Salary", "earning", "IN")["key"]
        self.deduction_component = self.payroll.define_component("LOAN", 1, "loan", "Loan", "deduction", "IN")["key"]
        self.earning = self.payroll.define_earning("SALARY", 1, "E101", self.earning_component, 100_000, "2026-01")["key"]

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_addition_only_reconciliation_rejects_while_fixed_snapshot_commits(self):
        self.payroll.create_draft("D1", "E101", "2026-11", [self.earning], [])
        self.payroll.add_instruction("NEW", "NEW-V1", 1, "E101", self.deduction_component, 1_000, "monthly", "2026-11")
        with self.assertRaises(Conflict):
            self.payroll.commit("D1", "E101", "fresh", 1, reconcile_sources=True)
        self.assertEqual("committed", self.payroll.commit("D1", "E101", "fixed", 1)["status"])

    def test_hold_release_fresh_review_and_terminal_cancel(self):
        draft = self.payroll.create_draft("D1", "E101", "2026-11", [self.earning], [])
        self.payroll.review_draft("D1", "E101", "R1", draft["content_hash"], 1, "approved")
        self.payroll.set_draft_control("D1", "E101", True, False, "hold", 1)
        with self.assertRaises(PayrollError):
            self.payroll.commit("D1", "E101", "held", 2, approval_required=True)
        self.payroll.set_draft_control("D1", "E101", False, False, "release", 2)
        with self.assertRaises(PayrollError):
            self.payroll.commit("D1", "E101", "stale-review", 3, approval_required=True, fresh_review_required=True)
        self.payroll.review_draft("D1", "E101", "R2", draft["content_hash"], 3, "approved")
        self.payroll.commit("D1", "E101", "commit", 3, approval_required=True, fresh_review_required=True)
        cancelled = self.payroll.create_draft("D2", "E101", "2026-12", [self.earning], [])
        self.payroll.set_draft_control("D2", "E101", False, True, "cancel", 1)
        for operation in (
            lambda: self.payroll.set_draft_control("D2", "E101", False, False, "reopen", 2),
            lambda: self.payroll.review_draft("D2", "E101", "R3", cancelled["content_hash"], 2, "approved"),
            lambda: self.payroll.commit("D2", "E101", "cancelled", 2),
        ):
            with self.assertRaises(PayrollError):
                operation()

    def test_correction_requires_earlier_posted_entry_for_same_employee(self):
        self.payroll.create_draft("D1", "E101", "2026-11", [self.earning], [])
        posted = self.payroll.commit("D1", "E101", "commit", 1)["posted_entry_ids"][0]
        for name, employee, month, referent in (
            ("SAME", "E101", "2026-11", posted),
            ("OTHER", "E102", "2026-12", posted),
            ("MISSING", "E101", "2026-12", "payrollentry_missing"),
        ):
            with self.subTest(name=name), self.assertRaises(PayrollError):
                self.payroll.add_instruction(name, name + "-V1", 1, employee, self.deduction_component, 1_000, "one_time", month, month, adjustment_of=referent)
        valid = self.payroll.add_instruction("VALID", "VALID-V1", 1, "E101", self.deduction_component, 1_000, "one_time", "2026-12", "2026-12", adjustment_of=posted)
        self.assertEqual(posted, valid["value"]["adjustment_of"])

    def test_payable_deductions_exclude_loan_and_elr_enforces_scope_and_caps(self):
        statutory = self.payroll.define_component("TAX", 1, "tax", "Tax", "deduction", "IN", authority_payable=True)["key"]
        employer = self.payroll.define_component("EMPLOYER", 1, "employer", "Employer", "employer_contribution", "IN")["key"]
        employer_earning = self.payroll.define_earning("EMPLOYER", 1, "E101", employer, 3_000, "2026-01")["key"]
        tax = self.payroll.add_instruction("TAX", "TAX-V1", 1, "E101", statutory, 2_000, "monthly", "2026-11")
        loan = self.payroll.add_instruction("LOAN", "LOAN-V1", 1, "E101", self.deduction_component, 1_000, "monthly", "2026-11")
        self.payroll.create_draft("D1", "E101", "2026-11", [self.earning, employer_earning], [tax["value"]["version_id"], loan["value"]["version_id"]])
        outcome = self.payroll.commit("D1", "E101", "commit", 1)
        self.assertEqual(2, len(outcome["payable_entry_ids"]))
        posted = {row["ledger_entry_id"]: row for row in self.connection.execute("SELECT * FROM payroll_ledger")}
        self.assertNotIn(self.deduction_component, {posted[key]["component_key"] for key in outcome["payable_entry_ids"]})
        for index, posted_id in enumerate(outcome["payable_entry_ids"], 1):
            self.payroll.record_obligation(f"OB{index}", posted_id, posted[posted_id]["amount_minor"], employer_id="ORG", authority_id="AUTH")
        with self.assertRaises(Conflict):
            self.payroll.record_obligation("DUP", outcome["payable_entry_ids"][0], posted[outcome["payable_entry_ids"][0]]["amount_minor"], employer_id="ORG", authority_id="AUTH")
        self.payroll.record_remittance("WRONG", 10_000, "proof", employer_id="ORG", authority_id="OTHER")
        with self.assertRaises(PayrollError):
            self.payroll.allocate_remittance("A0", "OB1", "WRONG", 1)
        self.payroll.record_remittance("REM", 10_000, "proof", employer_id="ORG", authority_id="AUTH")
        self.payroll.allocate_remittance("A1", "OB1", "REM", 1_000)
        self.assertGreater(self.payroll.elr_outstanding("OB1"), 0)
        with self.assertRaises(PayrollError):
            self.payroll.allocate_remittance("A2", "OB1", "REM", posted[outcome["payable_entry_ids"][0]]["amount_minor"])
        self.assertGreater(self.payroll.elr_outstanding("OB2"), 0)

    def test_empty_committed_draft_is_terminal(self):
        for draft_id, operation in (
            ("EMPTY-REVIEW", lambda draft: self.payroll.review_draft(draft["draft_id"], "E101", "R1", draft["content_hash"], 1, "approved")),
            ("EMPTY-CONTROL", lambda draft: self.payroll.set_draft_control(draft["draft_id"], "E101", True, False, "late", 1)),
            ("EMPTY-RECOMMIT", lambda draft: self.payroll.commit(draft["draft_id"], "E101", "second", 1)),
        ):
            draft = self.payroll.create_draft(draft_id, "E101", "2026-11", [], [])
            committed = self.payroll.commit(draft_id, "E101", "first", 1)
            self.assertEqual(committed, self.payroll.commit(draft_id, "E101", "first", 1))
            with self.subTest(operation=draft_id), self.assertRaises(PayrollError):
                operation(draft)

    def test_consumed_instruction_cannot_change_cadence_to_bypass_uniqueness(self):
        first = self.payroll.add_instruction("BONUS", "BONUS-V1", 1, "E101", self.earning_component, 10_000, "one_time", "2026-11", "2026-11")
        self.payroll.create_draft("D1", "E101", "2026-11", [self.earning], [first["value"]["version_id"]])
        self.payroll.commit("D1", "E101", "first", 1)
        changed = self.payroll.add_instruction("BONUS", "BONUS-V2", 2, "E101", self.earning_component, 10_000, "monthly", "2026-12")
        self.payroll.create_draft("D2", "E101", "2026-12", [self.earning], [changed["value"]["version_id"]])
        with self.assertRaises(Conflict):
            self.payroll.commit("D2", "E101", "second", 1)

        monthly = self.payroll.add_instruction("MONTHLY", "MONTHLY-V1", 1, "E101", self.earning_component, 5_000, "monthly", "2027-01")
        self.payroll.create_draft("M1", "E101", "2027-01", [self.earning], [monthly["value"]["version_id"]])
        self.payroll.commit("M1", "E101", "monthly", 1)
        changed = self.payroll.add_instruction("MONTHLY", "MONTHLY-V2", 2, "E101", self.earning_component, 5_000, "one_time", "2027-01", "2027-01")
        self.payroll.create_draft("M2", "E101", "2027-01", [self.earning], [changed["value"]["version_id"]])
        with self.assertRaises(Conflict):
            self.payroll.commit("M2", "E101", "one-time", 1)

    def test_control_and_commit_scalars_are_strict(self):
        draft = self.payroll.create_draft("STRICT", "E101", "2026-11", [self.earning], [])
        for field in ("approval_required", "reconcile_sources", "fresh_review_required"):
            with self.subTest(field=field), self.assertRaises(PayrollError):
                self.payroll.commit("STRICT", "E101", field, 1, **{field: 1})
        with self.assertRaises(PayrollError):
            self.payroll.commit("STRICT", "E101", "revision", True)
        with self.assertRaises(PayrollError):
            self.payroll.set_draft_control("STRICT", "E101", 1, False, "invalid", 1)
        with self.assertRaises(PayrollError):
            self.payroll.set_draft_control("STRICT", "E101", False, False, "invalid", True)
        with self.assertRaises(PayrollError):
            self.payroll.review_draft("STRICT", "E101", "R1", draft["content_hash"], True, "approved")
        with self.assertRaises(PayrollError):
            self.payroll.disable_component("SALARY", True)
        self.assertEqual("committed", self.payroll.commit("STRICT", "E101", "approval_required", 1)["status"])


if __name__ == "__main__":
    unittest.main()

import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from sqlite_lab.payroll import Conflict, Payroll, PayrollError
from sqlite_lab.prove import run_proof
from sqlite_lab.records import connect


class PayrollTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "payroll.sqlite3"
        self.connection = connect(self.path)
        self.payroll = Payroll(self.connection, "T1", "U7")
        self.payroll.define_component("SALARY", 1, "salary", "Salary", "earning", "IN")
        self.payroll.define_component("LOAN", 1, "loan", "Loan deduction", "deduction", "IN")
        self.payroll.define_component("EMPLOYER", 1, "employer", "Employer contribution", "employer_contribution", "IN")
        self.payroll.add_instruction(
            "I-LOAN", "IV-LOAN-1", 1, "E101", "LOAN", 200_000,
            "monthly", "2026-10", "2027-02",
        )

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def make_draft(self, month="2026-11", draft_id="D1", calculation_id="CAL1",
                   instructions=("IV-LOAN-1",), employer_contribution_minor=0):
        return self.payroll.create_draft(
            calculation_id, draft_id, "E101", month, 5_000_000,
            list(instructions), employer_contribution_minor=employer_contribution_minor,
        )

    def test_november_salary_and_monthly_loan_are_literal_minor_unit_totals(self):
        draft = self.make_draft()
        self.assertEqual(draft["gross_minor"], 5_000_000)
        self.assertEqual(draft["deductions_minor"], 200_000)
        self.assertEqual(draft["net_minor"], 4_800_000)
        self.assertEqual(len(draft["entries"]), 2)

    def test_instruction_create_and_version_actions_have_durable_receipts(self):
        created = self.payroll.add_instruction(
            "I-NEW", "IV-NEW-1", 1, "E101", "LOAN", 25_000,
            "monthly", "2026-11", "2026-12",
        )
        self.assertEqual(created["status"], "created")
        retried = self.payroll.add_instruction(
            "I-NEW", "IV-NEW-1", 1, "E101", "LOAN", 25_000,
            "monthly", "2026-11", "2026-12",
        )
        self.assertEqual(retried, created)
        with self.assertRaises(Conflict):
            self.payroll.add_instruction(
                "I-NEW", "IV-NEW-1", 1, "E101", "LOAN", 25_001,
                "monthly", "2026-11", "2026-12",
            )
        versioned = self.payroll.add_instruction_version(
            "I-NEW", "IV-NEW-2", 2, "LOAN", 30_000
        )
        self.assertEqual(versioned["status"], "version_created")
        receipts = [json.loads(row[0]) for row in self.connection.execute(
            "SELECT value FROM payroll_l1_records "
            "WHERE tenant='T1' AND key LIKE 'payroll.operation.receipt:%' "
            "AND json_extract(value,'$.operation') LIKE 'payroll.instruction.%' "
            "ORDER BY json_extract(value,'$.operation')"
        )]
        self.assertEqual(len(receipts), 3)  # includes I-LOAN from setUp
        new_version = next(item for item in receipts if item["operation"] == "payroll.instruction.version")
        self.assertEqual(new_version["executor"], "U7")
        self.assertEqual(new_version["before"]["latest_revision"], 1)
        self.assertEqual(new_version["after"]["latest_revision"], 2)

    def test_escaped_identities_work_through_component_instruction_draft_and_commit(self):
        component_id = "LOAN:West\\Legacy.1"
        instruction_id = "I:ESC\\1"
        version_id = "IV:ESC\\1"
        draft_id = "D:ESC\\1"
        self.payroll.define_component(component_id, 1, "escaped.loan", "Escaped loan", "deduction", "IN")
        self.payroll.add_instruction(
            instruction_id, version_id, 1, "E:101\\A", component_id, 123_456,
            "monthly", "2026-11", "2026-11",
        )
        draft = self.payroll.create_draft(
            "CAL:ESC\\1", draft_id, "E:101\\A", "2026-11", 1_000_000, [version_id]
        )
        outcome = self.payroll.commit(draft_id, "commit:escaped\\1", 1)
        self.assertEqual(draft["net_minor"], 876_544)
        self.assertEqual(outcome["status"], "committed")
        application = self.payroll.instruction_application(
            instruction_id, "E:101\\A", "2026-11"
        )
        self.assertEqual(application["value"]["draft_id"], draft_id)
        self.assertIn("payroll.instruction.application:IV\\:ESC\\\\1:", application["key"])

    def test_loan_applies_at_both_endpoints_and_expires_after_february(self):
        october = self.make_draft("2026-10", "D-OCT", "CAL-OCT")
        february = self.make_draft("2027-02", "D-FEB", "CAL-FEB")
        march = self.make_draft("2027-03", "D-MAR", "CAL-MAR")
        self.assertEqual(october["net_minor"], 4_800_000)
        self.assertEqual(february["net_minor"], 4_800_000)
        self.assertEqual(march["net_minor"], 5_000_000)

    def test_fixed_draft_hold_release_optional_approval_and_exact_review_binding(self):
        draft = self.make_draft()
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "UPDATE payroll_draft_entries SET amount_minor=1 WHERE tenant='T1' AND draft_id='D1'"
            )
        held = self.payroll.set_draft_control("D1", True, False, "check", expected_revision=1)
        with self.assertRaises(PayrollError):
            self.payroll.commit("D1", "held", expected_control_revision=2)
        released = self.payroll.set_draft_control("D1", False, False, "released", expected_revision=2)
        self.assertEqual((held["revision"], released["revision"]), (2, 3))
        with self.assertRaises(PayrollError):
            self.payroll.commit("D1", "needs-review", 3, approval_required=True)
        self.payroll.review_draft("D1", "R1", draft["content_hash"], 3, "approved")
        outcome = self.payroll.commit("D1", "reviewed", 3, approval_required=True)
        self.assertEqual(outcome["status"], "committed")

    def test_commit_writes_money_applications_effects_and_receipt_atomically(self):
        self.make_draft()
        outcome = self.payroll.commit("D1", "commit-nov", 1)
        self.assertEqual(len(outcome["posted_entry_ids"]), 2)
        application = self.connection.execute(
            "SELECT value FROM payroll_l1_records WHERE tenant='T1' AND key LIKE 'payroll.instruction.application:%'"
        ).fetchone()
        receipt = self.connection.execute(
            "SELECT value FROM payroll_l1_records WHERE tenant='T1' AND key LIKE 'payroll.operation.receipt:%'"
        ).fetchone()
        self.assertIsNotNone(application)
        self.assertIsNotNone(receipt)
        self.assertEqual(self.connection.execute(
            "SELECT COUNT(*) FROM payroll_ledger_entries WHERE tenant='T1' AND draft_id='D1'"
        ).fetchone()[0], 2)

    def test_injected_receipt_failure_rolls_back_every_commit_effect(self):
        self.make_draft()
        self.connection.execute(
            "CREATE TRIGGER fail_receipt BEFORE INSERT ON payroll_l1_records "
            "WHEN NEW.key LIKE 'payroll.operation.receipt:%' "
            "BEGIN SELECT RAISE(ABORT, 'injected receipt failure'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.payroll.commit("D1", "commit-fails", 1)
        self.assertEqual(self.connection.execute(
            "SELECT COUNT(*) FROM payroll_ledger_entries WHERE tenant='T1'"
        ).fetchone()[0], 0)
        self.assertEqual(self.connection.execute(
            "SELECT COUNT(*) FROM payroll_l1_records WHERE key LIKE 'payroll.instruction.application:%'"
        ).fetchone()[0], 0)
        self.assertEqual(self.connection.execute(
            "SELECT status FROM payroll_calculations WHERE tenant='T1' AND calculation_id='CAL1'"
        ).fetchone()[0], "draft")

    def test_commit_reopens_durably_and_replays_only_identical_request(self):
        self.make_draft()
        first = self.payroll.commit("D1", "durable", 1)
        self.connection.close()
        self.connection = connect(self.path)
        reopened = Payroll(self.connection, "T1", "U7")
        self.assertEqual(reopened.commit("D1", "durable", 1), first)
        with self.assertRaises(Conflict):
            reopened.commit("D1", "durable", 1, approval_required=True)

    def test_one_time_consumption_uses_stable_instruction_identity_across_versions(self):
        self.payroll.add_instruction(
            "I-BONUS", "IV-BONUS-1", 1, "E101", "LOAN", 50_000,
            "one_time", "2026-11", "2026-11",
        )
        self.make_draft(instructions=("IV-BONUS-1",))
        self.payroll.commit("D1", "one-time-first", 1)
        self.payroll.add_instruction_version("I-BONUS", "IV-BONUS-2", 2, "LOAN", 50_000)
        self.make_draft("2026-11", "D2", "CAL2", instructions=("IV-BONUS-2",))
        with self.assertRaises(Conflict):
            self.payroll.commit("D2", "one-time-second", 1)

    def test_two_connections_race_to_commit_one_draft_without_duplicate_money(self):
        self.make_draft()
        barrier = threading.Barrier(2)
        results = []

        def attempt(actor):
            connection = connect(self.path)
            payroll = Payroll(connection, "T1", actor)
            barrier.wait()
            try:
                results.append(("ok", payroll.commit("D1", "race-" + actor, 1)))
            except Exception as exc:
                results.append(("error", type(exc).__name__))
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt, args=(actor,)) for actor in ("U8", "U9")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(kind for kind, _ in results), ["error", "ok"])
        self.assertEqual(self.connection.execute(
            "SELECT COUNT(*) FROM payroll_ledger_entries WHERE tenant='T1' AND draft_id='D1'"
        ).fetchone()[0], 2)
        self.assertEqual(self.connection.execute(
            "SELECT COUNT(*) FROM payroll_l1_records WHERE tenant='T1' "
            "AND key LIKE 'payroll.operation.receipt:%' "
            "AND json_extract(value,'$.operation')='payroll.commit'"
        ).fetchone()[0], 1)

    def test_stale_control_and_cross_tenant_reference_are_rejected(self):
        self.make_draft()
        self.payroll.set_draft_control("D1", True, False, "held", 1)
        with self.assertRaises(Conflict):
            self.payroll.set_draft_control("D1", False, False, "stale", 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO payroll_draft_entries(tenant,draft_id,entry_id,component_id,direction,amount_minor) "
                "VALUES('T2','D1','X','SALARY','earning',1)"
            )

    def test_application_effect_arrays_are_checked_against_posted_entries(self):
        self.make_draft()
        outcome = self.payroll.commit("D1", "effects", 1)
        application = self.payroll.instruction_application("I-LOAN", "E101", "2026-11")
        self.assertEqual(application["value"]["effects"][0]["ledger_entry_id"], outcome["posted_entry_ids"][1])
        self.assertEqual(application["value"]["effects"][0]["amount_minor"], 200_000)

    def test_instruction_versions_and_committed_canonical_facts_are_immutable(self):
        self.make_draft(instructions=(), employer_contribution_minor=300_000)
        committed = self.payroll.commit("D1", "immutable", 1)
        self.payroll.record_obligation("OB1", committed["employer_liability_entry_id"], 300_000)
        self.payroll.record_remittance("REM1", 100_000)
        self.payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 100_000)
        updates = [
            "UPDATE payroll_instruction_versions SET amount_minor=1 WHERE tenant='T1'",
            "UPDATE payroll_ledger_entries SET amount_minor=1 WHERE tenant='T1'",
            "UPDATE payroll_statutory_obligations SET amount_minor=1 WHERE tenant='T1'",
            "UPDATE payroll_statutory_remittances SET amount_minor=1 WHERE tenant='T1'",
            "UPDATE payroll_statutory_allocations SET amount_minor=1 WHERE tenant='T1'",
        ]
        for statement in updates:
            with self.subTest(statement=statement), self.assertRaises(sqlite3.IntegrityError):
                self.connection.execute(statement)

    def test_elr_outstanding_reduces_only_after_allocation_and_rejects_overallocation(self):
        self.make_draft(instructions=(), employer_contribution_minor=300_000)
        committed = self.payroll.commit("D1", "contribution", 1)
        liability_entry = committed["employer_liability_entry_id"]
        self.assertIsNotNone(liability_entry)
        self.payroll.record_obligation("OB1", liability_entry, 300_000)
        self.assertEqual(self.payroll.elr_outstanding("OB1"), 300_000)
        self.payroll.record_remittance("REM1", 200_000)
        self.payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 200_000)
        self.assertEqual(self.payroll.elr_outstanding("OB1"), 100_000)
        self.payroll.record_remittance("REM2", 200_000)
        with self.assertRaises(PayrollError):
            self.payroll.allocate_remittance("ALLOC2", "OB1", "REM2", 200_000)

    def test_disabling_component_creates_new_current_revision_without_revival(self):
        disabled = self.payroll.disable_component("LOAN", 1)
        self.assertEqual(disabled["value"]["revision"], 2)
        self.assertEqual(disabled["state"], "disabled")
        self.assertIsNone(self.payroll.records.current_l1("T1", "payroll.component", "LOAN"))
        with self.assertRaises(Conflict):
            self.payroll.disable_component("LOAN", 1)
        with self.assertRaises(PayrollError):
            self.make_draft()


class ProofRunnerTest(unittest.TestCase):
    def test_proof_retains_evidence_and_maps_all_sixteen_roles_without_l3(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_proof(Path(directory))
            self.assertEqual(len(result["role_mapping"]), 16)
            self.assertEqual(result["outcomes"]["E101_november"]["net_minor"], 4_800_000)
            self.assertNotIn("payroll_l3_records", result["row_counts"])
            self.assertTrue(any(
                "l1_application_reverse" in detail
                for detail in result["query_plans"]["instruction_application_reverse_lookup"]
            ))
            source_role = next(item for item in result["role_mapping"]
                               if item["role"] == "payroll_source_authority_actions")
            self.assertEqual(source_role["status"], "witnessed")
            self.assertGreaterEqual(len(source_role["evidence"]), 2)
            self.assertTrue((Path(directory) / "evidence.json").is_file())
            self.assertTrue((Path(directory) / "proof.sqlite3").is_file())

    def test_proof_refuses_to_reuse_an_existing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "proof.sqlite3"
            database.write_bytes(b"user data")
            with self.assertRaises(FileExistsError):
                run_proof(Path(directory))


if __name__ == "__main__":
    unittest.main()

import hashlib
import importlib
import unittest
from pathlib import Path


TABLES = {
    "payroll_l1_records",
    "payroll_l2_records",
    "payroll_draft_ledger",
    "payroll_ledger",
    "payroll_employer_liability_ledger",
}


def load_demo_module():
    try:
        return importlib.import_module("sqlite_lab.demo")
    except ModuleNotFoundError as error:
        raise AssertionError("the canonical demo exporter module is missing") from error


class CanonicalDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo_module = load_demo_module()
        cls.demo = cls.demo_module.build_demo()
        cls.by_id = {stage["id"]: stage for stage in cls.demo["stages"]}

    def test_every_stage_contains_actual_rows_from_exactly_five_tables(self):
        self.assertEqual(TABLES, set(self.demo["tables"]))
        self.assertGreaterEqual(len(self.demo["stages"]), 10)
        for stage in self.demo["stages"]:
            self.assertEqual(TABLES, set(stage["tables"]), stage["id"])
            for rows in stage["tables"].values():
                self.assertIsInstance(rows, list)

    def test_connected_journey_preserves_draft_and_commit_boundaries(self):
        draft = self.by_id["draft"]
        held = self.by_id["held"]
        released = self.by_id["released"]
        committed = self.by_id["committed"]

        self.assertEqual(
            {"gross_minor": 5_300_000, "deductions_minor": 500_000, "net_minor": 4_800_000},
            draft["summary"]["payroll"],
        )
        self.assertEqual("rejected", held["outcome"]["status"])
        for table in ("payroll_draft_ledger", "payroll_ledger", "payroll_employer_liability_ledger"):
            self.assertEqual(draft["tables"][table], held["tables"][table])
        self.assertFalse(any(row["key"].startswith("payroll.instruction.application:") for row in held["tables"]["payroll_l1_records"]))
        self.assertEqual(draft["tables"]["payroll_draft_ledger"], released["tables"]["payroll_draft_ledger"])
        self.assertEqual(5, len(committed["tables"]["payroll_ledger"]))
        self.assertEqual(
            {
                ("payroll.component:BASIC:1", "earning", 3_000_000),
                ("payroll.component:HRA:1", "earning", 2_000_000),
                ("payroll.component:EMPLOYER:1", "employer_expense", 300_000),
                ("payroll.component:EMPLOYER:1", "employer_liability", 300_000),
                ("payroll.component:LOAN:1", "deduction", 200_000),
            },
            {(row["component_key"], row["direction"], row["amount_minor"]) for row in committed["tables"]["payroll_ledger"] if row["employee_id"] == "E101"},
        )
        self.assertTrue(any(row["key"].startswith("payroll.instruction.application:") for row in committed["tables"]["payroll_l1_records"]))
        self.assertTrue(any(row["value"].get("operation") == "payroll.commit" for row in committed["tables"]["payroll_l1_records"]))

    def test_review_is_explicitly_optional_and_history_never_changes(self):
        reviewed = self.by_id["reviewed"]
        committed = self.by_id["committed"]
        self.assertFalse(committed["outcome"]["approval_required"])
        self.assertTrue(reviewed["outcome"]["optional"])

        draft_row = next(row for row in self.by_id["draft"]["tables"]["payroll_l1_records"] if row["key"] == "payroll.draft:D1:1")
        for stage in self.demo["stages"][3:]:
            current = next(row for row in stage["tables"]["payroll_l1_records"] if row["key"] == "payroll.draft:D1:1")
            self.assertEqual(draft_row, current)

    def test_remittance_and_allocation_are_distinct_liability_facts(self):
        obligation = self.by_id["obligation"]
        remittance = self.by_id["remittance"]
        allocation = self.by_id["allocation"]
        self.assertEqual(300_000, obligation["summary"]["liability"]["outstanding_minor"])
        self.assertEqual(300_000, remittance["summary"]["liability"]["outstanding_minor"])
        self.assertEqual(100_000, allocation["summary"]["liability"]["outstanding_minor"])
        self.assertEqual({"obligation", "remittance", "allocation"}, {row["row_kind"] for row in allocation["tables"]["payroll_employer_liability_ledger"]})

    def test_final_snapshot_witnesses_all_fifteen_canonical_kinds(self):
        final = self.demo["stages"][-1]["tables"]
        l1_types = {row["key"].rsplit(":", 2)[0] for row in final["payroll_l1_records"]}
        l2_types = {row["key"].rsplit(":", 2)[0] for row in final["payroll_l2_records"]}
        ledger_kinds = {
            *(row["row_kind"] for row in final["payroll_draft_ledger"]),
            *(row["row_kind"] for row in final["payroll_ledger"]),
            *(row["row_kind"] for row in final["payroll_employer_liability_ledger"]),
        }
        self.assertEqual(set(self.demo["catalogue"]["record_types"]), l1_types | l2_types)
        self.assertEqual(set(self.demo["catalogue"]["ledger_kinds"]), ledger_kinds)
        self.assertEqual(15, len(l1_types | l2_types) + len(ledger_kinds))

    def test_source_hashes_bind_the_export_to_executable_sources(self):
        root = Path(self.demo_module.__file__).parent
        self.assertEqual(
            {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ("demo.py", "schema.sql", "records.py", "payroll.py")},
            self.demo["source"]["sha256"],
        )


if __name__ == "__main__":
    unittest.main()

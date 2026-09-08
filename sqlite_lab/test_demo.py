import hashlib
import unittest
from pathlib import Path

from sqlite_lab import demo
from sqlite_lab.prove import _validate_reference_closure


class CanonicalDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flow = demo.build_demo()
        cls.final = cls.flow["stages"][-1]["tables"]

    def test_six_month_actual_journey(self):
        self.assertEqual({"E101", "E102"}, set(self.flow["fixture"]["employees"]))
        self.assertEqual(6, len(self.flow["fixture"]["months"]))
        self.assertTrue(all(set(stage["tables"]) == set(demo.TABLES) for stage in self.flow["stages"]))
        self.assertTrue(all(set(stage["context"]) >= {"employee_id", "payroll_month"} for stage in self.flow["stages"]))

        totals = {}
        for stage in self.flow["stages"]:
            context = stage["context"]
            if stage["summary"]["payroll"] and stage["outcome"].get("status") != "cancelled":
                totals[(context["employee_id"], context["payroll_month"])] = tuple(
                    stage["summary"]["payroll"][key]
                    for key in ("gross_minor", "deductions_minor", "net_minor")
                )
        self.assertEqual(demo.EXPECTED, totals)

    def test_consumption_corrections_and_liabilities(self):
        applications = [row["value"] for row in self.final["payroll_l1_records"] if row["key"].startswith("payroll.instruction.application:")]
        self.assertEqual(5, sum(row["instruction_id"] == "I-LOAN" for row in applications))
        self.assertFalse(any(row["instruction_id"] == "I-LOAN" and row["payroll_month"] == "2027-03" for row in applications))
        corrections = [row["value"] for row in self.final["payroll_l1_records"] if row["key"].startswith("payroll.instruction:") and row["value"].get("adjustment_of")]
        self.assertEqual({"E101", "E102"}, {row["employee_id"] for row in corrections})
        self.assertEqual(0, self.flow["stages"][-1]["summary"]["liability"]["outstanding_minor"])
        _validate_reference_closure(self.final)

    def test_source_hashes_bind_export(self):
        root = Path(demo.__file__).parent
        self.assertEqual(
            {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ("demo.py", "schema.sql", "records.py", "payroll.py")},
            self.flow["source"]["sha256"],
        )


if __name__ == "__main__":
    unittest.main()

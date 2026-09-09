import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from sqlite_lab.cli import main
from sqlite_lab.payroll import Payroll
from sqlite_lab.records import connect


class CliLedgerContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "payroll.sqlite"
        self.config = self.root / "cli.json"
        connection = connect(self.database)
        payroll = Payroll(connection, "T1", "U1")
        component = payroll.define_component(
            "PF", 1, "pf", "PF", "employer_contribution", "IN"
        )["key"]
        self.earning = payroll.define_earning(
            "PF", 1, "E1", component, 100_000, "2026-01"
        )["key"]
        connection.close()
        self.config.write_text(json.dumps({
            "database": str(self.database), "tenant": "T1",
            "actor": "U1", "format": "json",
        }))

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, argv, payload=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.dict(os.environ, {"PAYROLL_CLI_CONFIG": str(self.config)}),
            patch.object(os.sys, "stdin", io.StringIO("" if payload is None else json.dumps(payload))),
            redirect_stdout(stdout), redirect_stderr(stderr),
        ):
            status = main([*argv, *([] if payload is None else ["--input", "-"])])
        self.assertEqual((status, stderr.getvalue()), (0, ""))
        return json.loads(stdout.getvalue())

    def test_three_ledger_posts_and_reversal_aware_employee_view(self):
        draft = self.invoke(["ledger-post", "draft"], {
            "draft_id": "D1", "employee_id": "E1", "payroll_month": "2026-11",
            "earning_keys": [self.earning], "instruction_version_ids": [],
        })
        committed = self.invoke(["ledger-post", "payroll"], {
            "draft_id": "D1", "employee_id": "E1", "idempotency_key": "commit",
            "expected_control_revision": 1,
        })
        obligation = self.invoke(["ledger-post", "liability"], {
            "row_kind": "obligation", "entry_id": "OB1",
            "posted_liability_entry_id": committed["payable_entry_ids"][0],
            "amount_minor": 100_000, "employer_id": "ORG",
            "authority_id": "EPFO", "currency": "INR",
        })
        self.assertEqual(
            (draft["value"]["draft_id"], committed["status"], obligation["row_kind"]),
            ("D1", "committed", "obligation"),
        )

        self.invoke(["ledger-post", "liability"], {
            "row_kind": "remittance", "entry_id": "REM1", "amount_minor": 100_000,
            "proof_ref": "proof", "employer_id": "ORG",
            "authority_id": "EPFO", "currency": "INR",
        })
        self.invoke(["ledger-post", "liability"], {
            "row_kind": "allocation", "entry_id": "ALLOC1",
            "obligation_entry_id": "OB1", "remittance_entry_id": "REM1",
            "amount_minor": 60_000,
        })
        self.invoke(["ledger-post", "liability"], {
            "row_kind": "reversal", "entry_id": "REV1",
            "reversal_of_entry_id": "ALLOC1", "reason": "wrong allocation",
        })

        outstanding = self.invoke([
            "ledger", "liability", "--view", "outstanding", "--employee", "E1"
        ])
        self.assertEqual(
            [(row["entry_id"], row["outstanding_minor"]) for row in outstanding],
            [("OB1", 100_000)],
        )
        entries = self.invoke(["ledger", "liability", "--employee", "E1"])
        self.assertEqual(
            {row["row_kind"] for row in entries}, {"obligation", "allocation", "reversal"}
        )
        self.assertEqual(self.invoke(["ledger", "liability", "--employee", "E2"]), [])


if __name__ == "__main__":
    unittest.main()

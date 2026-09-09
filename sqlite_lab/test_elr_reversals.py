import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from sqlite_lab.cli import main
from sqlite_lab.payroll import Conflict, Payroll, PayrollError
from sqlite_lab.prove import _catalogue, run_proof
from sqlite_lab.records import connect


class ELRReversalTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "payroll.sqlite"
        self.connection = connect(self.path)
        self.payroll = Payroll(self.connection, "T1", "U1")
        component = self.payroll.define_component(
            "PF", 1, "pf", "PF", "employer_contribution", "IN"
        )["key"]
        earning = self.payroll.define_earning(
            "PF", 1, "E1", component, 100_000, "2026-01"
        )["key"]
        self.payroll.create_draft("D1", "E1", "2026-11", [earning], [])
        self.posted = self.payroll.commit("D1", "E1", "commit", 1)[
            "payable_entry_ids"
        ][0]
        self.payroll.record_obligation(
            "OB1", self.posted, 100_000, employer_id="ORG", authority_id="EPFO"
        )
        self.payroll.record_remittance(
            "REM1", 100_000, "proof", employer_id="ORG", authority_id="EPFO"
        )

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_reversing_allocation_restores_both_parent_balances(self):
        self.payroll.post_elr(
            "allocation",
            entry_id="ALLOC1",
            obligation_entry_id="OB1",
            remittance_entry_id="REM1",
            amount_minor=60_000,
        )
        self.assertEqual(self.payroll.elr_outstanding("OB1"), 40_000)

        reversal = self.payroll.post_elr(
            "reversal",
            entry_id="REV1",
            reversal_of_entry_id="ALLOC1",
            reason="wrong obligation",
        )

        self.assertEqual(reversal["row_kind"], "reversal")
        self.assertEqual(reversal["amount_minor"], 60_000)
        self.assertEqual(reversal["actor"], "U1")
        self.assertEqual(self.payroll.elr_outstanding("OB1"), 100_000)
        self.payroll.allocate_remittance("ALLOC2", "OB1", "REM1", 100_000)
        self.assertEqual(self.payroll.elr_outstanding("OB1"), 0)

    def test_parent_dependencies_and_reversal_retry_are_enforced(self):
        self.payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 10_000)
        for target in ("OB1", "REM1"):
            with self.subTest(target=target), self.assertRaises(PayrollError):
                self.payroll.post_elr(
                    "reversal",
                    entry_id="BLOCKED-" + target,
                    reversal_of_entry_id=target,
                    reason="blocked",
                )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM payroll_employer_liability_ledger "
                "WHERE row_kind='reversal'"
            ).fetchone()[0],
            0,
        )

        first = self.payroll.post_elr(
            "reversal",
            entry_id="REV1",
            reversal_of_entry_id="ALLOC1",
            reason="wrong allocation",
        )
        self.assertEqual(
            self.payroll.post_elr(
                "reversal",
                entry_id="REV1",
                reversal_of_entry_id="ALLOC1",
                reason="wrong allocation",
            ),
            first,
        )
        with self.assertRaises(Conflict):
            self.payroll.post_elr(
                "reversal",
                entry_id="REV1",
                reversal_of_entry_id="ALLOC1",
                reason="changed",
            )
        with self.assertRaises(Conflict):
            self.payroll.post_elr(
                "reversal",
                entry_id="REV2",
                reversal_of_entry_id="ALLOC1",
                reason="again",
            )
        with self.assertRaises(PayrollError):
            self.payroll.post_elr(
                "reversal",
                entry_id="REV3",
                reversal_of_entry_id="REV1",
                reason="reverse reversal",
            )

    def test_reversed_obligation_allows_one_exact_replacement(self):
        self.payroll.post_elr(
            "reversal",
            entry_id="REV-OB1",
            reversal_of_entry_id="OB1",
            reason="wrong authority recording",
        )
        self.assertEqual(self.payroll.elr_outstanding("OB1"), 0)
        self.payroll.record_obligation(
            "OB2", self.posted, 100_000, employer_id="ORG", authority_id="EPFO"
        )
        self.assertEqual(self.payroll.elr_outstanding("OB2"), 100_000)
        with self.assertRaises(Conflict):
            self.payroll.record_obligation(
                "OB3", self.posted, 100_000, employer_id="ORG", authority_id="EPFO"
            )

    def test_reversed_parents_reject_new_allocations_and_cross_tenant_reversal(self):
        self.payroll.post_elr(
            "reversal",
            entry_id="REV-REM1",
            reversal_of_entry_id="REM1",
            reason="void proof",
        )
        with self.assertRaises(PayrollError):
            self.payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 1)

        other = Payroll(self.connection, "T2", "U2")
        with self.assertRaises(PayrollError):
            other.post_elr(
                "reversal",
                entry_id="REV-X",
                reversal_of_entry_id="OB1",
                reason="wrong tenant",
            )

    def test_dispatch_rejects_open_or_wrong_shapes(self):
        with self.assertRaises(PayrollError):
            self.payroll.post_elr("unknown", entry_id="X")
        with self.assertRaises(PayrollError):
            self.payroll.post_elr([], entry_id="X")
        with self.assertRaises(PayrollError):
            self.payroll.post_elr(
                "reversal",
                entry_id="REV1",
                reversal_of_entry_id="OB1",
                reason="reason",
                amount_minor=100_000,
            )
        with self.assertRaises(PayrollError):
            self.payroll.post_elr(
                "reversal", entry_id="REV1", reversal_of_entry_id="OB1"
            )

    def test_full_allocation_replay_precedes_current_balance_checks(self):
        first = self.payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 100_000)
        self.assertEqual(
            self.payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 100_000),
            first,
        )
        with self.assertRaises(Conflict):
            self.payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 99_999)

        self.payroll.record_reversal("REV1", "ALLOC1", "wrong allocation")
        self.assertEqual(
            self.payroll.allocate_remittance("ALLOC1", "OB1", "REM1", 100_000),
            first,
        )

    def test_allocation_and_parent_reversal_are_serialized(self):
        barrier = threading.Barrier(2)
        results = []

        def run(kind):
            connection = connect(self.path)
            payroll = Payroll(connection, "T1", kind)
            barrier.wait()
            try:
                if kind == "allocate":
                    payroll.allocate_remittance("RACE-A", "OB1", "REM1", 1)
                else:
                    payroll.post_elr(
                        "reversal",
                        entry_id="RACE-R",
                        reversal_of_entry_id="OB1",
                        reason="race",
                    )
                results.append("ok")
            except (PayrollError, Conflict):
                results.append("rejected")
            finally:
                connection.close()

        threads = [threading.Thread(target=run, args=(kind,)) for kind in ("allocate", "reverse")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertCountEqual(results, ["ok", "rejected"])

    def test_cli_canonical_post_and_reverse_use_closed_bodies(self):
        config = Path(self.temp.name) / "cli.json"
        config.write_text(json.dumps({
            "database": str(self.path), "tenant": "T1", "actor": "U1", "format": "json"
        }))

        def invoke(command, payload):
            stdout, stderr = io.StringIO(), io.StringIO()
            with (
                patch.dict(os.environ, {"PAYROLL_CLI_CONFIG": str(config)}),
                patch.object(os.sys, "stdin", io.StringIO(json.dumps(payload))),
                redirect_stdout(stdout), redirect_stderr(stderr),
            ):
                status = main(["liability", command, "--input", "-"])
            self.assertEqual((status, stderr.getvalue()), (0, ""))
            return json.loads(stdout.getvalue())

        allocation = invoke("post", {
            "row_kind": "allocation", "entry_id": "CLI-A",
            "obligation_entry_id": "OB1", "remittance_entry_id": "REM1",
            "amount_minor": 25_000,
        })
        reversal = invoke("reverse", {
            "entry_id": "CLI-R", "reversal_of_entry_id": allocation["entry_id"],
            "reason": "wrong allocation",
        })
        self.assertEqual(reversal["reversal_of_entry_id"], "CLI-A")
        self.assertEqual(self.payroll.elr_outstanding("OB1"), 100_000)

    def test_proof_catalogue_closes_optional_reversal_reference(self):
        output = Path(self.temp.name) / "proof"
        run_proof(output)
        rows = json.loads((output / "canonical-rows.json").read_text())
        target = next(
            row for row in rows["payroll_employer_liability_ledger"]
            if row["row_kind"] == "allocation"
        )
        reversal = {
            **target,
            "entry_id": "REV-PROOF",
            "row_kind": "reversal",
            "reporting_period": target.get("reporting_period"),
            "posted_liability_entry_id": None,
            "obligation_entry_id": None,
            "remittance_entry_id": None,
            "proof_ref": None,
            "reversal_of_entry_id": target["entry_id"],
            "reason": "proof correction",
            "actor": "U1",
        }
        rows["payroll_employer_liability_ledger"].append(reversal)
        self.assertEqual(_catalogue(rows)["coverage"], {"covered": 16, "required": 16})
        reversal["reversal_of_entry_id"] = "MISSING"
        with self.assertRaisesRegex(ValueError, "reversal target"):
            _catalogue(rows)


if __name__ == "__main__":
    unittest.main()

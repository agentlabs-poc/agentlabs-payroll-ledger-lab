import io
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from sqlite_lab.cli import main


class CliContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / "cli.json"
        self.database = self.root / "payroll.sqlite"
        self.write_config()

    def tearDown(self):
        self.temp.cleanup()

    def write_config(self, **overrides):
        value = {
            "database": str(self.database),
            "tenant": "T1",
            "actor": "payroll-admin",
            "format": "json",
            **overrides,
        }
        self.config.write_text(json.dumps(value))

    def call(self, argv, input_text=""):
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.dict(os.environ, {"PAYROLL_CLI_CONFIG": str(self.config)}),
            patch.object(os.sys, "stdin", io.StringIO(input_text)),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            status = main(argv)
        output = stdout.getvalue().strip()
        error = stderr.getvalue().strip()
        return status, json.loads(output) if output else None, json.loads(error) if error else None

    def invoke(self, argv, payload=None):
        if payload is not None:
            argv = [*argv, "--input", "-"]
        status, output, error = self.call(argv, "" if payload is None else json.dumps(payload))
        self.assertEqual((status, error), (0, None))
        return output

    def init(self):
        self.invoke(["init"])

    def define_component(self, tenant=None, component_id="BASE", label="Base"):
        argv = ["component", "define"]
        if tenant:
            argv += ["--tenant", tenant]
        return self.invoke(argv, {
            "component_id": component_id,
            "revision": 1,
            "code": "BASE",
            "label": label,
            "kind": "earning",
            "country_code": "IN",
        })

    def test_configure_and_precedence_resolve_stable_database_paths(self):
        configured = self.root / "configured.json"
        database = self.root / "configured.sqlite"
        status, output, error = self.call([
            "configure", "--config", str(configured), "--db", str(database),
            "--tenant", "ENV", "--actor", "operator", "--format", "json",
        ])
        self.assertEqual((status, error), (0, None))
        saved = json.loads(configured.read_text())
        self.assertEqual(saved["database"], str(database.resolve()))
        self.assertEqual(output["status"], "configured")

        explicit = self.root / "nested" / "explicit.json"
        explicit.parent.mkdir()
        explicit.write_text(json.dumps({
            "database": "relative.sqlite", "tenant": "EXPLICIT",
            "actor": "operator", "format": "json",
        }))
        status, _, error = self.call(["init", "--config", str(explicit)])
        self.assertEqual((status, error), (0, None))
        self.assertTrue((explicit.parent / "relative.sqlite").is_file())

        override = self.root / "override.sqlite"
        status, _, error = self.call([
            "init", "--config", str(explicit), "--db", str(override),
            "--tenant", "FLAG",
        ])
        self.assertEqual((status, error), (0, None))
        self.assertTrue(override.is_file())

    def test_config_rejects_invalid_json_unknown_fields_and_wrong_types(self):
        cases = (
            ("{", "invalid config JSON"),
            (json.dumps([]), "config must be an object"),
            (json.dumps({"database": "x", "tenant": "T1", "actor": "a", "format": "json", "extra": True}), "only database"),
            (json.dumps({"database": 7, "tenant": "T1", "actor": "a", "format": "json"}), "nonempty strings"),
            (json.dumps({"database": "x", "tenant": "T1", "actor": "a", "format": "yaml"}), "json or table"),
        )
        for text, message in cases:
            with self.subTest(text=text):
                self.config.write_text(text)
                status, _, error = self.call(["operations"])
                self.assertEqual(status, 1)
                self.assertIn(message, error["message"])

    def test_operation_input_rejects_invalid_json_non_objects_and_bad_types(self):
        self.init()
        for text, error_type in (("{", "JSONDecodeError"), ("[]", "ValueError")):
            with self.subTest(text=text):
                status, _, error = self.call(["component", "define", "--input", "-"], text)
                self.assertEqual(status, 1)
                self.assertEqual(error["error"], error_type)
        payload = {
            "component_id": "BASE", "revision": True, "code": "BASE",
            "label": "Base", "kind": "earning", "country_code": "IN",
        }
        status, _, error = self.call(
            ["component", "define", "--input", "-"], json.dumps(payload)
        )
        self.assertEqual(status, 1)
        self.assertIn("revision", error["message"])

    def test_natural_reads_keep_tenant_and_escaped_employee_owners_isolated(self):
        self.init()
        component = self.define_component(label="Tenant one")
        self.define_component(tenant="T2", label="Tenant two")
        key = component["key"]
        first = "EMP:1\\West"
        second = "EMP:2\\East"
        for employee, amount in ((first, 100), (second, 200)):
            self.invoke(["earning", "define"], {
                "earning_id": "LOCAL:PAY\\1", "revision": 1,
                "employee_id": employee, "component_key": key,
                "amount_minor": amount, "effective_from": "2026-11",
            })

        for employee, amount in ((first, 100), (second, 200)):
            history = self.invoke(["record", "history"], {
                "record_type": "payroll.earning", "employee_id": employee,
                "earning_id": "LOCAL:PAY\\1",
            })
            self.assertEqual([row["value"]["amount_minor"] for row in history], [amount])
            self.assertIn("\\:", history[0]["key"])
            self.assertIn("\\\\", history[0]["key"])

        tenant_one = self.invoke(["record", "get"], {"key": key})
        tenant_two = self.invoke(["record", "get", "--tenant", "T2"], {"key": key})
        self.assertEqual(tenant_one["value"]["label"], "Tenant one")
        self.assertEqual(tenant_two["value"]["label"], "Tenant two")

    def test_reset_clears_all_tenants_and_preserves_config_and_topology(self):
        self.init()
        self.define_component()
        self.define_component(tenant="T2", label="Other")
        before = self.config.read_bytes()
        result = self.invoke(["reset"])
        self.assertEqual(result["status"], "reset")
        self.assertEqual(self.config.read_bytes(), before)

        database = sqlite3.connect(self.database)
        tables = [row[0] for row in database.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        self.assertEqual(tables, [
            "payroll_draft_ledger", "payroll_employer_liability_ledger",
            "payroll_l1_records", "payroll_l2_records", "payroll_ledger",
        ])
        self.assertTrue(all(database.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0 for table in tables))
        database.close()

    def test_reset_refuses_foreign_database_without_changing_it(self):
        foreign = self.root / "foreign.sqlite"
        database = sqlite3.connect(foreign)
        database.execute("CREATE TABLE notes(value TEXT)")
        database.execute("INSERT INTO notes VALUES ('keep')")
        database.commit()
        database.close()
        self.write_config(database=str(foreign))

        status, _, error = self.call(["reset"])
        self.assertEqual(status, 1)
        self.assertIn("incompatible payroll SQLite prototype", error["message"])
        database = sqlite3.connect(foreign)
        self.assertEqual(database.execute("SELECT value FROM notes").fetchall(), [("keep",)])
        database.close()

    def test_reset_refuses_foreign_database_spoofing_the_five_table_names(self):
        foreign = self.root / "foreign-five.sqlite"
        tables = (
            "payroll_l1_records", "payroll_l2_records", "payroll_draft_ledger",
            "payroll_ledger", "payroll_employer_liability_ledger",
        )
        database = sqlite3.connect(foreign)
        for table in tables:
            database.execute(f"CREATE TABLE {table}(marker TEXT)")
        database.execute("INSERT INTO payroll_l1_records VALUES ('keep')")
        database.commit()
        database.close()
        self.write_config(database=str(foreign))

        status, _, error = self.call(["reset"])
        self.assertEqual(status, 1)
        self.assertIn("incompatible payroll SQLite prototype", error["message"])
        database = sqlite3.connect(foreign)
        self.assertEqual(database.execute("SELECT marker FROM payroll_l1_records").fetchall(), [("keep",)])
        database.close()

    def test_commit_control_and_policy_flags_require_exact_json_types(self):
        self.init()
        component = self.define_component()
        earning = self.invoke(["earning", "define"], {
            "earning_id": "SALARY", "revision": 1, "employee_id": "E101",
            "component_key": component["key"], "amount_minor": 100,
            "effective_from": "2026-11",
        })
        invalid = (
            ("expected_control_revision", True),
            ("approval_required", 0),
            ("reconcile_sources", "false"),
            ("fresh_review_required", 1),
        )
        for index, (field, value) in enumerate(invalid):
            draft_id = f"D{index}"
            self.invoke(["draft", "create"], {
                "draft_id": draft_id, "employee_id": "E101",
                "payroll_month": "2026-11", "earning_keys": [earning["key"]],
                "instruction_version_ids": [],
            })
            payload = {
                "draft_id": draft_id, "employee_id": "E101",
                "idempotency_key": f"commit-{index}",
                "expected_control_revision": 1,
                field: value,
            }
            with self.subTest(field=field, value=value):
                status, _, error = self.call(
                    ["draft", "commit", "--input", "-"], json.dumps(payload)
                )
                self.assertEqual(status, 1)
                self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()

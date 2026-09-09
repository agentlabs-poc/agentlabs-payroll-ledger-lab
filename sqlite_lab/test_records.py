import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from sqlite_lab.records import RecordError, RecordStore, canonical_key, connect, parse_key


class RecordStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "records.sqlite3"
        self.connection = connect(self.path)
        self.store = RecordStore(self.connection)

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def component(self, component_id, revision, label=None):
        return {
            "schema_version": 1,
            "component_id": component_id,
            "revision": revision,
            "code": component_id.replace(":", "-").replace("\\", "-"),
            "label": label or component_id,
            "kind": "earning",
            "country_code": "IN",
        }

    def test_exact_three_ledger_topology_has_five_physical_tables(self):
        names = {row[0] for row in self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )}
        self.assertEqual(names, {
            "payroll_draft_ledger", "payroll_ledger",
            "payroll_employer_liability_ledger", "payroll_l1_records",
            "payroll_l2_records",
        })

    def test_connect_refuses_an_existing_incompatible_prototype(self):
        legacy_path = Path(self.temp.name) / "legacy.sqlite3"
        legacy = sqlite3.connect(legacy_path)
        legacy.execute("CREATE TABLE payroll_calculations(id TEXT)")
        legacy.close()
        with self.assertRaisesRegex(RuntimeError, "incompatible payroll SQLite prototype"):
            connect(legacy_path)

    def test_canonical_key_escapes_identity_colon_and_backslash_and_preserves_case(self):
        key = canonical_key("payroll.component", "Ab:C\\D.x_9", 10)
        self.assertEqual(key, "payroll.component:Ab\\:C\\\\D.x_9:10")
        self.assertEqual(parse_key(key), ("payroll.component", "Ab:C\\D.x_9", 10))
        review_key = canonical_key("payroll.draft.review", "E:1", "D:1", "R\\2:west")
        self.assertEqual(review_key, "payroll.draft.review:E\\:1:D\\:1:R\\\\2\\:west")
        self.assertEqual(parse_key(review_key),
                         ("payroll.draft.review", "E:1", "D:1", "R\\2:west"))

    def test_record_key_is_reconstructed_from_stored_segments(self):
        component_id = "C:East\\Legacy.1"
        key = canonical_key("payroll.component", component_id, 10)
        value = self.component(component_id, 10)

        stored = self.store._put_l1("T1", key, value)
        row = self.connection.execute(
            "SELECT key1,key2,key3,key4,key5,key10,key,value FROM payroll_l1_records"
        ).fetchone()

        self.assertEqual(tuple(row[:7]),
                         ("payroll", "component", component_id, "10", "", "", key))
        self.assertEqual(stored["value"], value)
        self.assertNotIn("key", stored["value"])

    def test_generated_key_cannot_disagree_with_stored_segments(self):
        columns = ",".join(f"key{index}" for index in range(1, 11))
        slots = ("payroll", "component", "C1", "1", "", "", "", "", "", "")
        with self.assertRaisesRegex(sqlite3.OperationalError, "generated column"):
            self.connection.execute(
                f"INSERT INTO payroll_l1_records(tenant,{columns},key,value,ts,state) "
                f"VALUES({','.join('?' for _ in range(15))})",
                ("T1", *slots, "payroll.component:WRONG:1",
                 '{}', "2026-09-09T00:00:00+00:00", "enabled"),
            )

    def test_storage_rejects_gapped_segments_and_duplicate_full_identity(self):
        columns = ",".join(f"key{index}" for index in range(1, 11))
        insert = (f"INSERT INTO payroll_l1_records(tenant,{columns},value,ts,state) "
                  f"VALUES({','.join('?' for _ in range(14))})")
        with self.assertRaises(sqlite3.OperationalError):
            self.connection.execute(
                insert,
                ("T1", "payroll", "component", "", "1", "", "", "", "", "", "",
                 '{}', "2026-09-09T00:00:00+00:00", "enabled"),
            )

        key = canonical_key("payroll.component", "C1", 1)
        value = self.component("C1", 1)
        self.store._put_l1("T1", key, value)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._put_l1("T1", key, value)

    def test_component_prefix_lookup_uses_full_identity_index(self):
        key = canonical_key("payroll.component", "C1", 1)
        self.store._put_l1("T1", key, self.component("C1", 1))
        query = ("SELECT key FROM payroll_l1_records "
                 "WHERE tenant=? AND key1=? AND key2=? AND key3=?")

        self.assertEqual(
            self.connection.execute(query, ("T1", "payroll", "component", "C1")).fetchone()[0],
            key,
        )
        plan = self.connection.execute(
            "EXPLAIN QUERY PLAN " + query,
            ("T1", "payroll", "component", "C1"),
        ).fetchall()
        self.assertTrue(any(
            "USING INDEX" in row[3]
            and "tenant=? AND key1=? AND key2=? AND key3=?" in row[3]
            for row in plan
        ), plan)

    def test_employee_owned_keys_require_the_registered_owner_arity(self):
        expected = {
            "payroll.earning": ("E101", "EARN", 2),
            "payroll.instruction": ("E101", "I1", 2),
            "payroll.draft": ("E101", "D1", 1),
            "payroll.draft.control": ("E101", "D1", 3),
            "payroll.draft.review": ("E101", "D1", "R1"),
            "payroll.instruction.resolution": ("E101", "D1", "RES1"),
            "payroll.instruction.application": ("E101", "I1", "APP1"),
            "payroll.operation.receipt": ("E101", "D1", "RCPT1"),
            "payroll.employee.settings": ("E101", 2),
        }
        for record_type, identity in expected.items():
            with self.subTest(record_type=record_type):
                key = canonical_key(record_type, *identity)
                self.assertEqual(parse_key(key), (record_type, *identity))
        for old_key in (
            "payroll.earning:EARN:2",
            "payroll.draft:D1:1",
            "payroll.operation.receipt:D1:RCPT1",
        ):
            with self.subTest(old_key=old_key), self.assertRaises(RecordError):
                parse_key(old_key)

    def test_canonical_key_rejects_malformed_segments_and_unnecessary_escapes(self):
        for invalid in ("", "E/101", "white space", "../E101"):
            with self.subTest(invalid=invalid), self.assertRaises(RecordError):
                canonical_key("payroll.component", invalid, 1)
        malformed_keys = (
            "payroll.component:subject",
            "payroll.component::1",
            "payroll.component:subject:",
            "payroll.component:subject:1:extra",
            "payroll.component:sub\\.ject:1",
            "payroll.component:subject\\:1",
            "payroll.component:subject:1/",
        )
        for key in malformed_keys:
            with self.subTest(key=key), self.assertRaises(RecordError):
                parse_key(key)

    def test_l1_and_l2_are_separate_scopes_and_l1_has_no_public_generic_write(self):
        key = canonical_key("payroll.component", "E101", 1)
        self.store._put_l1("T1", key, self.component("E101", 1))
        settings = {
            "schema_version": 1, "employee_id": "E101", "revision": 1,
            "effective_from": "2026-11", "policy_ref": {"id": "P1", "revision": 1},
            "payslip_locale": "en-IN",
        }
        self.store.put_l2_settings("T1", settings)
        self.assertEqual(self.store.get_l1("T1", key)["value"]["component_id"], "E101")
        self.assertIsNone(self.store.get_l2("T1", key))
        self.assertEqual(
            tuple(self.connection.execute(
                "SELECT key1,key2,key3,key4,key5 FROM payroll_l1_records"
            ).fetchone()),
            ("payroll", "component", "E101", "1", ""),
        )
        self.assertEqual(
            tuple(self.connection.execute(
                "SELECT key1,key2,key3,key4,key5 FROM payroll_l2_records"
            ).fetchone()),
            ("payroll", "employee", "settings", "E101", "1"),
        )
        self.assertFalse(hasattr(self.store, "put_l1"))

    def test_payload_must_be_object_with_exact_schema_and_key_identity(self):
        key = canonical_key("payroll.component", "C1", 1)
        invalid_payloads = [
            [],
            {**self.component("C2", 1)},
            {**self.component("C1", 1), "unknown": True},
            {**self.component("C1", 1), "label": None},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload), self.assertRaises(RecordError):
                self.store._put_l1("T1", key, payload)

    def test_versions_are_positive_integers_and_order_numerically(self):
        for revision in (2, 10):
            self.store._put_l1(
                "T1", canonical_key("payroll.component", "C1", revision),
                self.component("C1", revision),
            )
        self.assertEqual(
            [record["value"]["revision"] for record in
             self.store.history_l1("T1", "payroll.component", "C1")],
            [2, 10],
        )
        with self.assertRaises(RecordError):
            self.store._put_l1(
                "T1", canonical_key("payroll.component", "C1", "0"),
                self.component("C1", 0),
            )

    def test_escaped_subject_history_orders_revisions_numerically(self):
        component_id = "C:East\\Legacy.1"
        for revision in (10, 2):
            self.store._put_l1(
                "T1", canonical_key("payroll.component", component_id, revision),
                self.component(component_id, revision),
            )
        self.assertEqual(
            [row["value"]["revision"] for row in
             self.store.history_l1("T1", "payroll.component", component_id)],
            [2, 10],
        )

    def test_history_subject_match_is_case_sensitive_and_not_a_like_pattern(self):
        for component_id in ("C1", "c1", "C_1", "CA1"):
            self.store._put_l1(
                "T1", canonical_key("payroll.component", component_id, 1),
                self.component(component_id, 1),
            )
        self.assertEqual(
            [row["value"]["component_id"] for row in
             self.store.history_l1("T1", "payroll.component", "C1")],
            ["C1"],
        )
        self.assertEqual(
            [row["value"]["component_id"] for row in
             self.store.history_l1("T1", "payroll.component", "C_1")],
            ["C_1"],
        )

    def test_duplicate_identity_is_rejected_even_when_content_matches(self):
        key = canonical_key("payroll.component", "C1", 1)
        value = self.component("C1", 1)
        self.store._put_l1("T1", key, value)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._put_l1("T1", key, value)

    def test_insert_or_replace_cannot_rewrite_l1_history(self):
        key = canonical_key("payroll.component", "C1", 1)
        self.store._put_l1("T1", key, self.component("C1", 1))
        slots = ("payroll", "component", "C1", "1", "", "", "", "", "", "")
        columns = ",".join(f"key{index}" for index in range(1, 11))
        replacement = self.component("C1", 1, label="rewritten")

        with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable"):
            self.connection.execute(
                f"INSERT OR REPLACE INTO payroll_l1_records(tenant,{columns},value,ts,state) "
                f"VALUES({','.join('?' for _ in range(14))})",
                ("T1", *slots, json.dumps(replacement),
                 "2026-09-09T00:00:00+00:00", "enabled"),
            )

        self.assertEqual(self.store.get_l1("T1", key)["value"]["label"], "C1")

    def test_disabled_latest_component_does_not_revive_older_enabled_revision(self):
        self.store._put_l1("T1", canonical_key("payroll.component", "C1", 1),
                           self.component("C1", 1), state="enabled")
        self.store._put_l1("T1", canonical_key("payroll.component", "C1", 2),
                           self.component("C1", 2), state="disabled")
        self.assertIsNone(self.store.current_l1("T1", "payroll.component", "C1"))
        self.assertEqual(
            self.store.get_l1("T1", canonical_key("payroll.component", "C1", 1))["state"],
            "enabled",
        )

    def test_effective_settings_differs_from_current_revision(self):
        def settings(revision, effective_from, locale):
            return {
                "schema_version": 1, "employee_id": "E101", "revision": revision,
                "effective_from": effective_from,
                "policy_ref": {"id": "P1", "revision": 1},
                "payslip_locale": locale,
            }
        self.store.put_l2_settings("T1", settings(1, "2026-01", "en-IN"))
        self.store.put_l2_settings("T1", settings(2, "2027-01", "hi-IN"))
        self.assertEqual(self.store.current_l2_settings("T1", "E101")["value"]["revision"], 2)
        self.assertEqual(
            self.store.effective_l2_settings("T1", "E101", "2026-11")["value"]["revision"],
            1,
        )

    def test_current_and_effective_settings_accept_escaped_employee_identity(self):
        employee_id = "EMP:101\\A"
        self.store.put_l2_settings("T1", {
            "schema_version": 1, "employee_id": employee_id, "revision": 1,
            "effective_from": "2026-11", "policy_ref": {"id": "P:1", "revision": 1},
            "payslip_locale": "en-IN",
        })
        self.assertEqual(
            self.store.current_l2_settings("T1", employee_id)["value"]["employee_id"],
            employee_id,
        )
        self.assertEqual(
            self.store.effective_l2_settings("T1", employee_id, "2026-11")["value"]["employee_id"],
            employee_id,
        )

    def test_generic_reads_reject_malformed_canonical_keys(self):
        malformed = "payroll.component:sub\\.ject:1"
        with self.assertRaises(RecordError):
            self.store.get_l1("T1", malformed)
        with self.assertRaises(RecordError):
            self.store.get_l2("T1", malformed)

    def test_foreign_keys_are_enabled_for_every_connection(self):
        self.assertEqual(self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()

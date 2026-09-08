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

    def test_canonical_key_escapes_identity_colon_and_backslash_and_preserves_case(self):
        key = canonical_key("payroll.component", "Ab:C\\D.x_9", 10)
        self.assertEqual(key, "payroll.component:Ab\\:C\\\\D.x_9:10")
        self.assertEqual(parse_key(key), ("payroll.component", "Ab:C\\D.x_9", 10))
        review_key = canonical_key("payroll.draft.review", "D:1", "R\\2:west")
        self.assertEqual(review_key, "payroll.draft.review:D\\:1:R\\\\2\\:west")
        self.assertEqual(parse_key(review_key),
                         ("payroll.draft.review", "D:1", "R\\2:west"))

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

    def test_foreign_keys_are_enabled_for_every_connection(self):
        self.assertEqual(self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()

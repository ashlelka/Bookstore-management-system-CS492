"""TT: T2-001 and T2-009 regression tests; run python -m unittest test_timur_sprint2 -v."""
import csv
import io
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import customer_management as customers
import database
import sales_reports as reports
import sales_app
import user_management
import users


class Sprint2Tests(unittest.TestCase):
    def setUp(self):
        # TT: Every write is redirected to temporary files, including staff permissions.
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for module, attribute, filename in (
            (database, "SALES_PATH", "sales.json"),
            (customers, "CUSTOMERS_PATH", "customers.json"),
            (user_management, "USERS_FILE", "users.json"),
            (users, "OVERRIDES_PATH", "overrides.json"),
        ):
            patcher = patch.object(module, attribute, root / filename)
            patcher.start()
            self.addCleanup(patcher.stop)
        user_management.save_users([
            {"user_id": 1, "username": "manager", "role": "Manager", "active": True},
            {"user_id": 2, "username": "cashier", "role": "Cashier", "active": True},
            {"user_id": 3, "username": "admin", "role": "Admin", "active": True},
        ])
        self.client = sales_app.app.test_client()
        self.signin()

    def signin(self, username="manager"):
        with self.client.session_transaction() as session:
            session.clear()
            if username:
                session["username"] = username

    def form(self, **changes):
        self.client.get("/customers/new")
        with self.client.session_transaction() as session:
            token = session["customer_csrf"]
        return {"first_name": "Test", "last_name": "Customer", "email": "test@example.com",
                "csrf_token": token, **changes}

    def fixture(self):
        rows = [{"sale_id": "SALE-1042", "timestamp": stamp,
                 "subtotal": 10.005, "tax": .63, "total": 10.635}
                for stamp in ("2026-09-06T23:59:59", "2026-09-07T00:00:00",
                              "2026-09-13T23:59:59", "2026-09-14T00:00:00",
                              "2026-10-01T00:00:00")]
        database.save_sales(rows)
        return rows

    def test_T2_001_period_boundaries(self):
        self.fixture()
        self.assertEqual(reports.generate_report("daily", "2026-09-13")["count"], 1)
        week = reports.generate_report("weekly", "2026-09-13")
        self.assertEqual((week["start"], week["end"], week["count"]),
                         (date(2026, 9, 7), date(2026, 9, 13), 2))
        self.assertEqual(reports.generate_report("monthly", "2026-09-20")["count"], 4)
        self.assertEqual(reports.period_bounds("monthly", "2024-02-01")[1], date(2024, 2, 29))
        self.assertEqual(reports.period_bounds("monthly", "2026-12-31")[1], date(2026, 12, 31))
        self.assertEqual(reports.period_bounds("weekly", "2026-01-01")[0], date(2025, 12, 29))

    def test_T2_001_totals_keep_duplicate_legacy_ids(self):
        self.fixture()
        report = reports.generate_report("weekly", "2026-09-13")
        self.assertEqual(report["total"], Decimal("21.28"))
        self.assertEqual(report["subtotal"], Decimal("20.02"))
        self.assertEqual(report["tax"], Decimal("1.26"))
        self.assertEqual(report["count"], 2)

    def test_T2_001_empty_and_missing_store(self):
        for output in ("html", "csv", "pdf"):
            response = self.client.get("/reports?date=2020-01-01&format=" + output)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(reports.generate_report("daily", "2020-01-01")["total"], 0)

    def test_T2_001_html_csv_pdf_same_totals(self):
        self.fixture()
        base = "/reports?period=weekly&date=2026-09-13"
        self.assertIn(b"21.28", self.client.get(base).data)
        response = self.client.get(base + "&format=csv")
        rows = list(csv.reader(io.StringIO(response.get_data(as_text=True))))
        self.assertEqual(rows[-1], ["TOTAL", "2", "20.02", "1.26", "21.28"])
        self.assertEqual(response.mimetype, "text/csv")
        pdf = self.client.get(base + "&format=pdf")
        self.assertEqual(pdf.mimetype, "application/pdf")
        self.assertTrue(pdf.data.startswith(b"%PDF-"))
        self.assertIn("attachment", pdf.headers["Content-Disposition"])

    def test_T2_001_invalid_filters(self):
        for query in ("date=bad", "date=2026-02-30", "period=yearly", "format=exe"):
            with self.subTest(query=query):
                self.assertEqual(self.client.get("/reports?" + query).status_code, 400)

    def test_T2_001_corrupt_source_never_becomes_zero_report(self):
        for data in ("broken json", '{"sales": null}', '[{"timestamp":"bad"}]'):
            database.SALES_PATH.write_text(data)
            for output in ("html", "csv", "pdf"):
                self.assertEqual(self.client.get("/reports?format=" + output).status_code, 503)
            self.assertEqual(database.SALES_PATH.read_text(), data)

    def test_T2_001_invalid_amounts(self):
        for amount in (None, "NaN", "Infinity", "bad"):
            database.save_sales([{"sale_id": "A", "timestamp": "2026-09-20T00:00:00",
                                  "subtotal": 1, "tax": 0, "total": amount}])
            self.assertEqual(self.client.get("/reports?date=2026-09-20").status_code, 503)

    def test_T2_001_csv_formula_and_html_escaping(self):
        rows = self.fixture()
        rows[2]["sale_id"] = "=SUM(1,2)"
        database.save_sales(rows)
        report = reports.generate_report("daily", "2026-09-13")
        cells = list(csv.reader(io.StringIO(reports.csv_report(report))))
        self.assertEqual(cells[2][0], "'=SUM(1,2)")
        rows[2]["sale_id"] = "<script>alert(1)</script>"
        database.save_sales(rows)
        self.assertNotIn(b"<script>alert(1)</script>", self.client.get("/reports?date=2026-09-13").data)
        self.assertTrue(reports.pdf_report(reports.generate_report("daily", "2026-09-13")).startswith(b"%PDF"))

    def test_T2_001_list_store_supported_and_source_unchanged(self):
        rows = self.fixture()
        database.SALES_PATH.write_text(json.dumps(rows))
        before = database.SALES_PATH.read_bytes()
        self.assertEqual(reports.generate_report("monthly", "2026-09-01")["count"], 4)
        self.assertEqual(database.SALES_PATH.read_bytes(), before)

    def test_T2_001_multi_page_pdf(self):
        database.save_sales([{"sale_id": f"SALE-{i}", "timestamp": "2026-09-20T12:00:00",
                              "subtotal": 10, "tax": 1, "total": 11} for i in range(150)])
        pdf = reports.pdf_report(reports.generate_report("daily", "2026-09-20"))
        # TT: ReportLab writes one /Type /Page entry per page, plus /Pages for the tree.
        self.assertGreater(pdf.count(b"/Type /Page\n"), 1)

    def test_T2_009_add_and_edit_profile(self):
        response = self.client.post("/customers/new", data=self.form())
        self.assertEqual(response.status_code, 302)
        row = customers.load_customers()[0]
        fields = self.form(first_name="Edited", updated_at=row["updated_at"])
        edited = self.client.post(f"/customers/{row['customer_id']}/edit", data=fields)
        self.assertEqual(edited.status_code, 302)
        saved = customers.get_customer(row["customer_id"])
        self.assertEqual(saved["created_at"], row["created_at"])
        self.assertEqual(saved["first_name"], "Edited")
        self.assertEqual(len(customers.load_customers()), 1)
        self.assertIn(b"Edited", self.client.get(response.location).data)

    def test_T2_009_unknown_fields_and_loyalty_preserved(self):
        row = customers.save_customer(self.form())
        row.update(loyalty_points=55, future_field="keep me")
        customers.CUSTOMERS_PATH.write_text(json.dumps([row]))
        customers.save_customer(self.form(first_name="New"), row["customer_id"])
        saved = customers.get_customer(row["customer_id"])
        self.assertEqual((saved["loyalty_points"], saved["future_field"]), (55, "keep me"))

    def test_T2_009_duplicate_email_and_required_names(self):
        self.client.post("/customers/new", data=self.form())
        for fields in (self.form(email="TEST@example.com"), self.form(first_name=" "),
                       self.form(email="bad"), self.form(address="a" * 501)):
            self.assertEqual(self.client.post("/customers/new", data=fields).status_code, 400)
        self.assertEqual(len(customers.load_customers()), 1)

    def test_T2_009_optional_contact_fields(self):
        response = self.client.post("/customers/new", data=self.form(email="", phone="", address=""))
        self.assertEqual(response.status_code, 302)

    def test_T2_009_stale_form_conflict(self):
        row = customers.save_customer(self.form())
        stale = self.form(first_name="Stale", updated_at=row["updated_at"])
        customers.save_customer(self.form(first_name="Latest"), row["customer_id"])
        response = self.client.post(f"/customers/{row['customer_id']}/edit", data=stale)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(customers.get_customer(row["customer_id"])["first_name"], "Latest")

    def test_T2_009_corrupt_store_preserved(self):
        for bad in ("not json", '{}', '[{"first_name":"No ID"}]'):
            customers.CUSTOMERS_PATH.write_text(bad)
            self.assertEqual(self.client.get("/customers").status_code, 503)
            response = self.client.post("/customers/new", data=self.form())
            self.assertEqual(response.status_code, 503)
            self.assertEqual(customers.CUSTOMERS_PATH.read_text(), bad)

    def test_T2_009_csrf_and_html_escaping(self):
        for token in ("", "wrong", "тест"):
            self.assertEqual(self.client.post("/customers/new", data=self.form(csrf_token=token)).status_code, 400)
        response = self.client.post("/customers/new", data=self.form(first_name="<script>test</script>"))
        self.assertNotIn(b"<script>test</script>", self.client.get(response.location).data)
        self.assertIn(b"&lt;script&gt;", self.client.get(response.location).data)

    def test_T2_009_missing_profile(self):
        self.assertEqual(self.client.get("/customers/missing").status_code, 404)
        self.assertEqual(self.client.get("/customers/missing/edit").status_code, 404)

    def test_T2_009_write_failure_preserves_original(self):
        row = customers.save_customer(self.form())
        before = customers.CUSTOMERS_PATH.read_bytes()
        with patch("customer_management.os.fsync", side_effect=OSError("disk error")):
            with self.assertRaises(customers.CustomerStoreError):
                customers.save_customer(self.form(first_name="Not saved"), row["customer_id"])
        self.assertEqual(customers.CUSTOMERS_PATH.read_bytes(), before)
        self.assertEqual(list(customers.CUSTOMERS_PATH.parent.glob(".customers-*.tmp")), [])

    def test_access_roles_locks_and_permission_revocation(self):
        for path in ("/reports", "/reports?format=csv", "/reports?format=pdf", "/customers", "/customers/new"):
            with self.subTest(path=path):
                self.signin(None)
                self.assertEqual(self.client.get(path).status_code, 302)
                self.signin("cashier")
                self.assertEqual(self.client.get(path).status_code, 403)
                self.signin("admin")
                self.assertEqual(self.client.get(path).status_code, 200)
                users.set_locked("admin", True)
                self.assertEqual(self.client.get(path).status_code, 403)
                users.set_locked("admin", False)
                users.set_permissions("admin", ["use_pos"])
                self.assertEqual(self.client.get(path).status_code, 403)
                users.assign_role("admin", "Admin")

    def test_existing_timeout_applies_to_new_pages(self):
        with self.client.session_transaction() as session:
            session["last_activity"] = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        self.assertEqual(self.client.get("/customers").status_code, 302)

    def test_navigation_and_cache_headers(self):
        page = self.client.get("/").get_data(as_text=True)
        for path in ("/reports", "/customers", "/financial-dashboard", "/suppliers", "/purchase-orders"):
            self.assertIn(f'href="{path}"', page)
        self.assertEqual(self.client.get("/customers").headers["Cache-Control"], "no-store")


if __name__ == "__main__":
    unittest.main()

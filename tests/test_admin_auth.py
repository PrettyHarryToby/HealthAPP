import os
import secrets
import unittest
from unittest.mock import patch

import database


class FakeCursor(list):
    def sort(self, key, direction):
        return FakeCursor(sorted(self, key=lambda row: row.get(key, ""), reverse=direction < 0))

    def limit(self, count):
        return FakeCursor(self[:count])


class FakeCollection:
    def __init__(self):
        self.documents = []

    def create_index(self, *args, **kwargs):
        return None

    def update_one(self, *args, **kwargs):
        return None

    def find_one(self, *args, **kwargs):
        return None

    def insert_one(self, document):
        self.documents.append(document)

    def count_documents(self, query):
        return len(self.documents)

    def find(self, query, projection=None):
        return FakeCursor(self.documents)


class FakeDatabase(dict):
    name = "test_healthapp"

    def __getitem__(self, name):
        if name not in self:
            self[name] = FakeCollection()
        return super().__getitem__(name)


class AdminAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_database = FakeDatabase()
        cls.original_username = os.environ.get("ADMIN_USERNAME")
        cls.original_password = os.environ.get("ADMIN_PASSWORD")
        cls.original_client = database._client
        cls.database_patch = patch.object(database, "mongo_database", cls.fake_database)
        cls.init_patch = patch.object(database, "init_database")
        cls.test_username = "test-admin"
        cls.test_password = secrets.token_urlsafe(24)
        cls.database_patch.start()
        cls.init_patch.start()
        os.environ["ADMIN_USERNAME"] = cls.test_username
        os.environ["ADMIN_PASSWORD"] = cls.test_password
        import app_web
        cls.app = app_web.app
        cls.app.config.update(TESTING=True)

    def setUp(self):
        self.client = self.app.test_client()
        self.fake_database["admin_events"].documents.clear()

    @classmethod
    def tearDownClass(cls):
        cls.init_patch.stop()
        cls.database_patch.stop()
        if cls.original_client:
            cls.original_client.close()
        if cls.original_username is None:
            os.environ.pop("ADMIN_USERNAME", None)
        else:
            os.environ["ADMIN_USERNAME"] = cls.original_username
        if cls.original_password is None:
            os.environ.pop("ADMIN_PASSWORD", None)
        else:
            os.environ["ADMIN_PASSWORD"] = cls.original_password

    def test_workspace_requires_login(self):
        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.headers["Location"])

    def test_patient_portal_is_publicly_discoverable(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Patient portal", response.data)
        self.assertIn(b"Staff sign in", response.data)

    def test_public_homepage_policies_and_patient_login(self):
        for path, expected in (
            ("/login", b"Welcome back"),
            ("/portal/login", b"Welcome back"),
            ("/faq", b"Frequently asked questions"),
            ("/terms", b"Terms of use"),
            ("/privacy", b"Privacy notice"),
            ("/about", b"About Avenara"),
            ("/how-it-works", b"How it works"),
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected, response.data)

    def test_mobile_menu_contains_new_public_pages(self):
        response = self.client.get("/")

        self.assertIn(b'aria-controls="mobile-menu"', response.data)
        self.assertIn(b'id="mobile-menu"', response.data)
        self.assertIn(b'href="/about"', response.data)
        self.assertIn(b'href="/how-it-works"', response.data)
        self.assertIn(b"Patient sign in", response.data)

    def test_standalone_public_pages_offer_back_to_home(self):
        for path in ("/login", "/admin/login", "/portal/register", "/faq", "/terms", "/privacy"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Back to home", response.data)
                self.assertIn(b'href="/"', response.data)

    def test_authenticated_pages_offer_return_to_workspace(self):
        with self.client.session_transaction() as browser_session:
            browser_session["admin_authenticated"] = True

        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Back to overview", response.data)
        self.assertIn(b'href="/dashboard"', response.data)

    def test_brand_mark_is_served_and_used_as_favicon(self):
        homepage = self.client.get("/")
        favicon = self.client.get("/static/avenara-mark.svg")

        self.assertEqual(favicon.status_code, 200)
        self.assertEqual(favicon.mimetype, "image/svg+xml")
        self.assertIn(b"Avenara", homepage.data)
        self.assertNotIn(b"Health Database", homepage.data)
        self.assertIn(b'rel="icon" type="image/svg+xml"', homepage.data)
        self.assertIn(b"avenara-mark.svg", homepage.data)
        favicon.close()

    def test_patient_session_cannot_access_staff_routes(self):
        with self.client.session_transaction() as browser_session:
            browser_session["portal_patient_id"] = 42

        response = self.client.get("/patients")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/portal", response.headers["Location"])

    def test_valid_login_opens_admin_console(self):
        self.client.get("/admin/login")
        with self.client.session_transaction() as browser_session:
            token = browser_session["csrf_token"]

        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": token,
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        self.assertEqual(response.status_code, 302)
        dashboard_response = self.client.get("/dashboard")
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertIn(b"Dashboard Overview", dashboard_response.data)
        admin_response = self.client.get("/admin")
        self.assertEqual(admin_response.status_code, 200)
        self.assertIn(b"System console", admin_response.data)
        self.assertIn(b"Recent admin activity", admin_response.data)
        self.assertIn(b"Login", admin_response.data)
        self.assertEqual(len(self.fake_database["admin_events"].documents), 1)


if __name__ == "__main__":
    unittest.main()

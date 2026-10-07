import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fantasy_football_app"))
from app import app
class StartupTests(unittest.TestCase):
    def test_public_pages_render(self):
        with app.test_client() as client:
            for route in ("/", "/login", "/register"):
                with self.subTest(route=route): self.assertEqual(client.get(route).status_code, 200)
    def test_private_pages_require_login(self):
        with app.test_client() as client:
            for route in ("/teams", "/players"):
                self.assertEqual(client.get(route).status_code, 302)

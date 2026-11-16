import os
from pathlib import Path
import runpy
from types import ModuleType
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1] / "geonode_project"


class RegistrationTests(unittest.TestCase):
    def load_settings(self, environment):
        upstream = ModuleType("geonode.settings")
        upstream.SITEURL = "https://geo.example.com/"
        upstream.INSTALLED_APPS = ()
        upstream.STATICFILES_DIRS = []
        upstream.LOCALE_PATHS = ()
        upstream.TEMPLATES = [{"DIRS": [], "OPTIONS": {}}]
        upstream.ACCOUNT_ADAPTER = "geonode.people.adapters.LocalAccountAdapter"
        upstream.INVITATIONS_ADAPTER = upstream.ACCOUNT_ADAPTER
        with patch.dict(os.environ, environment, clear=True):
            with patch.dict("sys.modules", {"geonode.settings": upstream}):
                return runpy.run_path(str(PROJECT_ROOT / "settings.py"))

    def test_existing_environment_without_signup_flags_is_closed(self):
        settings = self.load_settings({})
        self.assertIs(settings["ACCOUNT_OPEN_SIGNUP"], False)
        self.assertIs(settings["ACCOUNT_OPEN_SOCIALSIGNUP"], False)
        self.assertIs(settings["ACCOUNT_APPROVAL_REQUIRED"], True)
        self.assertIs(settings["AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS"], False)
        self.assertEqual(settings["ACCOUNT_ADAPTER"], "geonode.people.adapters.LocalAccountAdapter")
        self.assertEqual(settings["INVITATIONS_ADAPTER"], settings["ACCOUNT_ADAPTER"])

    def test_explicit_environment_configuration_is_respected(self):
        settings = self.load_settings({
            "ACCOUNT_OPEN_SIGNUP": "True",
            "ACCOUNT_OPEN_SOCIALSIGNUP": "True",
            "ACCOUNT_APPROVAL_REQUIRED": "False",
            "AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS": "True",
        })
        self.assertIs(settings["ACCOUNT_OPEN_SIGNUP"], True)
        self.assertIs(settings["ACCOUNT_OPEN_SOCIALSIGNUP"], True)
        self.assertIs(settings["ACCOUNT_APPROVAL_REQUIRED"], False)
        self.assertIs(settings["AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS"], True)

    def test_invalid_configuration_fails_explicitly(self):
        with self.assertRaises((ValueError, SyntaxError)):
            self.load_settings({"ACCOUNT_OPEN_SIGNUP": "not-a-boolean"})


if __name__ == "__main__":
    unittest.main()

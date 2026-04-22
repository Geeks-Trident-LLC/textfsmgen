"""
Unit tests for the `textfsmgen.config` module.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/test_config.py
    or
    $ python -m pytest tests/unit/test_config.py
"""


import pytest   # noqa

from pathlib import Path
from pathlib import PurePath

from textfsmgen import version
import textfsmgen.config as config
from textfsmgen.libs import shell


# Package info for textfsmgen
pkg_info = shell.PackageInfo("textfsmgen")

# Skip marker if textfsmgen is not installed
skip_if_missing_textfsmgen = pytest.mark.skipif(
    not pkg_info.is_installed,
    reason="Skipping: textfsmgen package is not installed."
)


@skip_if_missing_textfsmgen
def test_version_matches_config():
    """Ensure installed package version matches config version."""
    assert pkg_info.is_installed is True
    assert pkg_info.version == config.version


class TestData:
    """Tests for Data class."""

    def test_user_keyword_mapping_file(self):
        """Check template filename path."""
        expected = str(PurePath(Path.home(), '.textfsmgen', 'user_keyword_mapping.yaml'))
        assert config.user_keyword_mapping_file == expected

    def test_main_app_text(self):
        """Check main app text."""
        assert f"v{version}" in config.main_app_text

    def test_company_info(self):
        """Check company info."""
        assert config.company == "Geeks Trident LLC"
        assert "geekstrident.com" in config.company_url

    def test_repo_and_docs_urls(self):
        """Check repo and docs URLs."""
        assert config.repo_url.startswith("https://github.com/")
        assert config.urls.get("readme").endswith("README.md")
        assert config.urls.get("license").endswith("LICENSE")

    def test_license_info(self):
        """Check license info."""
        assert "TextFSM Generator License" in config.license_name
        assert "2022" in config.copyright_text
        assert isinstance(config.license_text, str)

    @pytest.mark.parametrize(
        "pkg",
        [
            "textfsm",
            "pyyaml",
        ],
    )
    def test_get_dependency(self, pkg):
        """Check dependency dict."""
        pkg_name, pkg_url = config.get_dependency().get(pkg).values()
        assert pkg_name.startswith(f"{pkg} v")
        assert pkg_url.rstrip("/").lower() == f"https://pypi.org/project/{pkg}"

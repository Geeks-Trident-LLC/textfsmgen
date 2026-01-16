
import pytest
from textfsmgen import version
import textfsmgen.config as config
from pathlib import Path
from pathlib import PurePath


class TestData:
    """Tests for Data class."""

    def test_user_template_filename(self):
        """Check template filename path."""
        expected = str(PurePath(Path.home(), '.textfsmgen', 'user_templates.yaml'))
        assert config.Data.user_template_filename == expected

    def test_main_app_text(self):
        """Check main app text."""
        assert f"v{version}" in config.Data.main_app_text

    @pytest.mark.parametrize(
        "attr",
        [
            "regexapp",
            "genericlib",
            "textfsm",
            "pyyaml",
        ],
    )
    def test_package_texts(self, attr):
        """Check package text strings."""
        expected = f"{attr} v"
        assert getattr(config.Data, f"{attr}_text").lower().startswith(expected)

    @pytest.mark.parametrize(
        "attr",
        [
            "regexapp",
            "genericlib",
            "textfsm",
            "pyyaml",
        ],
    )
    def test_package_links(self, attr):
        """Check package links."""
        expected = f"https://pypi.org/project/{attr}"
        assert getattr(config.Data, f"{attr}_link").rstrip("/").lower() == expected

    def test_company_info(self):
        """Check company info."""
        assert config.Data.company == "Geeks Trident LLC"
        assert "geekstrident.com" in config.Data.company_url

    def test_repo_and_docs_urls(self):
        """Check repo and docs URLs."""
        assert config.Data.repo_url.startswith("https://github.com/")
        assert config.Data.documentation_url.endswith("README.md")
        assert config.Data.license_url.endswith("LICENSE")

    def test_license_info(self):
        """Check license info."""
        assert "TextFSM Generator License" in config.Data.license_name
        assert "2022" in config.Data.copyright_text
        assert isinstance(config.Data.license, str)

    @pytest.mark.parametrize(
        "pkg",
        [
            "regexapp",
            "genericlib",
            "textfsm",
            "pyyaml",
        ],
    )
    def test_get_dependency(self, pkg):
        """Check dependency dict."""
        pkg_name, pkg_url = config.Data.get_dependency().get(pkg).values()
        assert pkg_name.startswith(f"{pkg} v")
        assert pkg_url.rstrip("/").lower() == f"https://pypi.org/project/{pkg}"

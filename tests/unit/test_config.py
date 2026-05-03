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

import requests     # noqa

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




def test_user_keyword_mapping_file():
    """Check template filename path."""
    expected = str(PurePath(Path.home(), '.textfsmgen', 'user_keyword_mapping.yaml'))
    assert config.user_keyword_mapping_file == expected

def test_main_app_text():
    """Check main app text."""
    assert f"v{version}" in config.main_app_text

def test_company_info():
    """Check company info."""
    assert config.company == "Geeks Trident LLC"
    assert "geekstrident.com" in config.company_url

def test_repo_and_docs_urls():
    """Check repo and docs URLs."""
    assert config.repo_url.startswith("https://github.com/")
    assert config.urls.get("readme").endswith("README.md")
    assert config.urls.get("license").endswith("LICENSE")

def test_license_info():
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
def test_get_dependency(pkg):
    """Check dependency dict."""
    pkg_name, pkg_url = config.get_dependency().get(pkg).values()
    assert pkg_name.startswith(f"{pkg} v")
    assert pkg_url.rstrip("/").lower() == f"https://pypi.org/project/{pkg}"


@pytest.mark.parametrize(
    "page, expected",
    [
        ("how-to-use-regex-builder", ["Regex Builder Tool", "Semantic Overview"]),
        ("how-to-use-textfsm-tester", ["TextFSM Tester Tool", "Interface Overview"]),
        ("how-to-use-snippet-translator", ["Snippet Translator Tool", "Interface Overview"]),
        ("high-level-overview", ["Free‑Form Workflow", "Semi‑Structured Workflow"]),
        ("textfsm-generator-settings-guide", ["General Arguments Settings", "Category Translator Arguments"]),
        ("demo-snippet-translator", ["Demo Snippet Translator", "The current Snippet Translator settings"]),
        ("demo-ios-show-clock", ["Demo IOS show clock",]),
        ("demo-listing-files-in-long-format-on-linux", ["Demo Listing Files in Long Format on Linux",]),
        ("demo-listing-files-on-powershell", ["Demo Listing Files on Powershell"]),
        ("demo-linux-file-status-information", ["Demo Linux File Status Information"]),
        ("faq", ["FAQ"]),
    ]
)
def test_url_page(page, expected):
    url = config.urls.get(page)
    response = requests.get(url, timeout=10)
    assert response.status_code == 200

    html_text = response.text.lower()

    for item in expected:
        assert item.lower() in html_text






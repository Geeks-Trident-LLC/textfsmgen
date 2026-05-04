"""
Unit tests for the `textfsmgen.config` module.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/config/test_urls.py
    or
    $ python -m pytest tests/unit/config/test_urls.py
"""

import pytest       # noqa
import requests     # noqa
from concurrent.futures import ThreadPoolExecutor, as_completed

import textfsmgen.config as config

# Shared session for connection reuse
@pytest.fixture(scope="session")
def http_session():
    session = requests.Session()
    yield session
    session.close()


PAGES = [
    ("how-to-use-regex-builder", ["Regex Builder Tool", "Semantic Overview"]),
    ("how-to-use-textfsm-tester", ["TextFSM Tester Tool", "Interface Overview"]),
    ("how-to-use-regex-suggester", ["Regex Suggester Tool", "Interface Overview"]),
    ("high-level-overview", ["Free‑Form Workflow", "Semi‑Structured Workflow"]),
    ("textfsm-generator-settings-guide", ["General Arguments Settings", "Category Translator Arguments"]),
    ("demo-regex-suggester", ["Demo Regex Suggester", "The current Regex Suggester settings"]),
    ("demo-ios-show-clock", ["Demo IOS show clock"]),
    ("demo-listing-files-in-long-format-on-linux", ["Demo Listing Files in Long Format on Linux"]),
    ("demo-listing-files-on-powershell", ["Demo Listing Files on Powershell"]),
    ("demo-linux-file-status-information", ["Demo Linux File Status Information"]),
    ("faq", ["FAQ"]),
]


def fetch_page(session, url):
    """Fetch a single page, return (url, response_or_exception)."""
    try:
        return url, session.get(url, timeout=10)
    except requests.RequestException as e:
        return url, e


@pytest.fixture(scope="session")
def prefetched_pages(http_session):
    """Fetch all pages in parallel once per session and cache results."""
    urls = {page: config.urls.get(page) for page, _ in PAGES}

    results = {}
    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        futures = {
            executor.submit(fetch_page, http_session, url): page
            for page, url in urls.items()
        }
        for future in as_completed(futures):
            page = futures[future]
            _, result = future.result()
            results[page] = result

    return results


@pytest.mark.parametrize("page, expected", PAGES)
def test_url_page(prefetched_pages, page, expected):
    result = prefetched_pages[page]

    if isinstance(result, Exception):
        pytest.fail(f"Request failed for '{page}': {result}")

    assert result.status_code == 200

    html_text = result.text.lower()
    for item in expected:
        assert item.lower() in html_text

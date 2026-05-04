"""
textfsmgen.config
=================

Configuration utilities for the TextFSM Generator library.
"""

from pathlib import Path
from pathlib import PurePath

import textfsm
import yaml

from textfsmgen.libs.common import dedent_and_strip

__version__ = "0.6.2"
version = __version__

__all__ = [
    "version",
]

# app yaml files
user_keyword_mapping_file = str(
    PurePath(Path.home(), ".textfsmgen", "user_keyword_mapping.yaml")
)


app_version = version

# main app
main_app_text = f"TextFSM Generator v{version}"
software_release = f"TextFSM Generator v{version} - Beta"

# company
company = "Geeks Trident LLC"   # noqa
company_full_name = company
company_name = "Geeks Trident"
company_url = "https://www.geekstrident.com/"

# URL
repo_url = "https://github.com/Geeks-Trident-LLC/textfsmgen"
wiki_url = f"{repo_url}/wiki"

urls = {
    "project-page": repo_url,
    "package-page": "https://pypi.org/project/textfsmgen/",
    "readme": f"{repo_url}/blob/develop/README.md",
    "license": f"{repo_url}/blob/develop/LICENSE",
    "report-issue": f"{repo_url}/issues/new",
    "wiki": wiki_url,

    "video": "https://www.youtube.com/@geekstrident",

    "youtube": "https://www.youtube.com/@geekstrident",

    "contact-support": "https://www.geekstrident.com/contact",
    "submit-feedback": "https://forms.microsoft.com/r/vQ2NHk7tRb",

}
for name in (
    "high-level-overview", "faq", "textfsm-generator-settings-guide",
    "how-to-use-regex-suggester",
    "how-to-use-regex-builder",
    "how-to-use-textfsm-tester",
    "demo-regex-suggester", "demo-ios-show-clock",
    "demo-listing-files-in-long-format-on-linux",
    "demo-listing-files-on-powershell", "demo-linux-file-status-information",
):
    urls[name] = f"{wiki_url}/{name}"


# License
years = "2022"
license_name = "TextFSM Generator License"
copyright_text = f"Copyright \xa9 {years}"

license_text = dedent_and_strip(
    """
    BSD 3-Clause License

    Copyright (c) 2021-2040, Geeks Trident LLC
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
       list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
       contributors may be used to endorse or promote products derived from
       this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

    """
)


def get_dependency():
    """Return dependency metadata for the application."""
    dependencies = dict(
        textfsm=dict(
            package=f"textfsm v{textfsm.__version__}",
            url="https://pypi.org/project/textfsm/"
        ),
        pyyaml=dict(
            package=f"pyyaml v{yaml.__version__}",
            url="https://pypi.org/project/PyYAML/"
        )
    )
    return dependencies


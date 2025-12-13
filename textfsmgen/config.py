"""This module defines and organizes the essential core attributes powering
functionality, structure, and extensibility of the TextFSM Generator library."""

from os import path

from pathlib import Path
from pathlib import PurePath

import regexapp
import textfsm
import yaml

from genericlib import version as gtlib_version

__version__ = '0.2.1a1'
version = __version__
__edition__ = 'Community'
edition = __edition__

__all__ = [
    'version',
    'edition',
    'Data'
]


class Data:
    # app yaml files
    user_template_filename = str(
        PurePath(
            Path.home(),
            '.geekstrident',
            'textfsmgen',
            'user_templates.yaml')
    )

    app_version = version

    # main app
    main_app_text = 'TextFSM Generator v{}'.format(version)

    # packages
    gtregexapp_text = 'regexapp v{}'.format(regexapp.version)
    gtregexapp_link = 'https://pypi.org/project/regexapp'

    gtgenlib_text = f"genericlib v{gtlib_version}"
    gtgenlib_link = "https://pypi.org/project/genericlib"

    textfsm_text = 'textfsm v{}'.format(textfsm.__version__)
    textfsm_link = 'https://pypi.org/project/textfsm/'

    pyyaml_text = 'pyyaml v{}'.format(yaml.__version__)
    pyyaml_link = 'https://pypi.org/project/PyYAML/'

    # company
    company = 'Geeks Trident LLC'
    company_full_name = company
    company_name = "Geeks Trident"
    company_url = 'https://www.geekstrident.com/'

    # URL
    repo_url = 'https://github.com/Geeks-Trident-LLC/textfsmgen'
    documentation_url = path.join(repo_url, 'blob/develop/README.md')
    license_url = path.join(repo_url, 'blob/develop/LICENSE')

    # License
    years = '2022'
    license_name = f'{company_name} License'
    copyright_text = f'Copyright \xa9 {years}'

    with open("LICENSE", encoding="utf-8") as f:
        license = f.read()

    @classmethod
    def get_dependency(cls):
        dependencies = dict(
            gtregexapp=dict(
                package=cls.gtregexapp_text,
                url=cls.gtregexapp_link
            ),
            gtgenlib=dict(
                package=cls.gtgenlib_text,
                url=cls.gtgenlib_link
            ),
            textfsm=dict(
                package=cls.textfsm_text,
                url=cls.textfsm_link
            ),
            pyyaml=dict(
                package=cls.pyyaml_text,
                url=cls.pyyaml_link
            )
        )
        return dependencies

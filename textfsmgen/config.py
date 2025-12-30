"""
textfsmgen.config
=================

Configuration utilities for the TextFSM Generator library.

This module centralizes application‑wide configuration values, constants,
and helper functions that control the behavior of the TextFSM Generator.
It provides a single source of truth for default settings, file paths,
naming conventions, and runtime options used across both the core logic
and GUI components.

Notes
-----
- Configuration values defined here are intended to be application‑wide
  and should not be duplicated in other modules.
- This module supports both GUI and CLI workflows by providing consistent
  defaults.
"""

from os import path

from pathlib import Path
from pathlib import PurePath

import regexapp
import textfsm
import yaml

from genericlib import version as genericlib_version
import genericlib.file as file

__version__ = '0.2.1a2'
version = __version__
__edition__ = 'Community'
edition = __edition__

__all__ = [
    'version',
    'edition',
    'Data'
]


class Data:
    """
    Centralized metadata and configuration for the TextFSM Generator application.

    This class provides static attributes and helper methods that define
    application metadata, dependency information, company details, and
    repository links. It serves as a single source of truth for versioning,
    licensing, and package references used throughout the application.
    """

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
    regexapp_text = 'regexapp v{}'.format(regexapp.version)
    regexapp_link = 'https://pypi.org/project/regexapp'

    genlib_text = f"genericlib v{genericlib_version}"
    genlib_link = "https://pypi.org/project/genericlib"

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

    license = file.read("LICENSE")

    @classmethod
    def get_dependency(cls):
        """
        Return dependency metadata for the application.

        Returns
        -------
        dict
            A dictionary mapping dependency names to their metadata,
            including package display strings and PyPI URLs.
        """
        dependencies = dict(
            regexapp=dict(
                package=cls.regexapp_text,
                url=cls.regexapp_link
            ),
            genlib=dict(
                package=cls.genlib_text,
                url=cls.genlib_link
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

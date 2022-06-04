"""Module containing the attributes for templatepro."""

from os import path
from textwrap import dedent

from pathlib import Path
from pathlib import PurePath

import regexpro
import dlpro
import textfsm
import yaml

__version__ = '0.1.9'
version = __version__
__edition__ = 'Pro'
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
            'templatepro',
            'user_templates.yaml')
    )

    # main app
    main_app_text = 'Template Pro {}'.format(version)

    # packages
    regexpro_text = 'regexpro v{}'.format(regexpro.version)
    regexpro_link = 'https://pypi.org/project/regexpro/'

    dlpro_text = 'dlpro v{}'.format(dlpro.version)
    dlpro_link = 'https://pypi.org/project/dlpro/'

    textfsm_text = 'textfsm v{}'.format(textfsm.__version__)
    textfsm_link = 'https://pypi.org/project/textfsm/'

    pyyaml_text = 'pyyaml v{}'.format(yaml.__version__)
    pyyaml_link = 'https://pypi.org/project/PyYAML/'

    # company
    company = 'Geeks Trident LLC'
    company_url = 'https://www.geekstrident.com/'

    # URL
    repo_url = 'https://github.com/Geeks-Trident-LLC/templatepro'
    # TODO: Need to update wiki page for documentation_url instead of README.md.
    documentation_url = path.join(repo_url, 'blob/develop/README.md')
    license_url = path.join(repo_url, 'blob/develop/LICENSE')

    # License
    years = '2022-2080'
    license_name = 'Geeks Trident License'
    copyright_text = 'Copyright @ {}'.format(years)
    license = dedent(
        """
        Geeks Trident License

        Copyright (c) {}, {}
        All rights reserved.

        Unauthorized copying of file, source, and binary forms without 
        Geeks Trident permissions, via any medium is strictly prohibited.

        Proprietary and confidential.

        Written by Tuyen Mathew Duong <tuyen@geekstrident.com>, Jan 14, 2022.
        """.format(years, company)
    ).strip()

    @classmethod
    def get_dependency(cls):
        dependencies = dict(
            regexpro=dict(
                package=cls.regexpro_text,
                url=cls.regexpro_link
            ),
            dlpro=dict(
                package=cls.dlpro_text,
                url=cls.dlpro_link
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

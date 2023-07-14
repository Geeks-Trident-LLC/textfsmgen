"""Module containing the attributes for templatepro."""

from os import path
from textwrap import dedent

from pathlib import Path
from pathlib import PurePath

import regexpro
import dlpro
import textfsm
import yaml

from genericlib import version as gtlib_version
# from genericlib import File

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
    main_app_text = 'TemplateApp v{}'.format(version)

    # packages
    gtregexpro_text = 'regexapp v{}'.format(regexpro.version)
    gtregexpro_link = ''

    gtgenlib_text = f"genericlib v{gtlib_version}"
    gtgenlib_link = ""

    gtdlpro_text = 'dlapp v{}'.format(dlpro.version)
    gtdlpro_link = ''

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
    repo_url = 'https://github.com/Geeks-Trident-LLC/templatepro'
    # TODO: Need to update wiki page for documentation_url instead of README.md.
    documentation_url = path.join(repo_url, 'blob/develop/README.md')
    license_url = path.join(repo_url, 'blob/develop/LICENSE')

    # License
    years = '2022'
    license_name = f'{company_name} License'
    copyright_text = f'Copyright \xa9 {years}'
    license = dedent(
        f"""
        {company_name} License

        {copyright_text} {company}.  All rights reserved.

        Unauthorized copying of file, source, and binary forms without {company_name} permissions, via any medium is strictly prohibited.

        Proprietary and confidential.

        Written by Tuyen Mathew Duong <tuyen@geekstrident.com>, Jan 14, 2022.
        """).strip()    # noqa

    @classmethod
    def get_dependency(cls):
        dependencies = dict(
            gtregexapp=dict(
                package=cls.gtregexpro_text,
                url=""
            ),
            gtdlapp=dict(
                package=cls.gtdlpro_text,
                url=""
            ),
            gtgenlib=dict(
                package=cls.gtgenlib_text,
                url=""
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

"""
setup.py configuration for packaging and distributing the TextFSM Generator
library. Defines metadata, dependencies, and build instructions to ensure
consistent installation across supported Python environments.
"""

from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='textfsmgen',
    version='0.6.2',
    license='BSD-3-Clause',
    license_files=['LICENSE'],
    description='TextFSM Generator is a low‑code, no‑code Python library that '
                'transforms simple, readable snippets into TextFSM templates, '
                'reducing manual effort and accelerating automation development.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tuyen Mathew Duong',
    author_email='tuyen@geekstrident.com',
    maintainer='Tuyen Mathew Duong',
    maintainer_email='tuyen@geekstrident.com',

    install_requires=[
        "textfsm>=1.1.0",
        "pyyaml>=6.0",
    ],
    url='https://github.com/Geeks-Trident-LLC/textfsmgen',
    packages=find_packages(
        exclude=(
            'tests*', 'testing*', 'examples*',
            'build*', 'dist*', 'docs*', 'venv*'
        )
    ),
    project_urls={
        "Documentation": "https://github.com/Geeks-Trident-LLC/textfsmgen/wiki",
        "Source": "https://github.com/Geeks-Trident-LLC/textfsmgen",
        "Tracker": "https://github.com/Geeks-Trident-LLC/textfsmgen/issues",
    },
    python_requires=">=3.9",
    include_package_data=True,
    package_data={"": ["LICENSE", "README.md"]},
    entry_points={
        'console_scripts': [
            'textfsmgen = textfsmgen.main:execute',
            'textfsmgen-gui = textfsmgen.application:execute',
            'textfsmgen-app = textfsmgen.application:execute',
            'textfsm-app = textfsmgen.application:execute',
        ]
    },
    classifiers=[
        # development status
        "Development Status :: 4 - Beta",
        # natural language
        "Natural Language :: English",
        # intended audience
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Other Audience",
        "Intended Audience :: Science/Research",
        # operating system
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        # programming language
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        # topic
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing",
    ],
    keywords="low-code, no-code, citizen developer, "
             "automation, workflow automation, process automation,"
             "textfsm, textfsm generator, text parsing, "
             "verification, validation, qa, test automation, "
             "robotframework, test script, "
             "ai integration, ai-assisted automation, generative ai",
)

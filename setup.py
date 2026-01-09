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
    version='0.3.0a1',
    license='BSD-3-Clause',
    license_files=['LICENSE'],
    description='TextFSM Generator simplifies template creation by converting '
                'plain English snippets into reusable parsing rules, '
                'standardizing workflows and enhancing collaboration across teams.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tuyen Mathew Duong',
    author_email='tuyen@geekstrident.com',
    maintainer='Tuyen Mathew Duong',
    maintainer_email='tuyen@geekstrident.com',
    install_requires=[
        "textfsm>=1.1.0",
        "pyyaml>=6.0",
        "genericlib",
        "regexapp",
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
        ]
    },
    classifiers=[
        # development status
        "Development Status :: 3 - Alpha",
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
        # topic
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing",
    ],
    keywords="textfsm, textfsm generator, text parsing, automation, "
             "verification, validation, qa, robotframework, test script, "
             "test case, test plan, ai integration",
)

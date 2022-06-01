#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    raise ValueError("Requires Python 3.6 or superior")

from ees_microsoft_outlook import __version__  # NOQA

install_requires = [
    "cached_property==1.5.2; python_version < '3.8'",
    "cerberus",
    "ecs_logging",
    "elastic_enterprise_search",
    "flake8",
    "pytest",
    "pytest-cov",
    "pyyaml",
    "tika",
    "beautifulsoup4",
    "iteration_utilities",
    "ldap3",
    "exchangelib",
    "requests",
    "pytz"
]

description = ""

with open("README.rst", encoding="utf-8") as readme_file:
    description += readme_file.read() + "\n\n"


classifiers = [
    "Programming Language :: Python",
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
]


setup(
    name="Microsoft Outlook",
    version=__version__,
    url="https://example.com",
    packages=find_packages(),
    long_description=description.strip(),
    description=("This is a python project for a Enterprise Search Outlook Connector."),
    author="author",
    author_email="email",
    include_package_data=True,
    zip_safe=False,
    classifiers=classifiers,
    install_requires=install_requires,
    data_files=[("config", ["microsoft_outlook_connector.yml"])],
    entry_points="""
      [console_scripts]
      ees_microsoft_outlook = ees_microsoft_outlook.cli:main
      """,
)

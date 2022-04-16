#!/usr/bin/env python

"""The setup script"""

from setuptools import find_packages, setup

with open("requirements.txt") as f:
    INSTALL_REQUIRES = f.read().strip().split("\n")

with open("README.md") as f:
    LONG_DESCRIPTION = f.read()

PYTHON_REQUIRES = ">=3.7"

description = "analysis of the California forest carbon offsets protocol buffer pool"

setup(
    name="carbonplan_buffer_analysis",
    description=description,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    maintainer="Grayson Badgley",
    maintainer_email="grayson@carbonplan.org",
    url="https://github.com/carbonplan/carbonplan-buffer-integrity",
    packages=find_packages(),
    include_package_data=True,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    tests_require=["pytest"],
    license="MIT",
    keywords="carbon, data, forest offsets",
    use_scm_version={"version_scheme": "post-release", "local_scheme": "dirty-tag"},
    setup_requires=["setuptools_scm", "setuptools>=30.3.0"],
)

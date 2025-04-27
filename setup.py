#!/usr/bin/env python
"""
Setup script for Schwab API client
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
README = ""
if os.path.exists('README.md'):
    with open('README.md', 'r', encoding='utf-8') as f:
        README = f.read()

# Package requirements
REQUIREMENTS = [
    'requests>=2.25.0',
    'cryptography>=3.3.1',
    'pywin32>=300;platform_system=="Windows"',
]

setup(
    name="schwab_api",
    version="0.1.0",
    description="Modular Schwab API client with OAuth authentication",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/schwab_api",
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.7",
    entry_points={
        'console_scripts': [
            'schwab-oauth-demo=examples.oauth_demo:main',
        ],
    },
)
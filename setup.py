#!/usr/bin/env python3
"""
Setup script for Transcriber v2.0
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open('requirements.txt') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            # Remove version constraints for basic install
            package = line.split('>=')[0].split('==')[0]
            requirements.append(package)

setup(
    name="transcriber-v2",
    version="2.1.0-dev",
    author="Transcriber Team",
    author_email="contact@transcriber.dev",
    description="Modular transcription pipeline with AI enhancements",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/transcriber/transcriber-v2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Content Creators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0"],
        "docs": ["mkdocs>=1.5.0", "mkdocs-material>=9.0.0"],
        "audio": ["librosa>=0.10.0"],
    },
    entry_points={
        "console_scripts": [
            "transcriber-v2=run_transcription_pipeline_v2:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yaml", "*.yml"],
    },
)

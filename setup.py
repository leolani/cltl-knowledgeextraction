#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_namespace_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("VERSION", "r", encoding="utf-8") as fh:
    version = fh.read().strip()

setup(
    name="cltl.triple_extraction",
    description="The Leolani Language module for knowledge extraction",
    version=version,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leolani/cltl-knowledgeextraction",
    license='MIT License',
    authors={
        "Bajc̆etic": ("Lenka Bajc̆etic", "l.bajccetic@vu.nl"),
        "Baez Santamaria": ("Selene Baez Santamaria", "s.baezsantamaria@vu.nl"),
        "Baier": ("Thomas Baier", "t.baier@vu.nl")
    },
    package_dir={'': 'src'},
    packages=find_namespace_packages(include=['cltl.*'], where='src'),
    package_data={'cltl.triple_extraction': [
        'stanford-ner/*',
        'stanford-ner/**/*',
        'stanford-pos/*',
        'stanford-pos/**/*',
        'data/*',
        'data/**/*'
    ]},
    python_requires='>=3.7',
    install_requires=[
        'nltk~=3.4.4',
        'stanford_openie~=1.3.0',
        'spacy==3.2.3'
    ],
    setup_requires=['flake8']
)

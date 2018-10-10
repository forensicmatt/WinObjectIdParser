from setuptools import setup

setup(
    name='winobjid',
    version="0.0.2",
    description='Windows Tools and Lib for parsing Object IDs to JSONL.',
    author='Matthew Seyer',
    url='https://github.com/forensicmatt/WinObjectIdParser',
    license='Apache License (2.0)',
    packages=[
        'winobjid'
    ],
    python_requires='>=3',
    install_requires=[
        'pytsk3'
    ],
    scripts=[
        'scripts/objid_indx_parser.py'
    ]
)

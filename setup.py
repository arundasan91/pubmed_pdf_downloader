# File: setup.py
from setuptools import setup, find_packages

setup(
    name='pubmed_pdf_downloader',
    version='0.1.1',
    description='A package to download PDFs from PubMed Central using PMCIDs.',
    author='Arun Das',
    author_email='ard212@pitt.edu',
    url='https://github.com/arundasan91/pubmed_pdf_downloader',
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4'
    ],
    entry_points={
        'console_scripts': [
            'pubmed-pdf-downloader = pubmed_pdf_downloader.downloader:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
	'License :: OSI Approved :: Apache Software License',
	'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

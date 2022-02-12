import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'lamarkdown',
    version = '0.1',
    description = 'A command-line tool for compiling a markdown document into a complete, static HTML page, using Python Markdown.',
    author = 'David J A Cooper',
    author_email = 'david.cooper@curtin.edu.au',
    long_description = read('README.md'),
    license = 'MIT',
    keywords = 'markdown',
    url = 'https://bitbucket.org/cooperdja/lamarkdown',
    install_requires=[
        'markdown', 'lxml', 'cssselect', 'pymdown-extensions', 'watchdog'
    ],
    packages = [
        'lamarkdown', 'lamarkdown.lib', 'lamarkdown.ext'
    ],
    entry_points = {
        'console_scripts': ['lamd=lamarkdown.lib.lamd:main'],
        'markdown.extensions': [
            'lamarkdown.eval = lamarkdown.ext.eval:EvalExtension',
            'lamarkdown.latex = lamarkdown.ext.latex:LatexExtension',
            'lamarkdown.markers = lamarkdown.ext.markers:MarkersExtension',
            'lamarkdown.pruner = lamarkdown.ext.pruner:PrunerExtension',
            'lamarkdown.sections = lamarkdown.ext.sections:SectionsExtension',
        ]
    },
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Documentation',
        'Topic :: Text Processing :: Markup :: Markdown',
    ]
)

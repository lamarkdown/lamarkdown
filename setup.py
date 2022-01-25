import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'lamarkdown',
    version = '0.1',
    author = 'David J A Cooper',
    author_email = 'david.cooper@curtin.edu.au',
    description = ('A command-line tool for compiling a markdown document into a complete, static HTML page, using Python Markdown.'),
    long_description = read('README.md'),
    license = 'BSD',
    keywords = 'markdown',
    url = 'https://bitbucket.org/cooperdja/lamarkdown',
    install_requires=[
        'markdown', 'pymdown-extensions', 'watchdog'
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
)

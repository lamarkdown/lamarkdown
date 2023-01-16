import unittest

import markdown
from lamarkdown.ext import sections

import re
from textwrap import dedent


class PybtexTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text, **kwargs):
        md = markdown.Markdown(
            extensions = ['lamarkdown.ext.pybtex'],
            extension_configs = {'lamarkdown.ext.pybtex':
            {
                **kwargs
            }}
        )
        return md.convert(dedent(markdown_text).strip())


    def test_single_citation(self):
        '''Check some sections!'''

        html = self.run_markdown(
            r'''
            # Heading

            Citation A [@refB], citation B [@refC].
            
            Citation C [@refD], citation A [@refB].
            ''',
            file = [],
            references = r'''
                @article{refA,
                    author = "The Author A",
                    title = "The Title A",
                    journal = "The Journal A",
                    year = "1990"
                }
                @article{refB,
                    author = "The Author B",
                    title = "The Title B",
                    journal = "The Journal B",
                    year = "1991"
                }
                @article{refC,
                    author = "The Author C",
                    title = "The Title C",
                    journal = "The Journal C",
                    year = "1992"
                }
                @article{refD,
                    author = "The Author D",
                    title = "The Title D",
                    journal = "The Journal D",
                    year = "1993"
                }
                @article{refE,
                    author = "The Author E",
                    title = "The Title E",
                    journal = "The Journal E",
                    year = "1994"
                }
            ''')
            
        self.assertRegex(
            html,
            fr'''(?sx)
            \s* <h1>Heading</h1>
            \s* <p>Citation[ ]A[ ]<cite[ ]id="pybtexcite:1-1">\[<a[ ]href="\#pybtexref:1">1</a>\]</cite>,[ ]
                   citation[ ]B[ ]<cite[ ]id="pybtexcite:2-1">\[<a[ ]href="\#pybtexref:2">2</a>\]</cite>.</p>
            \s* <p>Citation[ ]C[ ]<cite[ ]id="pybtexcite:3-1">\[<a[ ]href="\#pybtexref:3">3</a>\]</cite>,[ ]
                   citation[ ]A[ ]<cite[ ]id="pybtexcite:1-2">\[<a[ ]href="\#pybtexref:1">1</a>\]</cite>.</p>
            \s* <dl> \s* <dt[ ]id="pybtexref:1">1</dt> \s* <dd> .* </dl>
            \s*
            '''
        )
        
        # TODO: the actual reference list comes after, so the above will fail at first.

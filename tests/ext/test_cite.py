from ..util.mock_progress import MockProgress
import unittest

import lamarkdown.ext
import markdown

import re
import sys
import tempfile
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']

class CiteTestCase(unittest.TestCase):
    REFERENCES = r'''
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
    '''

    def run_markdown(self, markdown_text, more_extensions=[], **kwargs):
        md = markdown.Markdown(
            extensions = ['la.cite', *more_extensions],
            extension_configs = {'la.cite': {
                'progress': MockProgress(),
                **kwargs
            }}
        )
        return md.convert(dedent(markdown_text).strip())


    def test_unused(self):
        html = self.run_markdown(
            r'''
            # Heading
            '''
        )

        self.assertRegex(
            html,
            r'''(?sx)
            \s* <h1>Heading</h1>
            '''
        )


    def test_not_mangling_other_things(self):
        # Check standard link and image syntax to make sure it still works. The Pymtex extension
        # should avoid matching:
        # [user@refA.com]             - '@' must come after a non-word character.
        # [@refA](http://example.com) - [...] must not be followed by '('.
        # [@refA][1]                  - [...] must not be followed by '['.
        # ![@refA](image.jpg)         - [...] must not be preceeded by '!' (or followed by '(').
        #
        # It _should_ match [@refE]. That's there to ensure the extension is actually running.

        html = self.run_markdown(
            r'''
            [user@refA.com]
            [@refA](http://example.com)
            [@refA][1]
            ![@refA](image.jpg)
            [@refE]
            [1]: http://example.com
            ''',
            file = [],
            references = self.REFERENCES)

        self.assertRegex(
            html,
            r'''(?sx)
            \s* <p>\[user@refA\.com]
            \s* <a[ ]href="http://example.com">@refA</a>
            \s* <a[ ]href="http://example.com">@refA</a>
            \s* <img[ ]alt="@refA"[ ]src="image\.jpg"\s*/?>
            \s* <cite>.*</cite>
            \s* </p>
            .*
            ''')


    def test_non_matching_citations(self):

        # Here, @refX doesn't match anything in the reference database, and we want to retain the
        # literal text instead.
        html = self.run_markdown(
            r'''
            # Heading

            Citation B [@refB], citation X [@refX].
            ''',
            file = [],
            references = self.REFERENCES,
            hyperlinks = 'none')

        self.assertRegex(
            html,
            r'''(?sx)
            \s* <h1>Heading</h1>
            \s* <p>Citation[ ]B[ ]<cite>\[<span[ ]id="la-cite:1-1">1</span>]</cite>,[ ]citation[ ]X[ ]\[@refX].</p>
            \s* <dl[ ]id="la-bibliography">
            \s* <dt[ ]id="la-ref:1">1</dt> \s* <dd> .* \. </dd>
            \s* </dl>
            \s*
            '''
        )


    def test_links(self):
        linked_citations = r'''
            \s* <p>Citation[ ]B[ ]<cite>\[<a[ ]href="\#la-ref:1"[ ]id="la-cite:1-1">1</a>,[ ]p\.[ ]5\]</cite>,[ ]
                   citation[ ]C[ ]<cite>\[<a[ ]href="\#la-ref:2"[ ]id="la-cite:2-1">2</a>\]</cite>.</p>
            \s* <p>Citation[ ]D[ ]<cite>\[<a[ ]href="\#la-ref:3"[ ]id="la-cite:3-1">3</a>[ ]maybe\]</cite>,[ ]
                   citation[ ]B[ ]<cite>\[<a[ ]href="\#la-ref:1"[ ]id="la-cite:1-2">1</a>\]</cite>.</p>
        '''

        unlinked_citations = r'''
            \s* <p>Citation[ ]B[ ]<cite>\[<span[ ]id="la-cite:1-1">1</span>,[ ]p\.[ ]5\]</cite>,[ ]
                   citation[ ]C[ ]<cite>\[<span[ ]id="la-cite:2-1">2</span>\]</cite>.</p>
            \s* <p>Citation[ ]D[ ]<cite>\[<span[ ]id="la-cite:3-1">3</span>[ ]maybe\]</cite>,[ ]
                   citation[ ]B[ ]<cite>\[<span[ ]id="la-cite:1-2">1</span>\]</cite>.</p>
        '''

        linked_refs = r'''
            \s* <dt[ ]id="la-ref:1">1</dt> \s* <dd> .* [ ]<span>↩[ ]<a[ ]href="\#la-cite:1-1">1</a>
                                                                    [ ]<a[ ]href="\#la-cite:1-2">2</a></span></dd>
            \s* <dt[ ]id="la-ref:2">2</dt> \s* <dd> .* [ ]<a[ ]href="\#la-cite:2-1">↩</a></dd>
            \s* <dt[ ]id="la-ref:3">3</dt> \s* <dd> .* [ ]<a[ ]href="\#la-cite:3-1">↩</a></dd>
        '''

        unlinked_refs = r'''
            \s* <dt[ ]id="la-ref:1">1</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:2">2</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:3">3</dt> \s* <dd> .* \. </dd>
        '''

        data = [('both',    linked_citations,   linked_refs),
                ('forward', linked_citations,   unlinked_refs),
                ('back',    unlinked_citations, linked_refs),
                ('none',    unlinked_citations, unlinked_refs)]

        for hyperlinks, cite_regex, ref_regex in data:
            html = self.run_markdown(
                r'''
                # Heading

                Citation B [@refB, p. 5], citation C [@refC].

                Citation D [@refD maybe], citation B [@refB].
                ''',
                file = [],
                references = self.REFERENCES,
                hyperlinks = hyperlinks)

            self.assertRegex(
                html,
                fr'''(?sx)
                \s* <h1>Heading</h1>
                {cite_regex}
                \s* <dl[ ]id="la-bibliography">
                {ref_regex}
                \s* </dl>
                \s*
                '''
            )


    def test_placeholder(self):
        src_place_marker = r'///References Go Here///'
        src_citation_b = r'Citation B [@refB].'
        src_citation_c = r'Citation C [@refC].'

        regex_references = r'''
            \s* <dl[ ]id="la-bibliography">
            \s* <dt[ ]id="la-ref:1">1</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:2">2</dt> \s* <dd> .* \. </dd>
            \s* </dl>
        '''

        regex_citation_b = r'\s* <p>Citation[ ]B[ ]<cite>\[<span[ ]id="la-cite:1-1">1</span>]</cite>.</p>'
        regex_citation_c = r'\s* <p>Citation[ ]C[ ]<cite>\[<span[ ]id="la-cite:2-1">2</span>]</cite>.</p>'

        # We're testing different placements of the 'place marker, which determines
        data = [
            (
                # Marker at start
                src_place_marker + '\n\n' + src_citation_b + '\n\n' + src_citation_c,
                fr'''(?sx)
                    {regex_references}
                    {regex_citation_b}
                    {regex_citation_c}
                    \s*
                '''
            ),
            (
                # Marker in the middle
                src_citation_b + '\n\n' + src_place_marker + '\n\n' + src_citation_c,
                fr'''(?sx)
                    {regex_citation_b}
                    {regex_references}
                    {regex_citation_c}
                    \s*
                '''
            ),
            (
                # Marker at end
                src_citation_b + '\n\n' + src_citation_c + '\n\n' + src_place_marker,
                fr'''(?sx)
                    {regex_citation_b}
                    {regex_citation_c}
                    {regex_references}
                    \s*
                '''
            ),
            (
                # Marker missing -- should be the same as if it was at the end.
                src_citation_b + '\n\n' + src_citation_c,
                fr'''(?sx)
                    {regex_citation_b}
                    {regex_citation_c}
                    {regex_references}
                    \s*
                '''
            )
        ]

        for markdown, regex in data:
            html = self.run_markdown(
                markdown,
                file = [],
                references = self.REFERENCES,
                hyperlinks = 'none')

            self.assertRegex(html, regex)


    def test_multipart_citations(self):
        html = self.run_markdown(
            r'''
            Citation B [see @refB, p. 5; @refC maybe; not @refX].
            ''',
            file = [],
            references = self.REFERENCES,
            hyperlinks = 'none')

        self.assertRegex(
            html,
            r'''(?sx)
            \s* <p>Citation[ ]B[ ]<cite>\[see[ ]
                <span[ ]id="la-cite:1-1">1</span>,[ ]p\.[ ]5;[ ]
                <span[ ]id="la-cite:2-1">2</span>[ ]maybe;[ ]not[ ]@refX\]</cite>.</p>
            \s* <dl[ ]id="la-bibliography">
            \s* <dt[ ]id="la-ref:1">1</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:2">2</dt> \s* <dd> .* \. </dd>
            \s* </dl>
            \s*
            ''')


    def test_citation_key_syntax(self):
        html = self.run_markdown(
            fr'''
            # Heading
            [see @1:a.2b$3c&4+d?5<e>6~f/7-g; @{{![]!}}; @{{;;;}}]
            ''',
            file = [],
            references = r'''
                @article{refA,
                    author = "The Author A",
                    title = "The Title A",
                    journal = "The Journal A",
                    year = "1990"
                }
                @article{1:a.2b$3c&4+d?5<e>6~f/7-g,
                    author = "The Author B",
                    title = "The Title B",
                    journal = "The Journal B",
                    year = "1991"
                }
                @article{![]!,
                    author = "The Author C",
                    title = "The Title C",
                    journal = "The Journal C",
                    year = "1992"
                }
                @article{;;;,
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
            ''',
            hyperlinks = 'none')

        self.assertRegex(
            html,
            r'''(?sx)
            \s* <h1>Heading</h1>
            \s* <p><cite>\[see[ ]<span[ ]id="la-cite:1-1">1</span>;[ ]
                                 <span[ ]id="la-cite:2-1">2</span>;[ ]
                                 <span[ ]id="la-cite:3-1">3</span>]</cite></p>
            \s* <dl[ ]id="la-bibliography">
            \s* <dt[ ]id="la-ref:1">1</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:2">2</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:3">3</dt> \s* <dd> .* \. </dd>
            \s* </dl>
            \s*
            ''')


    def test_reference_sources(self):
        with tempfile.TemporaryDirectory() as dir:

            # Create four different reference database files:
            for r in ['A', 'B', 'C', 'D']:
                with open(f'{dir}/references{r}.bib', 'w') as ref_file:
                    ref_file.write(fr'''
                        @article{{ref{r},
                            author = "The Author {r}",
                            title = "The Title {r}",
                            journal = "The Journal {r}",
                            year = "1990"
                        }}
                    ''')

            html = self.run_markdown(
                fr'''
                bibliography: {dir}/referencesA.bib
                              {dir}/referencesB.bib

                [@refA]
                [@refB]
                [@refC]
                [@refD]
                [@refE]
                ''',
                more_extensions = ['meta'],
                file = [f'{dir}/referencesC.bib', f'{dir}/referencesD.bib'],
                references = r'''
                    @article{refE,
                        author = "The Author E",
                        title = "The Title E",
                        journal = "The Journal E",
                        year = "1994"
                    }
                ''',
                hyperlinks = 'none')


    def test_nocite(self):
        html = self.run_markdown(
            fr'''
            nocite: @*

            # Heading
            ''',
            more_extensions = ['meta'],
            file = [],
            references = self.REFERENCES)

        self.assertRegex(
            html,
            r'''(?sx)
            \s* <h1>Heading</h1>
            \s* <dl[ ]id="la-bibliography">
            \s* <dt[ ]id="la-ref:1">1</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:2">2</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:3">3</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:4">4</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:5">5</dt> \s* <dd> .* \. </dd>
            \s* </dl>
            \s*
            ''')

        html = self.run_markdown(
            fr'''
            nocite: @refB, @refC
                    @refD

            # Heading
            ''',
            more_extensions = ['meta'],
            file = [],
            references = self.REFERENCES)

        self.assertRegex(
            html,
            r'''(?sx)
            \s* <h1>Heading</h1>
            \s* <dl[ ]id="la-bibliography">
            \s* <dt[ ]id="la-ref:1">1</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:2">2</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="la-ref:3">3</dt> \s* <dd> .* \. </dd>
            \s* </dl>
            \s*
            ''')


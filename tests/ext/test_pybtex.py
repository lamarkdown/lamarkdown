import unittest

import markdown
from lamarkdown.ext import sections

import re
from textwrap import dedent


class PybtexTestCase(unittest.TestCase):
    
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

    def run_markdown(self, markdown_text, **kwargs):
        md = markdown.Markdown(
            extensions = ['lamarkdown.ext.pybtex'],
            extension_configs = {'lamarkdown.ext.pybtex':
            {
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
            fr'''(?sx)
            \s* <h1>Heading</h1>
            '''
        )
        
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
            fr'''(?sx)
            \s* <h1>Heading</h1>
            \s* <p>Citation[ ]B[ ]<cite[ ]id="pybtexcite:1-1">\[1]</cite>,[ ]citation[ ]X[ ]\[@refX].</p>
            \s* <dl> 
            \s* <dt[ ]id="pybtexref:1">1</dt> \s* <dd> .* \. </dd>
            \s* </dl>
            \s*
            '''
        )
        

    def test_links(self):
        linked_citations = r'''
            \s* <p>Citation[ ]B[ ]<cite[ ]id="pybtexcite:1-1">\[<a[ ]href="\#pybtexref:1">1,[ ]p\.[ ]5</a>\]</cite>,[ ]
                   citation[ ]C[ ]<cite[ ]id="pybtexcite:2-1">\[<a[ ]href="\#pybtexref:2">2</a>\]</cite>.</p>
            \s* <p>Citation[ ]D[ ]<cite[ ]id="pybtexcite:3-1">\[<a[ ]href="\#pybtexref:3">3[ ]maybe</a>\]</cite>,[ ]
                   citation[ ]B[ ]<cite[ ]id="pybtexcite:1-2">\[<a[ ]href="\#pybtexref:1">1</a>\]</cite>.</p>
        '''
        
        unlinked_citations = r'''
            \s* <p>Citation[ ]B[ ]<cite[ ]id="pybtexcite:1-1">\[1,[ ]p\.[ ]5\]</cite>,[ ]
                   citation[ ]C[ ]<cite[ ]id="pybtexcite:2-1">\[2\]</cite>.</p>
            \s* <p>Citation[ ]D[ ]<cite[ ]id="pybtexcite:3-1">\[3[ ]maybe\]</cite>,[ ]
                   citation[ ]B[ ]<cite[ ]id="pybtexcite:1-2">\[1\]</cite>.</p>
        '''
        
        linked_refs = r'''
            \s* <dt[ ]id="pybtexref:1">1</dt> \s* <dd> .* [ ]<span>↩[ ]<a[ ]href="\#pybtexcite:1-1">1</a>
                                                                    [ ]<a[ ]href="\#pybtexcite:1-2">2</a></span></dd>
            \s* <dt[ ]id="pybtexref:2">2</dt> \s* <dd> .* [ ]<a[ ]href="\#pybtexcite:2-1">↩</a></dd>
            \s* <dt[ ]id="pybtexref:3">3</dt> \s* <dd> .* [ ]<a[ ]href="\#pybtexcite:3-1">↩</a></dd>
        '''

        unlinked_refs = r'''
            \s* <dt[ ]id="pybtexref:1">1</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="pybtexref:2">2</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="pybtexref:3">3</dt> \s* <dd> .* \. </dd>
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
                \s* <dl> 
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
            \s* <dl>
            \s* <dt[ ]id="pybtexref:1">1</dt> \s* <dd> .* \. </dd>
            \s* <dt[ ]id="pybtexref:2">2</dt> \s* <dd> .* \. </dd>
            \s* </dl>
        '''
        
        regex_citation_b = r'\s* <p>Citation[ ]B[ ]<cite[ ]id="pybtexcite:1-1">\[1]</cite>.</p>'
        regex_citation_c = r'\s* <p>Citation[ ]C[ ]<cite[ ]id="pybtexcite:2-1">\[2]</cite>.</p>'
        
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
            
            
        

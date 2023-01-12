from ..util.mock_progress import MockProgress
import unittest

import markdown
from lamarkdown.ext import latex

import base64
import os.path
import re
import tempfile
from textwrap import dedent

class LatexTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir_context = tempfile.TemporaryDirectory()
        self.tmp_dir = self.tmp_dir_context.__enter__()

        self.tex_file = os.path.join(self.tmp_dir, 'output.tex')
        self.mock_tex_command = os.path.join(self.tmp_dir, 'mock_tex_command')
        with open(self.mock_tex_command, 'w') as writer:

            # Create a tiny Python script to act as a mock 'tex' compiler.
            writer.write(dedent(
                fr'''
                import sys
                import shutil
                import os

                # If the .tex file (the one at the known location we're about to copy to) already
                # exists, find a new name. This lets us write test cases with multiple Latex
                # snippets.
                tex_file = '{self.tex_file}'
                if os.path.exists(tex_file):
                    index = 1
                    while os.path.exists(tex_file + str(index)):
                        index += 1
                    tex_file = tex_file + str(index)

                # Copy the .tex file to a known location, so the test case can find and read it.
                actual_tex_file = sys.argv[1]
                shutil.copyfile(actual_tex_file, tex_file)

                # Generate a mock .pdf file to satisfy the production code's checks.
                mock_pdf_file = sys.argv[2]
                with open(mock_pdf_file, 'w') as writer:
                    writer.write("mock")
                '''
            ))

        self.mock_svg = re.sub(
            r'\n\s*',
            '',
            '''
            <svg xmlns="http://www.w3.org/2000/svg" width="45" height="15">
                <text x="0" y="15">mock</text>
            </svg>
            '''
        )

        self.mock_pdf2svg_command = os.path.join(self.tmp_dir, 'mock_pdf2svg_command')
        with open(self.mock_pdf2svg_command, 'w') as writer:

            # Create another tiny Python script to act as a mock 'pdf2svg' converter.
            writer.write(dedent(
                fr'''
                import sys

                # Generate a mock output .svg file.
                mock_svg_file = sys.argv[2]
                with open(mock_svg_file, 'w') as writer:
                    writer.write('{self.mock_svg}')
                '''
            ))



    def tearDown(self):
        self.tmp_dir_context.__exit__(None, None, None)


    def run_markdown(self, markdown_text, **kwargs):
        md = markdown.Markdown(
            extensions = ['lamarkdown.ext.latex'],
            extension_configs = {'lamarkdown.ext.latex': {
                'build_dir': self.tmp_dir,
                'progress': MockProgress(),
                'tex': f'python {self.mock_tex_command} in.tex out.pdf',
                'pdf_svg_converter': f'python {self.mock_pdf2svg_command} in.pdf out.svg',
                **kwargs
            }}
        )
        return md.convert(dedent(markdown_text).strip())


    def assert_tex_regex(self, regex, file_index = ''):
        with open(f'{self.tex_file}{file_index or ""}', 'r') as reader:
            tex = reader.read()

        self.assertRegex(tex, regex,
            f'generated Tex code (#{file_index or 0}) does not match expected pattern\n---actual tex---\n{tex}\n---expected pattern---\n{dedent(regex).strip()}')

    @property
    def mock_svg_b64(self):
        return base64.b64encode(self.mock_svg.encode('utf-8')).decode('utf-8')


    def test_single_env(self):
        '''Check a single Latex environment.'''

        html = self.run_markdown(
            r'''
            Paragraph1

            \begin{tikzpicture}
                Latex code
            \end{tikzpicture}

            Paragraph2
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\begin \{document\}
            \s* \\begin \{tikzpicture\}
            \s* Latex[ ]code
            \s* \\end \{tikzpicture\}
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertIn(f'<p>Paragraph1</p>', html)
        self.assertIn(f'<p>Paragraph2</p>', html)
        self.assertIn(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}', html)


    def test_single_env_document(self):
        '''Check a complete embedded Latex document.'''

        html = self.run_markdown(
            r'''
            Paragraph1

            \begin{document}
                Latex code
            \end{document}

            Paragraph2
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\begin \{document\}
            \s* Latex[ ]code
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertIn(f'<p>Paragraph1</p>', html)
        self.assertIn(f'<p>Paragraph2</p>', html)
        self.assertIn(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}', html)


    def test_single_env_preamble(self):
        '''Check a single Latex environment with preceding preamble.'''

        html = self.run_markdown(
            r'''
            Paragraph1

            \usepackage{xyz}
            \somemacro{abc}
            \begin{tikzpicture}
                Latex code
            \end{tikzpicture}

            Paragraph2
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\usepackage \{xyz\}
            \s* \\somemacro \{abc\}
            \s* \\begin \{document\}
            \s* \\begin \{tikzpicture\}
            \s* Latex[ ]code
            \s* \\end \{tikzpicture\}
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertIn(f'<p>Paragraph1</p>', html)
        self.assertIn(f'<p>Paragraph2</p>', html)
        self.assertIn(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}', html)


    def test_full_doc(self):
        html = self.run_markdown(
            r'''
            Paragraph1

            \documentclass{article}
            \somemacro{def}
            \begin{document}
                Latex code
            \end{document}

            Paragraph2
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass \{article\}
            \s* \\somemacro \{def\}
            \s* \\begin \{document\}
            \s* Latex[ ]code
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertIn(f'<p>Paragraph1</p>', html)
        self.assertIn(f'<p>Paragraph2</p>', html)
        self.assertIn(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}', html)


    def test_attr(self):
        '''Check that attributes are assigned properly.'''

        html = self.run_markdown(
            r'''
            Paragraph1

            \begin{document}
                Latex code
            \end{document}
            {alt="alt text" width="5" #myid .myclass}

            Paragraph2
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\begin \{document\}
            \s* Latex[ ]code
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertIn(f'<p>Paragraph1</p>', html)
        self.assertIn(f'<p>Paragraph2</p>', html)

        img_tag = re.search('<img[^>]+>', html).group(0)
        self.assertIn('alt="alt text"', img_tag)
        self.assertIn('width="5"', img_tag)
        self.assertIn('id="myid"', img_tag)
        self.assertIn('class="myclass"', img_tag)


    def test_latex_comments(self):
        '''Check that Latex '%' comments don't stuff up the parsing.'''

        html = self.run_markdown(
            r'''
            Paragraph1

            \usepackage{abc} % \begin{tikzpicture}
            \begin{document} % \end{document}
                Latex code   % \end{tikzpicture}
            \end{document}   % \documentclass

            Paragraph2
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\usepackage \{abc\} (\s*%[^\n]+)?
            \s* \\begin \{document\} (\s*%[^\n]+)?
            \s* Latex[ ]code         (\s*%[^\n]+)?
            \s* \\end \{document\}   (\s*%[^\n]+)?
            \s* $
        ''')

        self.assertIn(f'<p>Paragraph1</p>', html)
        self.assertIn(f'<p>Paragraph2</p>', html)
        self.assertIn(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}', html)


    def test_html_comments(self):
        '''Check that HTML comments don't stuff up the parsing. This is complicated (on the production side) by the fact that Python Markdown appears to do its own substitution trick on HTML comments, but not all of them; perhaps only those where the <!-- and --> appear on separate lines.'''

        html = self.run_markdown(
            r'''
            Paragraph1

            \usepackage{abc} <!-- \begin{tikzpicture} -->
            <!--
            \usepackage{xyz}
            -->
            \begin{document} <!-- \end{document} -->
                Latex code   <!-- \end{tikzpicture} -->
            \end{document}   <!-- \documentclass -->

            Paragraph2
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\usepackage \{abc\}
            \s* \\begin \{document\}
            \s* Latex[ ]code
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertIn(f'<p>Paragraph1</p>', html)
        self.assertIn(f'<p>Paragraph2</p>', html)
        self.assertIn(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}', html)


    def test_commented_out_option_set(self, **kwargs):
        'Check that an entire Latex snippet is ignored if it occurs entirely within an HTML comment.'
        html = self.run_markdown(
            r'''
            Paragraph1 <!--

            \begin{document}
                Latex code
            \end{document}  -->

            Paragraph2
            ''',
            strip_html_comments = True)

        self.assertFalse(
            os.path.isfile(self.tex_file),
            'The .tex file should not have been created, because the Latex code was commented out.')


    # Note: I'm not sure how to construct the following test case properly.
    # Python Markdown intercepts some <!-- --> comments itself, but not all of them, meaning that
    # embedding Latex code in HTML comments *may or may not* make it visible to the latex
    # extension code. There's no definitive expectation on what should happen here.

    #def test_commented_out_option_unset(self):
        #html = self.run_markdown(
            #r'''
            #Paragraph1
            #<!--

            #\begin{document}
                #Latex code
            #\end{document}  -->

            #Paragraph2
            #''',
            #strip_html_comments = False)

        #self.assertTrue(
            #os.path.isfile(self.tex_file),
            #'The .tex file should have been created. Though the Latex code was commented out, the comments should have been disregarded.')



    def test_embedded_in_paragraph(self):
        'Previously, when the extension used a BlockProcessor, it would only identify Latex snippets starting in a new block; effectively a new paragraph.'
        html = self.run_markdown(
            r'''
            Text1
            \begin{document}
                Latex code
            \end{document}
            Text2
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\begin \{document\}
            \s* Latex[ ]code
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertRegex(
            html,
             r'<p>Text1\s*'
             + re.escape(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}" />')
             + r'\s*Text2</p>')


    def test_embedded_in_list(self):
        '''Previously, when the extension used a BlockProcessor, Latex snippets embedded in lists couldn't contain blank lines.'''
        html = self.run_markdown(
            r'''
            * List item 1

            * List item 2

                \begin{document}
                    Latex code 1

                    Latex code 2

                    Latex code 3
                \end{document}

                Trailing paragraph

            * List item 3
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\begin \{document\}
            \s* Latex[ ]code[ ]1
            \s* Latex[ ]code[ ]2
            \s* Latex[ ]code[ ]3
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertRegex(
            html,
            fr'''(?x)
            \s* <ul>
            \s* <li> \s* <p> List[ ]item[ ]1 \s* </p> \s* </li>
            \s* <li>
            \s* <p> List[ ]item[ ]2 \s* </p>
            \s* <p> <img[ ]src="data:image/svg\+xml;base64,{re.escape(self.mock_svg_b64)}" \s* /? > \s* </p>
            \s* <p> Trailing[ ]paragraph \s* </p>
            \s* </li>
            \s* <li> \s* <p> List[ ]item[ ]3 \s* </p> \s* </li>
            \s* </ul>
            \s*
            ''')


    def test_embedding_as_svg_element(self):
        '''Check that we can embed SVG content using an <svg> element (not just an <img> element with a data URL).'''
        html = self.run_markdown(
            r'''
            Paragraph1

            \begin{document}
                Latex code
            \end{document}

            Paragraph2
            ''',
            embedding = 'svg_element')

        self.assertRegex(html,
             r'<svg[^>]*><text[^>]*>mock</text></svg>')


    def test_latex_options(self):
        '''Check that the 'prepend', 'doc_class' and 'doc_class_options' config options work.'''
        html = self.run_markdown(
            r'''
            Paragraph1

            \begin{document}
                Latex code
            \end{document}

            Paragraph2
            ''',
            prepend = r'\usepackage{mypackage}',
            doc_class = 'myclass',
            doc_class_options = 'myoptions')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass \[ myoptions \] \{ myclass \}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\usepackage \{mypackage\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\begin \{document\}
            \s* Latex[ ]code
            \s* \\end \{document\}
            \s* $
        ''')


    def test_multiple(self):
        '''Check that we can process multiple Latex snippets in a single markdown file.'''
        html = self.run_markdown(
            r'''
            Paragraph1

            \begin{document}
                Latex code 0
            \end{document}

            Paragraph2

            \begin{document}
                Latex code 1
            \end{document}

            Paragraph3

            \begin{document}
                Latex code 2
            \end{document}

            Paragraph4
            ''')

        for i in [0, 1, 2]:
            self.assert_tex_regex(fr'''(?x)
                ^\s* \\documentclass (\[\])? \{{standalone\}}
                \s* ( \\usepackage \{{tikz\}} )?
                \s* \\begin \{{document\}}
                \s* Latex[ ]code[ ]{i}
                \s* \\end \{{document\}}
                \s* $
            ''',
            file_index = i)

        for i in [1, 2, 3, 4]:
            self.assertIn(f'<p>Paragraph{i}</p>', html)

        self.assertEqual(
            3, html.count(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}'),
            'There should be 3 <img> elements, one for each Latex snippet')


    def test_multiple_cached(self):
        '''Check that, when processing multiple identical Latex snippets, we use the cache rather than re-compiling redundantly.'''
        html = self.run_markdown(
            r'''
            Paragraph1

            \begin{document}
                Latex code
            \end{document}

            Paragraph2

            \begin{document}
                Latex code
            \end{document}

            Paragraph3

            \begin{document}
                Latex code
            \end{document}

            Paragraph4
            ''')

        self.assert_tex_regex(r'''(?x)
            ^\s* \\documentclass (\[\])? \{standalone\}
            \s* ( \\usepackage \{tikz\} )?
            \s* \\begin \{document\}
            \s* Latex[ ]code
            \s* \\end \{document\}
            \s* $
        ''')

        self.assertFalse(os.path.exists(f'{self.tex_file}1'))
        self.assertFalse(os.path.exists(f'{self.tex_file}2'))

        for i in [1, 2, 3, 4]:
            self.assertIn(f'<p>Paragraph{i}</p>', html)

        self.assertEqual(
            3, html.count(f'<img src="data:image/svg+xml;base64,{self.mock_svg_b64}'),
            'There should be 3 <img> elements, one for each Latex snippet')



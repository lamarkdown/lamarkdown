from ..util.mock_progress import MockProgress
from lamarkdown.lib import md_compiler, build_params

import unittest

import markdown
import lxml

import os
import tempfile
from textwrap import dedent


class CssTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_dir_context = tempfile.TemporaryDirectory()
        self.tmp_dir = self.tmp_dir_context.__enter__()
        self.html_file = os.path.join(self.tmp_dir, 'testdoc.html')


    def tearDown(self):
        self.tmp_dir_context.__exit__(None, None, None)


    def run_md_compiler(self, markdown = '', build = None, build_defaults = True, is_live = False):
        doc_file   = os.path.join(self.tmp_dir, 'testdoc.md')
        build_file = os.path.join(self.tmp_dir, 'testbuild.py')
        build_dir  = os.path.join(self.tmp_dir, 'build')

        with open(doc_file, 'w') as writer:
            writer.write(dedent(markdown))

        if build is not None:
            with open(build_file, 'w') as writer:
                 writer.write(dedent(build))

        bp = build_params.BuildParams(
            src_file = doc_file,
            target_file = self.html_file,
            build_files = [build_file] if build else [],
            build_dir = build_dir,
            build_defaults = build_defaults,
            cache = {},
            progress = MockProgress(),
            is_live = is_live
        )
        md_compiler.compile(bp)

        # Parse with lxml to ensure that the output is well formed, and to allow it to be queried
        # with XPath expressions.
        root = lxml.html.parse(self.html_file)

        # we probably want to just check the whole <body> element at once though.
        body_html = lxml.html.tostring(root.find('body'), with_tail = False, encoding = 'unicode')

        return (root, body_html)


    def test_basic(self):
        root, body_html = self.run_md_compiler(
            r'''
            # Heading

            Paragraph1
            ''',
            build_defaults = False)

        # The meta charset declaration should be there as a matter of course.
        self.assertNotEqual('[]', root.xpath('/html/head/meta[@charset="utf-8"]'))

        # The title should be taken from the <h1> element.
        self.assertEqual('Heading', root.xpath('//head//title')[0].text)

        # Check the document structure.
        self.assertRegex(
            body_html,
            r'''(?x)
            \s* <body>
            \s* <h1> Heading </h1>
            \s* <p> Paragraph1 </p>
            \s* </body>
            \s*
            ''')

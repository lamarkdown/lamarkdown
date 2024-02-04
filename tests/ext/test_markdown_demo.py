from ..util.markdown_ext import entry_point_cls
import unittest
from unittest.mock import patch
from hamcrest import assert_that, instance_of, same_instance

import lamarkdown.ext
import markdown

# import re
import sys
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']


class MarkdownDemoTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text, other_extensions = [], other_config = {}, **kwargs):
        md = markdown.Markdown(
            extensions = ['la.markdown_demo', *other_extensions],
            extension_configs = {'la.markdown_demo': kwargs, **other_config}
        )
        return md.convert(dedent(markdown_text).strip())


    def test_basic(self):
        html = self.run_markdown(
            '''
            /// markdown-demo
            print("build file")
            ---
            # Markdown Heading
            ///
            ''')

        print(html)

        # TODO!


    def test_extension_setup(self):
        assert_that(
            entry_point_cls('la.markdown_demo'),
            same_instance(lamarkdown.ext.markdown_demo.MarkdownDemoExtension))

        instance = lamarkdown.ext.markdown_demo.MarkdownDemoExtension()

        assert_that(
            instance,
            instance_of(lamarkdown.ext.markdown_demo.MarkdownDemoExtension))

        class MockBuildParams:
            def __getattr__(self, name):
                raise ModuleNotFoundError

        with patch('lamarkdown.lib.build_params.BuildParams', MockBuildParams()):
            instance = lamarkdown.ext.markdown_demo.MarkdownDemoExtension()

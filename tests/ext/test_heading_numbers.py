import unittest
from unittest.mock import patch
from hamcrest import *

import lamarkdown.ext
import markdown

import sys
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']

class HeadingNumbersTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text, **kwargs):
        md = markdown.Markdown(
            extensions = ['la.heading_numbers'],
            extension_configs = {'la.heading_numbers': kwargs}
        )
        return md.convert(dedent(markdown_text).strip())


    def test_headings(self):
        '''Check a simple tree of headings.'''

        html = self.run_markdown(
            r'''
            # Top-Level Heading

            ## Section 1

            ### Section 1.1

            ### Section 1.2

            ### Section 1.3

            ## _Section_ 2

            ### **Section** 2.1

            #### Section 2.1.1

            ##### Section 2.1.1.1

            ###### Section 2.1.1.1.1

            ### Section 2.2
            ''')

        self.assertRegex(
            html,
            fr'''(?xs)
            \s* <h1>Top-Level[ ]Heading</h1>
            \s* <h2><span[ ]class="la-heading-number">1</span>[ ]Section[ ]1</h2>
            \s* <h3><span[ ]class="la-heading-number">1.1</span>[ ]Section[ ]1.1</h3>
            \s* <h3><span[ ]class="la-heading-number">1.2</span>[ ]Section[ ]1.2</h3>
            \s* <h3><span[ ]class="la-heading-number">1.3</span>[ ]Section[ ]1.3</h3>
            \s* <h2><span[ ]class="la-heading-number">2</span>[ ]<em>Section</em>[ ]2</h2>
            \s* <h3><span[ ]class="la-heading-number">2.1</span>[ ]<strong>Section</strong>[ ]2.1</h3>
            \s* <h4><span[ ]class="la-heading-number">2.1.1</span>[ ]Section[ ]2.1.1</h4>
            \s* <h5><span[ ]class="la-heading-number">2.1.1.1</span>[ ]Section[ ]2.1.1.1</h5>
            \s* <h6><span[ ]class="la-heading-number">2.1.1.1.1</span>[ ]Section[ ]2.1.1.1.1</h6>
            \s* <h3><span[ ]class="la-heading-number">2.2</span>[ ]Section[ ]2.2</h3>
            \s*
            '''
        )

    def test_extension_setup(self):
        import importlib
        import importlib.metadata

        module_name, class_name = importlib.metadata.entry_points(
            group = 'markdown.extensions')['la.heading_numbers'].value.split(':', 1)
        cls = importlib.import_module(module_name).__dict__[class_name]

        assert_that(
            cls,
            same_instance(lamarkdown.ext.heading_numbers.HeadingNumbersExtension))

        instance = lamarkdown.ext.heading_numbers.makeExtension(from_level = 4)

        assert_that(
            instance,
            instance_of(lamarkdown.ext.heading_numbers.HeadingNumbersExtension))

        assert_that(
            instance.getConfig('from_level'),
            is_(4))

        class MockBuildParams:
            def __getattr__(self, name):
                raise ModuleNotFoundError

        with patch('lamarkdown.lib.build_params.BuildParams', MockBuildParams()):
            instance = lamarkdown.ext.heading_numbers.makeExtension()

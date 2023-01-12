import unittest

import markdown
from lamarkdown.ext import heading_numbers

from textwrap import dedent


class HeadingNumbersTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text, **kwargs):
        md = markdown.Markdown(
            extensions = ['lamarkdown.ext.heading_numbers'],
            extension_configs = {'lamarkdown.ext.heading_numbers':
            {

                **kwargs
            }}
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

            ## Section 2

            ### Section 2.1

            #### Section 2.1.1

            ##### Section 2.1.1.1

            ###### Section 2.1.1.1.1

            ### Section 2.2
            ''')

        self.assertRegex(
            html,
            fr'''(?x)
            \s* <h1>Top-Level[ ]Heading</h1>
            \s* <h2><span[ ]class="hnumber">1</span>[ ]Section[ ]1</h2>
            \s* <h3><span[ ]class="hnumber">1.1</span>[ ]Section[ ]1.1</h3>
            \s* <h3><span[ ]class="hnumber">1.2</span>[ ]Section[ ]1.2</h3>
            \s* <h3><span[ ]class="hnumber">1.3</span>[ ]Section[ ]1.3</h3>
            \s* <h2><span[ ]class="hnumber">2</span>[ ]Section[ ]2</h2>
            \s* <h3><span[ ]class="hnumber">2.1</span>[ ]Section[ ]2.1</h3>
            \s* <h4><span[ ]class="hnumber">2.1.1</span>[ ]Section[ ]2.1.1</h4>
            \s* <h5><span[ ]class="hnumber">2.1.1.1</span>[ ]Section[ ]2.1.1.1</h5>
            \s* <h6><span[ ]class="hnumber">2.1.1.1.1</span>[ ]Section[ ]2.1.1.1.1</h6>
            \s* <h3><span[ ]class="hnumber">2.2</span>[ ]Section[ ]2.2</h3>
            \s*
            '''
        )

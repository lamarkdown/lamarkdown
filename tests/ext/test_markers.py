import unittest

import lamarkdown.ext
import markdown
import sys
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']

class MarkersTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text, **kwargs):
        md = markdown.Markdown(
            extensions = ['la.markers']
        )
        return md.convert(dedent(markdown_text).strip())


    def test_usage(self):
        html = self.run_markdown(
            r'''
            # Heading
            
            /{.classX #idY attrZ="value"}
            
            1. Item1
            
                /{.classA}
                
            2. Item2
            ''')

        self.assertRegex(
            html,
            r'''(?x)
            \s* <h1>Heading</h1>
            \s* <div[ ]attrZ="value"[ ]class="classX"[ ]id="idY"[ ]style="display:\s*none;?"\s*(/>|></div>)
            \s* <ol>
            \s* <li>
            \s* <p>Item1</p>
            \s* <div[ ]class="classA"[ ]style="display:\s*none;?"\s*(/>|></div>)
            \s* </li>
            \s* <li>
            \s* <p>Item2</p>
            \s* </li>
            \s* </ol>
            \s*
            '''
        )

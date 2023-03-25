from lamarkdown.ext.util import replacement_patterns

import unittest
from hamcrest import *
import markdown
# import lxml.html

# from textwrap import dedent
from xml.etree import ElementTree


# Test design
# - pattern recognition in different structural cases:
#   <span>...</span>$some text$
#   <span>...</span><br>$some text$
#
# - verify that other things are not detected within the delimiters
#
# - multiple instance recognition
#   $some text$$some text$
#   $some text$x$some text$
#   $some text$<span></span>$some text$
#
# - interactions between two replacement patterns
# - interactions between replacement and inline patterns (particularly backticks)
# - escaping
# - respecting AtomicString


class ReplacementPatternsTestCase(unittest.TestCase):


    def test_single_pattern(self):

        class DollarPattern(replacement_patterns.ReplacementPattern):
            def __init__(self):
                super().__init__('\$([^$]+)\$')

            def handle_match(self, match):
                elem = ElementTree.Element('span', x = '1')
                elem.text = match.group(1)
                return elem


        for input_text, expected_html in [
            # Structural variations
            (
                'hello $some text$ world',
                'hello <span x="1">some text</span> world'
            ),
            (
                '<span>hello</span>$some text$ world',
                '<span>hello</span><span x="1">some text</span> world'
            ),
            (
                '<span>he</span>llo $some text$ wor<span>ld</span>',
                '<span>he</span>llo <span x="1">some text</span> wor<span>ld</span>'
            ),
            (
                '<span>h</span>e<span>l</span>lo $some text$<span> world</span>',
                '<span>h</span>e<span>l</span>lo <span x="1">some text</span><span> world</span>'
            ),

            # Multiple instances
            (
                'hello $some$$text$ world',
                'hello <span x="1">some</span><span x="1">text</span> world'
            ),
            (
                '<span>he</span>llo $some$$text$ world',
                '<span>he</span>llo <span x="1">some</span><span x="1">text</span> world'
            ),
            (
                'hello $so$$me$<span>-</span>$te$...$xt$ world',
                'hello <span x="1">so</span><span x="1">me</span><span>-</span><span x="1">te</span>...<span x="1">xt</span> world'
            ),

            # Other patterns _can't_ match inside a replacement pattern
            (
                '_hello_ $_some_ `text`$ `world`',
                '<em>hello</em> <span x="1">_some_ `text`</span> <code>world</code>'
            ),

            # Escaping
            (
                r'hello \$some text$ world',
                r'hello $some text$ world'
            ),
            (
                r'hello \\\\$some text$ world',
                r'hello \\<span x="1">some text</span> world'
            ),
            (
                r'hello \\\\\$some text$ world',
                r'hello \\$some text$ world'
            ),
        ]:
            md = markdown.Markdown()
            replacement_patterns.init(md)
            md.ESCAPED_CHARS.append('$')
            md.replacement_patterns.register(DollarPattern(), 'dollar', 10)

            html = md.convert(input_text)
            # print(html)

            assert_that(html, contains_string(expected_html))


    def test_transparent_pattern(self):
        class DollarPattern(replacement_patterns.ReplacementPattern):
            def __init__(self):
                super().__init__('\$([^$]+)\$', allow_inline_patterns = True)

            def handle_match(self, match):
                elem = ElementTree.Element('span', x = '1')
                elem.text = match.group(1)
                return elem

        input_text = '_hello_ $_some_ `text`$ `world`'
        expected_html = '<em>hello</em> <span x="1"><em>some</em> <code>text</code></span> <code>world</code>'

        md = markdown.Markdown()
        replacement_patterns.init(md)
        md.ESCAPED_CHARS.append('$')
        md.replacement_patterns.register(DollarPattern(), 'dollar', 10)

        html = md.convert(input_text)
        assert_that(html, contains_string(expected_html))

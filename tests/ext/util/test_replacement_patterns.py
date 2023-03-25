from lamarkdown.ext.util import replacement_patterns

import unittest
from hamcrest import *
import markdown

from xml.etree import ElementTree


# Test design
# - respecting AtomicString


class ReplacementPatternsTestCase(unittest.TestCase):

    def test_single_pattern(self):

        class TestHtmlBlockProcessor(markdown.blockprocessors.BlockProcessor):
            '''
            This is to force Markdown to convert HTML into actual Element nodes, to be seen in the
            tree-processing (and hence replacement-processing) stage. We need a way to test that
            ReplacementProcessor can handle structural situations.
            '''
            def test(self, parent, block):
                return True

            def run(self, parent, blocks):
                parent.append(ElementTree.fromstring(f'<p>{blocks.pop(0)}</p>'))


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
            (
                r'hello \$x\\\$y\\\\\$z world',
                r'hello $x\$y\\$z world'
            ),

            # Backtick interaction (also tests the interaction of two replacement patterns
            # generally)
            (
                r'hello `$some text$` world',
                r'hello <code>$some text$</code> world'
            ),
            (
                r'hello ````$some text$```` world',
                r'hello <code>$some text$</code> world'
            ),
            (
                r'hello $`some text`$ world',
                r'hello <span x="1">`some text`</span> world'
            ),
            (
                r'hello $````some text````$ world',
                r'hello <span x="1">````some text````</span> world'
            ),
            (
                r'hello `$some`$`text$` world',
                r'hello <code>$some</code><span x="1">`text</span>` world'
            ),
            (
                r'hello $`some$`$text`$ world',
                r'hello <span x="1">`some</span><code>$text</code>$ world'
            ),
        ]:
            md = markdown.Markdown()
            md.parser.blockprocessors.register(TestHtmlBlockProcessor(md.parser), 'testblock', 1000)

            replacement_patterns.init(md)
            md.ESCAPED_CHARS.append('$')
            md.replacement_patterns.register(DollarPattern(), 'dollar', 10)

            html = md.convert(input_text)

            assert_that(html, contains_string(expected_html))



    def test_transparent_pattern(self):
        class ElementPattern(replacement_patterns.ReplacementPattern):
            def __init__(self):
                super().__init__('\$([^$]+)\$', allow_inline_patterns = True)

            def handle_match(self, match):
                elem = ElementTree.Element('span', x = '1')
                elem.text = match.group(1)
                return elem


        class StringPattern(replacement_patterns.ReplacementPattern):
            def __init__(self):
                super().__init__('\$([^$]+)\$', allow_inline_patterns = True)

            def handle_match(self, match):
                return f'AAA {match.group(1)} BBB'


        input_text = '_hello_ $_some_ `text`$ `world`'

        for pattern, expected_html in [
            (
                ElementPattern,
                '<em>hello</em> <span x="1"><em>some</em> <code>text</code></span> <code>world</code>'
            ),
            (
                StringPattern,
                '<em>hello</em> AAA <em>some</em> <code>text</code> BBB <code>world</code>'
            )
        ]:
            md = markdown.Markdown()
            replacement_patterns.init(md)
            md.ESCAPED_CHARS.append('$')
            md.replacement_patterns.register(pattern(), 'dollar', 10)

            html = md.convert(input_text)
            assert_that(html, contains_string(expected_html))

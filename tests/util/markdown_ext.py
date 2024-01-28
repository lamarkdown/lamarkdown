from __future__ import annotations
# from hamcrest import assert_that, matches_regexp
import markdown
import importlib
import re
import sys
from xml.etree import ElementTree


def entry_point_cls(name: str) -> tuple[str, str]:

    if sys.version_info >= (3, 10):
        entry_point = importlib.metadata.entry_points(group='markdown.extensions')[name]

    else:
        entry_point = next(
            ep
            for ep in importlib.metadata.entry_points()['markdown.extensions']
            if ep.name == name
        )

    module_name, class_name = entry_point.value.split(':', 1)
    return importlib.import_module(module_name).__dict__[class_name]



class HtmlInsert(markdown.extensions.Extension):
    '''
    A Python Markdown extension for pure testing purposes -- injects arbitrary DOM subtree at a
    given point in the markdown.

    We can't achieve the same thing by writing literal HTML within the markdown, because that won't
    get embedded until the postprocessing stage, and we need it there earlier.
    '''

    def __init__(self, html, **kwargs):
        super().__init__(**kwargs)
        self.elements = list(ElementTree.fromstring(f'<div>{html}</div>'))

    def extendMarkdown(self, md):
        elements = self.elements

        class BlockProcessor(markdown.blockprocessors.BlockProcessor):
            def __init__(self):
                super().__init__(md.parser)

            def test(self, parent, block):
                return block == 'X'

            def run(self, parent, blocks):
                blocks.pop(0)
                parent.extend(elements)

        md.parser.blockprocessors.register(BlockProcessor(), 'hibp', 1000)


def assert_regex(actual: str,
                 regex: str,
                 flags = re.DOTALL | re.VERBOSE,
                 spacing_at_newlines = True):
    '''
    Asserts that string 'actual' matches regular expression 'regex', given 'flags' (by default,
    allowing '.' to match new newlines, and ignoring spaces and in-regex comments).

    Most importantly, in case of match failure, this function pinpoints the index of the
    mismatch (in both the string and the regex), using a binary search, and outputs this using
    ANSI highlighting.

    The algorithm is a bit simple-minded, and won't (for instance) precisely identify a mismatch
    index within brackets (instead identifying the starting bracket). However, most of our test
    code regexes don't seem to need to do this.
    '''

    if spacing_at_newlines:
        regex = re.sub(r'\n', '\n\\\\s*', regex)

    if re.fullmatch(regex, actual, flags = flags):
        return

    # Binary search for point of failure
    from_index = 0
    to_index = len(regex)
    halfway_index = from_index + (to_index - from_index) // 2
    remainder_index = 0

    while from_index < halfway_index:
        try:
            if match := re.fullmatch(regex[:halfway_index] + '(?P<remainder>.*)',
                                     actual,
                                     flags = flags):
                remainder_index = match.start('remainder')
                from_index = halfway_index
            else:
                to_index = halfway_index
            halfway_index = from_index + (to_index - from_index) // 2

        except re.error:
            # We caused the regex to be invalid; try again. (Note: the empty string is a valid
            # regex.)
            halfway_index -= 1

    HERE = '\x1b[44m 🡆 \x1b[40m'

    raise AssertionError(
        f'Match failed at string index {remainder_index}, regex index {from_index}:\n\n'
        f'--- ACTUAL ---\n{actual[:remainder_index]}{HERE}{actual[remainder_index:]}\n\n'
        f'--- REGEX ---\n{regex[:from_index]}{HERE}{regex[from_index:]}')

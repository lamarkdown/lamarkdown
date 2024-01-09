from lamarkdown.ext import util

import markdown
from xml.etree import ElementTree


class TestHtmlBlockProcessor(markdown.blockprocessors.BlockProcessor):
    '''
    This is to force Markdown to convert HTML into actual Element nodes, to be seen in the
    tree-processing (and hence replacement-processing) stage. This is so that we can test our
    inline and replacement processors in different structural situations.

    Note: this won't work on <div>s, which are captured earlier by Python Markdown, and stored
    using \x02 and \x03, which ElementTree considers invalid tokens.
    '''
    def test(self, parent, block):
        return True

    def run(self, parent, blocks):
        element = ElementTree.fromstring(f'<p>{blocks.pop(0)}</p>')
        if 'atomic' in element.attrib:
            del element.attrib['atomic']
            util.opaque_subtree(element)
        parent.append(element)


def init(md):
    md.parser.blockprocessors.register(
        TestHtmlBlockProcessor(md.parser),
        'testblock', 1000)

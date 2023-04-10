'''
# Attribute Prefix Extension

This extension permits attribute lists preceding a block, even with intervening whitespace. The
extension will associate an attribute list occurring at the start of a block, or in a block on its
own, with the next element in the document tree (at the same level of the tree).

This permits the styling of <ol> and <ul> (HTML list elements) that can't otherwise have attributes
associated with them. In other cases, it may simply seem more logical for certain attributes to
precede their elements.
'''

from . import util
import markdown

import re
from xml.etree import ElementTree


_ATTR_PREFIX_ATTR = 'la-attr-prefix-af9812f46b7201769eaf0d1a97f5a369'

ATTR_PREFIX_RE = re.compile(rf'(?x){util.ATTR}\s*(\n|$)')

class AttrPrefixBlockProcessor(markdown.blockprocessors.BlockProcessor):
    def __init__(self, md_parser):
        super().__init__(md_parser)

    def test(self, parent, block):
        self._match = ATTR_PREFIX_RE.match(block)
        return self._match

    def run(self, parent, blocks):
        block = blocks.pop(0)[self._match.end(0):]
        if len(block.strip()) > 0:
            blocks.insert(0, block)

        elem = ElementTree.SubElement(parent, 'div', {_ATTR_PREFIX_ATTR: '1'})
        util.set_attributes(elem, self._match.group('attr'))


class AttrPrefixTreeProcessor(markdown.treeprocessors.Treeprocessor):

    COMBINING_ATTRS = {
        ('class', ' '),
        ('style', '; '),
    }

    def __init__(self, md):
        super().__init__(md)


    def run(self, root):
        to_remove = []
        attrib = {}

        for element in root:
            if element.get(_ATTR_PREFIX_ATTR) == '1':
                del element.attrib[_ATTR_PREFIX_ATTR]
                self._merge_attributes(element.attrib, attrib)
                attrib = element.attrib
                to_remove.append(element)
            else:
                if attrib:
                    self._merge_attributes(element.attrib, attrib)
                    attrib = {}
                self.run(element)

        for element in to_remove:
            root.remove(element)

        return None


    def _merge_attributes(self, dest, src):
        original_dest = dict(dest)
        dest.update(src)

        for key, separator in self.COMBINING_ATTRS:
            src_value = src.get(key)
            dest_value = original_dest.get(key)
            if src_value and dest_value:
                dest[key] = f'{dest_value}{separator}{src_value}'


class AttrPrefixExtension(markdown.Extension):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # Auto-load attr_list, since conceptually attr_prefix is an add-on to it (and uses its code)
        md.registerExtensions(['attr_list'], {})

        md.parser.blockprocessors.register(
            AttrPrefixBlockProcessor(md.parser), 'la-attr-prefix-block', 95)
        md.treeprocessors.register(
            AttrPrefixTreeProcessor(md), 'la-attr-prefix-tree', 15)


def makeExtension(**kwargs):
    return AttrPrefixExtension(**kwargs)

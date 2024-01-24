from __future__ import annotations
import markdown
import importlib
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

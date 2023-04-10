'''
# Markers Extension (DEPRECATED - use attr_prefix instead)

This extension enables a CSS hack, useful in particular for styling <ol> and <ul> elements
generated from Markdown lists. These elements have no direct representation in .md files, and so
there is nothing (normally) to attach attributes to, even with the attr_list {...} syntax.

The markers extension recognises one-line blocks of the form '/{...}'. It makes the resulting
elements invisible (with 'display: none'). However, you can attach attributes to them, and if
placed before a list, you can style the list using the CSS sibling selector '+'.
'''

from . import util
from lamarkdown.lib.progress import Progress
import markdown

import re
from xml.etree import ElementTree


NAME = 'la.markers'

class MarkersTreeProcessor(markdown.treeprocessors.Treeprocessor):
    REGEX = re.compile(rf'(?x)/{util.ATTR}')

    def __init__(self, md, progress):
        super().__init__(md)
        self.progress = progress

    def run(self, root):
        for element in root.iter('p'):
            if not (element.text is None or isinstance(element.text, markdown.util.AtomicString)):
                match = self.REGEX.fullmatch(element.text)
                if match:
                    self.progress.warning(
                        NAME,
                        msg = 'Deprecated use of /{...} "marker" notation; use {...} instead (from attr_prefix)')

                    # Not a paragraph anymore
                    element.tag = 'div'

                    # Leave just the attribute list, for attr_list to parse later.
                    element.text = None

                    # attr_list_proc.assign_attrs(element, attrs)
                    util.set_attributes(element, match)

                    # Stop it being rendered in the output.
                    element.set('style', 'display: none;')

        return None



class MarkersExtension(markdown.Extension):
    def __init__(self, **kwargs):
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass # Use default defaults

        self.config = {
            'progress': [
                p.progress if p else Progress(),
                'An object accepting progress messages.'
            ],
        }
        super().__init__(**kwargs)


    def extendMarkdown(self, md):
        # Auto-load attr_list, since the markers extension is essentially useless without it.
        md.registerExtensions(['attr_list'], {})

        md.treeprocessors.register(
            MarkersTreeProcessor(md, self.getConfig('progress')), 'la-markers-tree', 100)


def makeExtension(**kwargs):
    return MarkersExtension(**kwargs)

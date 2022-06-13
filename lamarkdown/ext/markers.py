'''
# Markers Extension

This extension enables a CSS hack, useful in particular for styling <ol> and <ul> elements
generated from Markdown lists. These elements have no direct representation in .md files, and so
there is nothing (normally) to attach attributes to, even with the attr_list {...} syntax.

The markers extension recognises one-line blocks of the form '/{...}'. It makes the resulting
elements invisible (with 'display: none'). However, you can attach attributes to them, and if
placed before a list, you can style the list using the CSS sibling selector '+'.
'''


import markdown
import re
from xml.etree import ElementTree


class MarkersProcessor(markdown.treeprocessors.Treeprocessor):
    REGEX = re.compile('/(\{[^}]*\})')

    def __init__(self, md):
        super().__init__(md)

    def run(self, root):
        for element in root:
            if isinstance(element.text, str):
                match = self.REGEX.fullmatch(element.text)
                if match:
                    element.text = '\n' + match.group(1)
                    element.set('style', 'display: none;')

            self.run(element)

        return None



class MarkersExtension(markdown.Extension):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        proc = MarkersProcessor(md)
        md.treeprocessors.register(proc, 'lamarkdown.markers', 100)



def makeExtension(**kwargs):
    return MarkersExtension(**kwargs)

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
    REGEX = re.compile(r'/({[^}]*})')

    def __init__(self, md):
        super().__init__(md)

    def run(self, root):
        for element in root.iter('p'):
            if isinstance(element.text, str):
                match = self.REGEX.fullmatch(element.text)
                if match:
                    # Not a paragraph anymore
                    element.tag = 'div'
                    
                    # Leave just the attribute list, for attr_list to parse later.
                    element.text = '\n' + match.group(1)
                    
                    # Stop it being rendered in the output.
                    element.set('style', 'display: none;')

        return None



class MarkersExtension(markdown.Extension):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # Auto-load attr_list, since the markers extension is essentially useless without it.
        md.registerExtensions(['attr_list'], {}) 
        
        md.treeprocessors.register(MarkersProcessor(md), 'la-markers-tree', 100)


def makeExtension(**kwargs):
    return MarkersExtension(**kwargs)

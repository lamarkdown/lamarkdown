'''
The 'pruner' extension deletes branches of a document tree having certain specified classes.

This is used by Lamarkdown to arrange for different variations of a document to be built from the
same source.
'''

import markdown
from typing import Set
from xml.etree import ElementTree


class PrunerTreeProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md, prune_classes: Set[str]):
        super().__init__(md)
        self.prune_classes = prune_classes

    def run(self, root):
        prune_elements = []
        for element in root:
            element_classes = (element.attrib.get('class') or '').split()
            if not self.prune_classes.isdisjoint(element_classes):
                prune_elements.append(element)

        for element in prune_elements:
            root.remove(element)

        # Recurse
        for element in root:
            self.run(element)

        return None



class PrunerExtension(markdown.Extension):
    def __init__(self, **kwargs):
        self.config = {
            'classes': [set(), 'Elements with any of the specified classes will be discarded from the document'],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        proc = PrunerTreeProcessor(md, set(self.getConfig('classes')))
        md.treeprocessors.register(proc, 'lamarkdown.pruner', -100)



def makeExtension(**kwargs):
    return PrunerExtension(**kwargs)

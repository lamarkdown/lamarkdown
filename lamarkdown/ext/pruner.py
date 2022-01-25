import markdown
from xml.etree import ElementTree


class PrunerTreeProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md, pruneClasses: set[str]):
        super().__init__(md)
        self.pruneClasses = pruneClasses
        
    def run(self, root):
        pruneElements = []
        for element in root:            
            elementClasses = (element.attrib.get('class') or '').split()
            if not self.pruneClasses.isdisjoint(elementClasses):
                pruneElements.append(element)
                
        for element in pruneElements:
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
        

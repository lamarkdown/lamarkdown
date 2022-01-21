import markdown
import re
from xml.etree import ElementTree


class MarkerElementProcessor(markdown.treeprocessors.Treeprocessor):
    REGEX = re.compile('/(\{[^}]*\})')
    
    def __init__(self, md):
        super().__init__(md)
        
    def run(self, root):
        for element in root:
            if isinstance(element.text, str):
                if match := self.REGEX.fullmatch(element.text):
                    element.text = '\n' + match.group(1)
                    element.set('style', 'display: none;')
            
            self.run(element)
        
        return None
    


class MarkerElementExtension(markdown.Extension):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def extendMarkdown(self, md):
        proc = MarkerElementProcessor(md)
        md.treeprocessors.register(proc, 'marker_elements', 100)
        

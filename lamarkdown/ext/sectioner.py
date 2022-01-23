import markdown
from xml.etree import ElementTree


class SectionProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md, separator = '///'):
        super().__init__(md)
        self._separator = separator
        
    def run(self, root):   
        sections_found = False
        first = True
        new_root = ElementTree.Element('div')
        section = ElementTree.Element('section')
        section.text = '\n'
        section.tail = '\n'
        
        for element in root:
            if element.tag == 'p' and element.text == self._separator:
                sections_found = True
                if not first:
                    # Allow for a 'separator' right at the start, which serves purely to specify
                    # attributes, and doesn't create a blank first section.
                    new_root.append(section)
                
                section = ElementTree.Element('section')
                section.text = '\n'
                section.tail = '\n'
                section.attrib = element.attrib
                
            else:
                section.append(element)            
                
            first = False
            
        new_root.append(section)                
        return new_root if sections_found else root
    


class SectionerExtension(markdown.Extension):
    def __init__(self, **kwargs):
        self.config = {
            'separator': ['///', 'Sections will be divided by this string (which must be its own top-level block).'],
        }
        super().__init__(**kwargs)
        
    def extendMarkdown(self, md):
        proc = SectionProcessor(md, self.getConfig('separator'))
        md.treeprocessors.register(proc, 'revealjs', -50)
        

'''
# Pybtex Extension

'''

import markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor

import pybtex.backends.html
import pybtex.plugin

import lxml.html

import io
import re
from typing import List
from xml.etree import ElementTree


class CitationInlineProcessor(InlineProcessor):
    REGEX = r'\[@([^]]+)\]'
    
    def __init__(self, cited_keys: List[str]):
        super().__init__(self.REGEX)
        self.cited_keys = cited_keys
        
    def handleMatch(self, match, data):
        key = match.group(1)
        self.cited_keys.append(key)
        elem = ElementTree.Element('cite')
        elem.attrib['key'] = key
        return elem, match.start(0), match.end(0)
        
        
class ModifiedPybtexHtmlBackend(pybtex.backends.html.Backend):
    def __init__(self):
        super().__init__('utf-8')
        
    def write_entry(self, key, label, text):
        self.output(f'<dt id="pybtexref:{label}">{label}</dt>\n')
        self.output(f'<dd label="{label}">{text}</dd>\n')
        # Note: the 'label' attribute will be deleted later on. It's just here to help match up
        # this HTML (the reference) with its corresponding citations.
        

class PybtexTreeProcessor(Treeprocessor):
    def __init__(self, md, ext, cited_keys: List[str]):
        super().__init__(md)
        self.ext = ext
        
        # 'cited_keys' will be empty at first, but in between here and run() below, 
        # CitationInlineProcessor will add all citations found in the document.
        self.cited_keys = cited_keys
        
    def run(self, root):
        # 'cited_keys' will have been populated by now.
        
        file_spec = self.ext.getConfig('file')
        if file_spec is None:
            files = []
        elif isinstance(file_spec, str):
            files = [file_spec]
        else:
            files = list(file_spec)
        
        ref_str = self.ext.getConfig('references')
        if ref_str:
            files.append(io.StringIO(ref_str))
        
        bib_parser = pybtex.plugin.find_plugin('pybtex.database.input', self.ext.getConfig('format'))
        bib_data = bib_parser(
            encoding = self.ext.getConfig('encoding'),
            wanted_entries = self.cited_keys,
            min_crossrefs = self.ext.getConfig('min_crossrefs')).parse_files(files)
        
        # TODO: handle errors from parse_files(): pybtex.database.BibliographyDataError and OSError
        
        style_cls = pybtex.plugin.find_plugin('pybtex.style.formatting', self.ext.getConfig('style'))
        style = style_cls(
            label_style      = self.ext.getConfig('label_style'),
            name_style       = self.ext.getConfig('name_style'),
            sorting_style    = self.ext.getConfig('sorting_style'),
            abbreviate_names = self.ext.getConfig('abbreviate_names'),
            min_crossrefs    = self.ext.getConfig('min_crossrefs')
        )
        formatted_biblio = style.format_bibliography(bib_data, self.cited_keys)
        
        # Populate the <cite> elements (created by CitationInlineProcessor) with the 'labels' 
        # created by Pybtex.
        entries = {entry.key: entry for entry in formatted_biblio.entries}
        n_citations = {}
        create_forward_links = self.ext.getConfig('hyperlinks') in ['both', 'forward']
        
        for elem in root.iter(tag = 'cite'):
            key = elem.attrib['key']
            if key:
                del elem.attrib['key']
                label = entries[key].label
                n_citations[label] = n_citations.get(label, 0) + 1                    
                elem.attrib['id'] = f'pybtexcite:{label}-{n_citations[label]}'
                
                if create_forward_links:                    
                    elem.text = '['
                    link = ElementTree.SubElement(elem, 'a', attrib = {'href': f'#pybtexref:{label}'})
                    link.text = label
                    link.tail = ']'
                else:
                    elem.text = f'[{label}]'
                
            else:
                pass
                # TODO: insert error text explaining that 'key' was not a valid citekey.
                
        # TODO: we also want:
        # * hyperlinks (in both directions) between the citations and the reference entries
        # * hover popups (if possible; maybe just store the entry in the <cite> element's 'title' attribute?)
        # * configurable citation formats; e.g., as per the Latex natbib package.
              
        # Generate the full bibliography HTML
        biblio_html = io.StringIO()
        # pybtex.backends.html.Backend('utf-8').write_to_stream(formatted_biblio, biblio_html)
        ModifiedPybtexHtmlBackend().write_to_stream(formatted_biblio, biblio_html)
                
        # Parse the Pybtex-generated HTML using LXML (because the standard xml.etree API is not 
        # designed to parse HTML, and gets confused on '&nbsp;').
        biblio_tree = lxml.html.fromstring(biblio_html.getvalue())
        
        create_back_links = self.ext.getConfig('hyperlinks') in ['both', 'back']
        
        for dd in biblio_tree.iterfind('.//dd'):
            label = dd.attrib['label']
            del dd.attrib['label']
            
            if create_back_links:                
                if len(dd) == 0:
                    dd.text += ' '
                else:
                    dd[-1].tail += ' '
                
                n_cites = n_citations[label]
                if n_cites == 1:
                    back_link = lxml.etree.SubElement(dd, 'a', attrib = {'href': f'#pybtexcite:{label}-1'})
                    back_link.text = '↩'
                    
                else:
                    span = lxml.etree.SubElement(dd, 'span')
                    span.text = '↩ '
                    for i in range(1, n_cites + 1):
                        back_link = lxml.etree.SubElement(span, 'a', attrib = {'href': f'#pybtexcite:{label}-{i}'})
                        back_link.text = str(i)
                        back_link.tail = ' '
                        
        # Copy the LXML-parsed tree to the (standard) xml.etree structure used by Python-Markdown. 
        # AFAIK, there's no shortcut for this.
        def copy_tree(xml_tree_dest, lxml_tree_src):
            dest_element = ElementTree.SubElement(xml_tree_dest, 
                                                  lxml_tree_src.tag, 
                                                  dict(lxml_tree_src.attrib))
            dest_element.text = lxml_tree_src.text
            dest_element.tail = lxml_tree_src.tail
            for src_child in lxml_tree_src:
                copy_tree(dest_element, src_child)

        # Append <dl> element (the bibliography) to the root
        # TODO: we actually want to look for a placeholder to replace (and only append as a fallback).
        copy_tree(root, biblio_tree.find('.//dl'))
        
    
    
class PybtexExtension(markdown.Extension):
    def __init__(self, **kwargs):
        self.config = {
            # Todo: also allow embedded reference information, as a string in the build file.
            'file':       ['references.bib', 'A string, or list of strings, containing the filename(s) of Bibtex-formatted reference lists.'],
            'references': ['', 'A string directly containing a Bibtex-formatted reference list (or None).'],
            'encoding':   ['utf-8-sig', 'Encoding of the reference file.'],
            'format':     ['bibtex', '...'],
            'style':      ['unsrt', 'Reference style ("alpha", "plain", "unsrt", "unsrtalpha").'],
            'label_style': [None, '...'],
            'name_style':  [None, '...'],
            'sorting_style': [None, '...'],
            'abbreviate_names': [False, 'True/False...'],
            'min_crossrefs': [2, '...'],
            'hyperlinks': ['both', 'Must be "both" (the default), "forward", "back" or "none", indicating whether to create hyperlinks from citation to reference (forward/both) and from reference back to citation(s) (back/both).']
        }
        super().__init__(**kwargs)


    def extendMarkdown(self, md):
        
        cited_keys = []

        # The inline processor just replaces [@...] with <cite key="..." />, and gathers the set
        # of all cited keys.
        inline_proc = CitationInlineProcessor(cited_keys)
        md.inlinePatterns.register(inline_proc, 'lamarkdown.pybtex', 130)

        # The tree processor must come after the inline processor. Python-Markdown runs all inline
        # processors from within a TreeProcessor named InlineProcessor, with priority 20, so 
        # PybtexTreeProcessor must have lower priority than that.
        tree_proc = PybtexTreeProcessor(md, self, cited_keys)
        md.treeprocessors.register(tree_proc, 'lamarkdown.sections', 10)



def makeExtension(**kwargs):
    return PybtexExtension(**kwargs)

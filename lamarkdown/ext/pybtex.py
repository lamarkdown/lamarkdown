'''
# Pybtex Extension

'''

import markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import TreeProcessor

import pybtex

import io
import re
from xml.etree import ElementTree


class CitationInlineProcessor(InlineProcessor):
    REGEX = r'\[@([^]]+)\]'
    
    def __init__(self, cited_keys: set[str]):
        super().__init__(REGEX)
        self.cited_keys = cited_keys
        
    def handleMatch(self, match, data):
        key = match.group(1)
        cited_keys.add(key)
        elem = ElementTree.Element('cite')
        elem.attrib['key'] = key
        return elem, match.start(0), match.end(0)
        
        

class PybtexTreeProcessor(TreeProcessor):
    def __init__(self, md, cited_keys: set[str])
        super().__init__(md)
        
        # 'cited_keys' will be empty at first, but in between here and run() below, 
        # CitationInlineProcessor will add all citations found in the document.
        self.cited_keys = cited_keys
        
    def run(self, root):
        # 'cited_keys' will have been populated by now.
        
        file_spec = self.getConfig('file')
        if file_spec is None:
            files = []
        elif isinstance(file_spec, str):
            files = [file_spec]
        else:
            files = list(file_spec)
        
        ref_str = self.getConfig('references')
        if ref_str:
            files.append(io.StringIO(ref_str))
        
        bib_parser = pybtex.plugin.find_plugin('pybtex.database.input', self.getConfig('format'))
        bib_data = bib_parser(
            encoding = self.getConfig('encoding'),
            wanted_entries = self.cited_keys,
            min_crossrefs = self.getConfig('min_crossrefs')).parse_files(files)
        
        # TODO: handle errors from parse_files(): pybtex.database.BibliographyDataError and OSError
        
        style_cls = pybtex.plugin.find_plugin('pubtex.style.formatting', self.getConfig('style'))
        style = style_cls(
            label_style      = self.getConfig('label_style'),
            name_style       = self.getConfig('name_style'),
            sorting_style    = self.getConfig('sorting_style'),
            abbreviate_names = self.getConfig('abbreviate_names'),
            min_crossrefs    = self.getConfig('min_crossrefs')
        )
        formatted_biblio = style.format_bibliography(bib_data, self.cited_keys)
        
        # Populate the <cite> elements (created by CitationInlineProcessor) with the 'labels' 
        # created by Pybtex.
        entries = {entry.key: entry for entry in formatted_biblio.entries}
        for elem in root.iter(tag = 'cite'):
            key = elem.attrib['key']
            if key:
                del elem.attrib['key']
                elem.text = f'[{entries[key].label}]'
                
            else:
                pass
                # TODO: insert error text explaining that 'key' was not a valid citekey.
                
        # TODO: we also want:
        # * hyperlinks (in both directions) between the citations and the reference entries
        # * hover popups (if possible; maybe just store the entry in the <cite> element's 'title' attribute?)
        # * configurable citation formats; e.g., as per the Latex natbib package.
              
        # Generate the full bibliography HTML
        biblio_html = io.StringIO()
        pybtex.backends.html.Backend("utf-8").write_to_stream(formatted_biblio, biblio_html)

        # Parse bibliography HTML and append to the root
        # TODO: we actually want to look for a placeholder to replace (and only append as a fallback).
        root.append(ElementTree.parse(biblio_tree).getroot())
        
    
    
class PybtexExtension(markdown.Extension):
    def __init__(self, **kwargs):
        self.config = {
            # Todo: also allow embedded reference information, as a string in the build file.
            'file':       ['references.bib', 'A string, or list of strings, containing the filename(s) of Bibtex-formatted reference lists.'],
            'references': [None, 'A string directly containing a Bibtex-formatted reference list (or None).'],
            'encoding':   ['utf-8-sig', 'Encoding of the reference file.'],
            'format':     ['bibtex', '...'],
            'style':      ['unsrt', 'Reference style ("alpha", "plain", "unsrt", "unsrtalpha").'],
            'label_style': [None, '...'],
            'name_style':  [None, '...'],
            'sorting_style': [None, '...'],
            'abbreviate_names': [False, 'True/False...'],
            'min_crossrefs': [2, '...'],
        }
        super().__init__(**kwargs)


    def extendMarkdown(self, md):
        
        cited_keys = set()

        # The inline processor just replaces [@...] with <cite key="..." />, and gathers the set
        # of all cited keys.
        inline_proc = CitationInlineProcessor(all_references, cited_keys)
        md.inlinepatterns.register(inline_proc, 'lamarkdown.pybtex', 130)

        # The tree processor must come after the inline processor. Python-Markdown runs all inline
        # processors from within a TreeProcessor named InlineProcessor, with priority 20, so 
        # PybtexTreeProcessor must have lower priority than that.
        tree_proc = PybtexTreeProcessor(md, cited_keys)
        md.treeprocessors.register(tree_proc, 'lamarkdown.sections', 10)



def makeExtension(**kwargs):
    return PybtexExtension(**kwargs)

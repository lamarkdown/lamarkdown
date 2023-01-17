'''
# Pybtex Extension

'''
from lamarkdown.lib.progress import Progress

import markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor

import pybtex.backends.html
import pybtex.database
import pybtex.plugin
import pybtex.style.formatting

import lxml.html

import io
import os.path
import re
from typing import List
from xml.etree import ElementTree


class CitationInlineProcessor(InlineProcessor):
   
    # A citation syntactically consists of '[@' <citekey> [<extra>] ']'.
    # Where <citekey> is defined as per https://metacpan.org/dist/Text-BibTeX/view/btparse/doc/bt_language.pod
    # _except_ that '[' and ']' are invalid, since we use them to enclose a citation.
    #
    # <extra> is additional free-form text, starting with an invalid citekey character 
    # (such as ' ', ',' or '\'). This text will be added to the citation.
    
    #REGEX = '\\[@([^\x00-\x20 "#%\'(),=[\\]\\\\{}~]+)([^]]*)\\]'
    
    REGEX = '\\[@([a-zA-Z0-9!$&*+./:;<>?^_`|-]+)\\\\?([^]]*)\\]'
    
    def __init__(self, bib_data: pybtex.database.BibliographyData, 
                       cited_keys: List[str]):
        super().__init__(self.REGEX)
        self.bib_data = bib_data
        self.cited_keys = cited_keys
        
    def handleMatch(self, match, data):
        key = match.group(1)
        if key in self.bib_data.entries:
            extra = match.group(2)
            self.cited_keys.append(key)
            elem = ElementTree.Element('cite')
            elem.attrib['key'] = key
            elem.attrib['extra'] = extra
            return elem, match.start(0), match.end(0)
    
        else:
            # If the apparent citekey isn't in the reference database, then just leave everything
            # as it is. 
            return None, None, None
        
        
class ModifiedPybtexHtmlBackend(pybtex.backends.html.Backend):
    def __init__(self):
        super().__init__('utf-8')
        
    def write_entry(self, key, label, text):
        self.output(f'<dt id="pybtexref:{label}">{label}</dt>\n')
        self.output(f'<dd label="{label}">{text}</dd>\n')
        # Note: the 'label' attribute will be deleted later on. It's just here to help match up
        # this HTML (the reference) with its corresponding citations.
        

class PybtexTreeProcessor(Treeprocessor):
    def __init__(self, md, 
                       ext: 'PybtexExtension', 
                       bib_data: pybtex.database.BibliographyData,
                       bib_style: pybtex.style.formatting.BaseStyle,
                       cited_keys: List[str]):
        super().__init__(md)
        self.ext = ext
        self.bib_data = bib_data
        self.bib_style = bib_style
        
        # 'cited_keys' will be empty at first, but in between here and run() below, 
        # CitationInlineProcessor will add all citations found in the document.
        self.cited_keys = cited_keys
        
    def run(self, root):
        # 'cited_keys' should have been populated by now. If it's still empty, it means there are
        # no citations, and we can cut short the Treeprocessor:
        if len(self.cited_keys) == 0:
            return
        
        formatted_biblio = self.bib_style.format_bibliography(self.bib_data, self.cited_keys)
        
        # Populate the <cite> elements (created by CitationInlineProcessor) with the 'labels' 
        # created by Pybtex.
        entries = {entry.key: entry for entry in formatted_biblio.entries}
        n_citations = {}
        create_forward_links = self.ext.getConfig('hyperlinks') in ['both', 'forward']
        
        for elem in root.iter(tag = 'cite'):
            key = elem.attrib['key']
            extra = elem.attrib['extra']
            
            del elem.attrib['key']
            del elem.attrib['extra']
            
            label = entries[key].label
            n_citations[label] = n_citations.get(label, 0) + 1                    
            elem.attrib['id'] = f'pybtexcite:{label}-{n_citations[label]}'
            
            if create_forward_links:                    
                elem.text = '['
                link = ElementTree.SubElement(elem, 'a', attrib = {'href': f'#pybtexref:{label}'})
                link.text = label + extra
                link.tail = ']'
            else:
                elem.text = f'[{label + extra}]'
                                
        # TODO: we also want:
        # * hover popups (if possible; maybe just store the entry in the <cite> element's 'title' attribute?)
        # * configurable citation formats; e.g., as per the Latex natbib package.
              
        # Generate the full bibliography HTML
        biblio_html = io.StringIO()
        # pybtex.backends.html.Backend('utf-8').write_to_stream(formatted_biblio, biblio_html)
        ModifiedPybtexHtmlBackend().write_to_stream(formatted_biblio, biblio_html)
                
        # Parse the Pybtex-generated HTML using LXML (because the standard xml.etree API is not 
        # designed to parse HTML, and gets confused on '&nbsp;').
        biblio_tree = lxml.html.fromstring(biblio_html.getvalue())
        
        # Create back-links from references to their related citations.
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
                    back_link.tail = ''
                    
        # Determine where to put the bibliography -- the element containing the 'place_marker' 
        # text -- or (if not found) at the end of the document.
        placeholder = self.ext.getConfig('place_marker')
        def find_biblio_root(elem):
            if len(elem) == 0:
                if elem.text == placeholder:
                    return elem
            else:
                for child in elem:
                    found_elem = find_biblio_root(child)
                    if found_elem is not None:
                        return found_elem
            return None
        
        biblio_root = find_biblio_root(root)
        if biblio_root is None:
            biblio_root = ElementTree.SubElement(root, 'dl')            
        else:
            biblio_root.tag = 'dl'
            biblio_root.text = ''
                        
        # Copy the LXML-parsed tree to the (standard) xml.etree structure used by Python-Markdown. 
        # AFAIK, there's no shortcut for this.
        def copy_tree(xml_tree_dest, lxml_tree_src):
            for src_child in lxml_tree_src:
                dest_element = ElementTree.SubElement(xml_tree_dest, 
                                                      src_child.tag, 
                                                      dict(src_child.attrib))
                dest_element.text = src_child.text
                dest_element.tail = src_child.tail
                copy_tree(dest_element, src_child)

        copy_tree(biblio_root, biblio_tree.find('.//dl'))
        
        # Add <dl> element (the bibliography) to the root
        # TODO: we actually want to look for a placeholder to replace (and only append as a fallback).

    
class PybtexExtension(markdown.Extension):
    def __init__(self, **kwargs):
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass # Use default defaults

        progress = p.progress if p else Progress()
        
        self.config = {
            # Todo: also allow embedded reference information, as a string in the build file.
            'progress': [p.progress if p else Progress(), 'An object accepting progress messages.'],
            'file': [
                'references.bib', 
                'A string, or list of strings, containing the filename(s) of Bibtex-formatted reference lists.'
            ],
            'references': [
                '', 
                'A string directly containing a Bibtex-formatted reference list (or None).'
            ],
            'ignore_missing_file': [
                True, 
                'If True, missing reference files are ignored, rather than reported as errors.'
            ],
            'encoding': [
                'utf-8-sig', 
                'Encoding of the reference file.'
            ],
            'format': [
                'bibtex', 
                '...'
            ],
            'style': [
                'unsrt', 
                'Reference style ("alpha", "plain", "unsrt", "unsrtalpha").'
            ],
            'label_style': [
                None, 
                '...'
            ],
            'name_style': [
                None, 
                '...'
            ],
            'sorting_style': [
                None, 
                '...'
            ],
            'abbreviate_names': [
                False, 
                'True/False...'
            ],
            'min_crossrefs': [
                2, 
                '...'
            ],
            'place_marker': [
                '///References Go Here///', 
                'The text string marking where bibliography entries will be placed.'
            ],
            'hyperlinks': [
                'both', 
                'Must be "both" (the default), "forward", "back" or "none", indicating whether to create hyperlinks from citation to reference (forward/both) and from reference back to citation(s) (back/both).'
            ]
        }
        super().__init__(**kwargs)


    def extendMarkdown(self, md):
        
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
        
        # Pybtex reference database parser.
        bib_parser_cls = pybtex.plugin.find_plugin('pybtex.database.input', self.getConfig('format'))
        bib_parser = bib_parser_cls(
            encoding = self.getConfig('encoding'),
            min_crossrefs = self.getConfig('min_crossrefs'))
        
        # Parse files one by one.
        for file in files:
            if (self.getConfig('ignore_missing_file') 
                and isinstance(file, str)
                and not os.path.exists(file)):
                continue
            
            try:
                bib_parser.parse_file(file)                
            except Exception as e:
                self.getConfig('progress').error_from_exception('Pybtex', e)
                    
        # Pybtex formatter -- creates the document reference list.
        bib_style_cls = pybtex.plugin.find_plugin('pybtex.style.formatting', self.getConfig('style'))
        bib_style = bib_style_cls(
            label_style      = self.getConfig('label_style'),
            name_style       = self.getConfig('name_style'),
            sorting_style    = self.getConfig('sorting_style'),
            abbreviate_names = self.getConfig('abbreviate_names'),
            min_crossrefs    = self.getConfig('min_crossrefs')
        )
        
        cited_keys = []

        # The inline processor just replaces [@...] with <cite key="..." />, and gathers the set
        # of all cited keys.
        inline_proc = CitationInlineProcessor(bib_parser.data, cited_keys)
        md.inlinePatterns.register(inline_proc, 'lamarkdown.pybtex', 130)

        # The tree processor must come after the inline processor. Python-Markdown runs all inline
        # processors from within a TreeProcessor named InlineProcessor, with priority 20, so 
        # PybtexTreeProcessor must have lower priority than that.
        tree_proc = PybtexTreeProcessor(md, self, bib_parser.data, bib_style, cited_keys)
        md.treeprocessors.register(tree_proc, 'lamarkdown.sections', 10)



def makeExtension(**kwargs):
    return PybtexExtension(**kwargs)

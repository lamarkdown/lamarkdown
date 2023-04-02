'''
# Cite Extension

Allows embedding citations (e.g., [@author1990] or [see @author1; @author2; @{abc;def!}] ), which
are collected to generate a bibliography, based on an external database file.

We use the Pybtex package to read the database file(s) and format the bibliography.

'''

from lamarkdown.lib.progress import Progress

import markdown
from markdown.inlinepatterns import InlineProcessor
from markdown.preprocessors import Preprocessor
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

NAME = 'la.cite' # For progress/error messages


# TODO:
# * investigate https://github.com/brechtm/citeproc-py (a citation style language (CSL) processor)
#   - I think this is how we get long-form citations that specify the authors' names (similar to the Latex natbib package), and/or non-parenthetical references (the equivalent of \citet{...})
#   - It may also influence how/whether we integrate referencing into the footnote system



# A citation consists of '[...]' containing one or more citation keys (@xyz), at least one of
# which matches an entry in the reference database. There can be free-form text within the
# brackets, before, after and in-between citation keys.
#
# (In practice, most citations _probably_ contain just one citation key and no before/after
# text; e.g., [@author1990].)
#
# This is intended to be compatible (more-or-less) with the syntax used by Pandoc, and
# RMarkdown. (See https://pandoc.org/MANUAL.html#extension-citations.)
#
# Specifically, a citation key (starting after a @) can either:
# (a) consist of letters, digits and _, with selected other characters available as single-char
#     internal punctuation (e.g., '--' cannot be part of the key, nor can a key end with '.');
#     OR
# (b) be surrounded by braces (which are not part of the key), and contain any non-brace
#     characters as well as, optionally, matching pairs of braces (not nested braces though;
#     Pandoc may allow arbitrary nesting, but this seems a rarefied ability).

# (For reference, the BibTex format -- including allowed citation key characters -- is
# described here: https://metacpan.org/dist/Text-BibTeX/view/btparse/doc/bt_language.pod.
# However, I feel it's best to emulate Pandoc/RMarkdown for this purpose.)

CITE_REGEX = r'''
    (?<! \w ) # Require '@' to come after a non-word character, so as to avoid matching
              # things like me@example.com.
    @(
        (?P<simple_key> [a-zA-Z0-9_]+ ( [:.#$%&+?<>~/-] [a-zA-Z0-9_]+ )* )
        |
        \{ (?P<complex_key> [^{}]* ( \{ [^{}]* \} )* ) \}
    )
    (?P<post> [^]@]* )
'''

GROUP_REGEX = fr'''(?x)
    (?<! ! ) # The preceding character must not be '!', to avoid conflicts with the syntax for
             # embedding images.
    \[
    (?P<pre> [^]@]* )
    (?P<main> ({CITE_REGEX})+)
    \]
    (?! [\[(] ) # The trailing character must not be '(' or '[', to avoid conflicts with the
                # link syntax.
'''

CITE_REGEX_COMPILED = re.compile(f'(?x){CITE_REGEX}')


class MetadataPreprocessor(Preprocessor):
    """
    Handles directives in the document's metadata, specifically:
    'bibliography' -- specifies additional reference database files; and
    'nocite' -- lists references to be added to the bibliography regardless of whether they're
    actual cited in-text.
    """

    def __init__(self, md, ext, bib_parser, cited_keys: List[str]):
        super().__init__(md)
        self.ext = ext
        self.bib_parser = bib_parser
        self.cited_keys = cited_keys

    def run(self, lines):
        meta = self.md.__dict__.get('Meta', {})

        for filename in meta.get('bibliography', []):
            self.ext.getConfig('live_update_deps').add(filename)
            try:
                self.bib_parser.parse_file(filename)
            except Exception as e:
                self.ext.getConfig('progress').error(NAME, exception = e)

        for nocite in meta.get('nocite', []):
            if '@*' in nocite:
                # Wildcard specified; reference all entries.
                self.cited_keys.extend(self.bib_parser.data.entries.keys())
                break

            for cite_match in CITE_REGEX_COMPILED.finditer(nocite):
                key = cite_match.group('simple_key') or cite_match.group('complex_key')
                if key in self.bib_parser.data.entries:
                    self.cited_keys.append(key)

        return lines # Unmodified


class CitationInlineProcessor(InlineProcessor):
    def __init__(self, bib_parser, cited_keys: List[str]):
        super().__init__(GROUP_REGEX)
        self.bib_parser = bib_parser
        self.cited_keys = cited_keys


    def handleMatch(self, group_match, data):
        cite_elem = ElementTree.Element('cite')
        cite_elem.text = group_match.group('pre')

        def a1(text): cite_elem.text += text
        append_last = a1

        any_valid_citations = False
        for cite_match in CITE_REGEX_COMPILED.finditer(group_match.group('main')):
            key = cite_match.group('simple_key') or cite_match.group('complex_key')
            if key in self.bib_parser.data.entries:
                any_valid_citations = True
                self.cited_keys.append(key)
                span = ElementTree.SubElement(cite_elem, 'span')
                span.attrib['key'] = key
                span.tail = cite_match.group('post')

                def a2(text): span.tail += text
                append_last = a2

            else:
                append_last(cite_match.group())

        if any_valid_citations:
            return cite_elem, group_match.start(), group_match.end()

        else:
            return None, None, None


class ModifiedPybtexHtmlBackend(pybtex.backends.html.Backend):
    def __init__(self):
        super().__init__('utf-8')

    def write_entry(self, key, label, text):
        self.output(f'<dt id="la-ref:{label}">{label}</dt>\n')
        self.output(f'<dd label="{label}">{text}</dd>\n')
        # Note: the 'label' attribute will be deleted later on. It's just here to help match up
        # this HTML (the reference) with its corresponding citations.


class PybtexTreeProcessor(Treeprocessor):
    def __init__(self, md,
                       ext: 'PybtexExtension',
                       bib_parser,
                       bib_style: pybtex.style.formatting.BaseStyle,
                       cited_keys: List[str]):
        super().__init__(md)
        self.ext = ext

        # It's really just bib_parser.data that we want, but since BibliographyFilePreprocessor
        # may add/change the data between here and run() below, it seems safer to pass the parser
        # itself.
        self.bib_parser = bib_parser

        self.bib_style = bib_style

        # 'cited_keys' will be empty at first, but in between here and run() below,
        # CitationInlineProcessor will add all citations found in the document.
        self.cited_keys = cited_keys

    def run(self, root):
        progress = self.ext.getConfig('progress')

        # 'cited_keys' should have been populated by now. If it's still empty, it means there are
        # no citations, and we can cut short the Treeprocessor:
        if len(self.cited_keys) == 0:
            return

        try:
            formatted_biblio = self.bib_style.format_bibliography(self.bib_parser.data,
                                                                  self.cited_keys)
        except pybtex.exceptions.PybtexError as e:
            progress.error(NAME, str(e))
            return

        progress.progress(NAME, msg = f'{len(self.cited_keys)} citation(s)')

        # Populate the <cite> elements (created by CitationInlineProcessor) with the 'labels'
        # created by Pybtex, and 'id' and 'href' attributes to assist linking.
        entries = {entry.key: entry for entry in formatted_biblio.entries}
        n_citations = {}
        create_forward_links = self.ext.getConfig('hyperlinks') in ['both', 'forward']

        for elem in root.iter(tag = 'cite'):
            for child in elem:
                key = child.attrib.get('key')
                if child.tag == 'span' and key is not None:
                    del child.attrib['key']

                    label = entries[key].label
                    n_citations[label] = n_citations.get(label, 0) + 1
                    child.attrib['id'] = f'la-cite:{label}-{n_citations[label]}'
                    child.text = label

                    if create_forward_links:
                        child.tag = 'a'
                        child.attrib['href'] = f'#la-ref:{label}'

            elem.text = f'[{elem.text}'
            elem[-1].tail += ']'


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

            n_cites = n_citations.get(label, 0)
            if create_back_links and n_cites > 0:
                # (a) Even if create_back_links == False, we must still 'del' the label attribute.
                # (b) There could be 0 citations, if the reference was provided via 'nocite'. Only
                #     add links if there are citations.

                if len(dd) == 0:
                    dd.text += ' '
                else:
                    dd[-1].tail += ' '

                if n_cites == 1:
                    back_link = lxml.etree.SubElement(dd, 'a', attrib = {'href': f'#la-cite:{label}-1'})
                    back_link.text = '↩'

                else:
                    span = lxml.etree.SubElement(dd, 'span')
                    span.text = '↩ '
                    for i in range(1, n_cites + 1):
                        back_link = lxml.etree.SubElement(span, 'a', attrib = {'href': f'#la-cite:{label}-{i}'})
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

                dest_element.text = (src_child.text or '').replace('\n', ' ')
                dest_element.tail = (src_child.tail or '').replace('\n', ' ')
                copy_tree(dest_element, src_child)

                # Note: replacing '\n' avoids the 'nl2br' extension (if loaded) putting <br> tags
                # everywhere.


        copy_tree(biblio_root, biblio_tree.find('.//dl'))
        biblio_root.attrib['id'] = 'la-bibliography'

        # Finally, run Python Markdown's inline processors across the new sub-tree. These handle
        # things like formatting (e.g., _emph_) and links (e.g., [Example](http://example.com)).
        #
        # We're constrained to run this TreeProcessor *after* the normal inline processors (because
        # CitationInlineProcessor must run first to finds all the citations). So we need to run
        # the inline processors again, on just the reference list produced by Pybtex.
        #
        # Otherwise, we won't wouldn't be able to use normal markdown syntax inside the reference
        # list, and this would prevent sensible handling of URLs.
        markdown.treeprocessors.InlineProcessor(self.md).run(biblio_root)



class CiteExtension(markdown.Extension):
    def __init__(self, **kwargs):
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass # Use default defaults

        progress = p.progress if p else Progress()
        live_update_deps = p.live_update_deps if p else set()

        self.config = {
            'progress': [
                p.progress if p else Progress(),
                'An object accepting progress messages.'
            ],
            'live_update_deps': [
                p.live_update_deps if p else set(),
                'An updatable set of files that should be monitored for changes during live updating.'
            ],
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
                'Overall style ("alpha", "plain", "unsrt", "unsrtalpha").'
            ],
            'label_style': [
                '',
                '"" (default), "alpha" or "number".'
            ],
            'name_style': [
                '',
                '"" (default), "lastfirst" or "plain".'
            ],
            'sorting_style': [
                '',
                '"" (default), "author_year_title" or "none".'
            ],
            'abbreviate_names': [
                False,
                'If True, use initials for first/middle names. If False (default), use full names.'
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

        self.getConfig('live_update_deps').update(files)

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
                self.getConfig('progress').error(NAME, exception = e)

        # Pybtex formatter -- creates the document reference list.
        bib_style_cls = pybtex.plugin.find_plugin('pybtex.style.formatting', self.getConfig('style'))
        bib_style = bib_style_cls(
            label_style      = self.getConfig('label_style') or None,
            name_style       = self.getConfig('name_style') or None,
            sorting_style    = self.getConfig('sorting_style') or None,
            abbreviate_names = self.getConfig('abbreviate_names'),
            min_crossrefs    = self.getConfig('min_crossrefs')
        )

        cited_keys = []

        # The pre-processor handles additional directives given in the document metadata. Since
        # it's another extension's preprocessor ('meta') that _parses_ the metadata, our
        # preprocessor must run with a lower priority (than 27).
        pre_proc = MetadataPreprocessor(md, self, bib_parser, cited_keys)
        md.preprocessors.register(pre_proc, 'la-cite-pre', -10)

        # The inline processor identifies citations, creates tree nodes to keep track of them
        # (with details to be filled in later), and gathers the set of all cited keys.
        inline_proc = CitationInlineProcessor(bib_parser, cited_keys)
        md.inlinePatterns.register(inline_proc, 'la-cite-inline', 130)

        # The tree processor must run _after_ the inline processor. Python-Markdown runs all inline
        # processors from within a TreeProcessor named InlineProcessor, with priority 20, so
        # PybtexTreeProcessor must have lower priority than that.
        tree_proc = PybtexTreeProcessor(md, self, bib_parser, bib_style, cited_keys)
        md.treeprocessors.register(tree_proc, 'la-cite-tree', 10)



def makeExtension(**kwargs):
    return CiteExtension(**kwargs)

'''
# Latex Extension

The 'latex' extension lets uses write Latex code inside a .md file, which will be compiled,
converted to SVG, and embedded in the output HTML.

The user must write the Latex code starting on a new line, and can either:

(a) Write a complete Latex document, which must begin with '\\documentclass' and end with
    '\\end{document}';

(b) Write a cut-down form, which must:

    * Begin with '\\usepackage', '\\usetikzlibrary' or '\\begin{<name>}';
    * Contain '\\begin{<name>}' (if it didn't start with it); and
    * End with '\\end{<name>}'.

    The extension prepends an implied '\\documentclass'. If <name> is not 'document', then the
    extension also adds in '\\begin{document}...\\end{document}'.

There are various configuration options, allowing a choice of Latex compiler, PDF-to-SVG converter,
method of embedding SVG, optional common Latex code to be inserted after '\\documentclass', etc.
'''

from lamarkdown.lib.progress import Progress, ErrorMsg, ProgressMsg

from markdown import *
from markdown.extensions import *
from markdown.extensions.attr_list import AttrListTreeprocessor
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor
from markdown.util import AtomicString

import base64
import copy
import glob
import hashlib
import os
import re
import subprocess
import time
from typing import Dict, List, Union
from xml.etree import ElementTree


class CommandException(Exception):
    def __init__(self, msg: str, output: str):
        super().__init__(msg)
        self.output = output

class SyntaxException(Exception): pass

def check_run(command: Union[str,List[str]],
              expected_output_file: str,
              **kwargs):
    start_time = time.time_ns()
    command_str = ' '.join(command) if isinstance(command, list) else command

    proc = subprocess.run(command,
                          shell = isinstance(command, str),
                          stdin = subprocess.DEVNULL, # Supposed to be non-interactive!
                          stdout = subprocess.PIPE,
                          stderr = subprocess.STDOUT,
                          encoding = 'utf-8',
                          **kwargs)
    if proc.returncode != 0:
        raise CommandException(
            f'"{command_str}" returned error code {proc.returncode}',
            proc.stdout)

    try:
        file_time = os.stat(expected_output_file).st_mtime_ns
    except OSError:
        file_time = 0

    if file_time < start_time:
        raise CommandException(
            f'"{command_str}" did not create expected file "{expected_output_file}"',
            proc.stdout)


def get_blocks(blocks):
    while blocks:
        yield blocks.pop(0)


class Embedder:
    def generate_html(self, svg_content: str) -> ElementTree.Element: raise NotImplementedError


class DataUriEmbedder(Embedder):
    def generate_html(self, svg_content: str) -> ElementTree.Element:
        # Encode SVG data as a data URI in an <img> element.
        data_uri = f'data:image/svg+xml;base64,{base64.b64encode(svg_content.strip().encode()).decode()}'
        return ElementTree.fromstring(f'<img src="{data_uri}" />')


class SvgElementEmbedder(Embedder):
    def __init__(self):
        self.svg_index = 0

    def generate_html(self, svg_content: str) -> ElementTree.Element:
        svg_element = ElementTree.fromstring(svg_content)
        self._mangle(svg_element)
        self.svg_index += 1
        return svg_element

    def _mangle(self, elem: ElementTree.Element):
        # First, strip ElementTree namespaces
        if elem.tag.startswith('{'):
            elem.tag = elem.tag.split('}', 1)[1]

        key_set = set(elem.attrib.keys())
        for key in key_set:
            if key.startswith('{'):
                elem.attrib[key.split('}', 1)[1]] = elem.attrib[key]
                del elem.attrib[key]

        # Second, wrap all text in AtomicString (to prevent other markdown processors getting to it)
        if elem.text:
            elem.text = AtomicString(elem.text)

        if elem.tail:
            elem.tail = AtomicString(elem.tail)

        # Third, prepend the SVG index to every "id" we can find (to keep them separate from other SVGs that might share the same namespace.
        id = elem.attrib.get('id')
        href = elem.attrib.get('href')

        if id:
            elem.attrib['id'] = f'i{self.svg_index}_{id}'

        if href and href[0] == '#':
            elem.attrib['href'] = f'#i{self.svg_index}_{href[1:]}'

        for child in elem:
            self._mangle(child)


STX = '\u0002'
ETX = '\u0003'
LATEX_PLACEHOLDER_PREFIX = f'{STX}lamdlatex-uoqwpkayei:'
LATEX_PLACEHOLDER_RE     = re.compile(f'{LATEX_PLACEHOLDER_PREFIX}(?P<id>[0-9]+){ETX}')

HTML_COMMENT_RE = re.compile(r'<!--.*?(-->|$)', flags = re.DOTALL)


class LatexPreprocessor(Preprocessor):
    """
    The preprocessor is responsible for identifying and parsing Latex snippets found in the
    document. Each one is temporarily replaced by a placeholder, with the actual Latex code held
    separately in 'latex_docs', awaiting the postprocessor.

    (Previously, in commit 18fc579db4b4793a50ed077e369aa14e276ee189 and earlier, lamarkdown used a
    one-stage process, where a BlockProcessor would identify, parse, compile and embed each Latex
    snippet. This approach encountered some minor but unfortunate limitations; e.g., when placed
    inside a markdown list, the Latex code was prohibited from containing blank lines, because the
    block processor only saw one block at a time.)
    """


    TEX_END_UNCOMMENTED = r'''
        (                       # Our snippet of tex code must be:
            [^%\n]*?            # (a) a single line with no comments, OR
            | .*? \n [^%\n]*?   # (b) anything, but ending with a non-commented newline.
        )                       # (Match non-greedily, or else we won't know where to end.)
    '''

    ATTR = r'''
        (
            \n[ \t]*                # Start on a new line
            \{\:?[ ]*               # Starts with '{' or '{:' (with optional spaces)
            (?P<attr>
                [^\}\n ][^\}\n]*    # No '}' or newlines, and at least one non-space char.
            )?
            [ ]*\}                  # Ends with '}' (with optional spaces)
        )?
    '''

    TEX_RE = re.compile(
        fr'''
        ^ (?P<indent> [ \t]* )          # Start on a new line; preserve indent
        (
            (?P<doc>                    # Full document syntax
                (?P<docclass>
                    \\documentclass
                    \{{ [^}}]+ \}}
                )
                {TEX_END_UNCOMMENTED}
                \\end\{{document}}
            )
            |
            (?P<preamble>               # OR, short-cut syntax, starting with optional preamble...
                \\
                (
                    usepackage          # Preamble begins with one of these
                    | usetikzlibrary
                )
                {TEX_END_UNCOMMENTED}
            )?
            (?P<main>
                \\begin\{{              # Start of the main environment
                    (?P<env>[^}}]+)      # Capture the environment name
                \}}
                {TEX_END_UNCOMMENTED}
                \\end\{{                # End of main environment
                    (?P=env)            # Match previous name
                \}}
            )
        )
        [ \t]* (%[^\n]*)?   # Ends with whitespace, then an optional comment
        {ATTR}
        ''',
        re.VERBOSE | re.DOTALL | re.MULTILINE)


    def __init__(self, prepend: str, doc_class: str, doc_class_options: str, strip_html_comments: bool):
        self.prepend = prepend
        self.doc_class = doc_class
        self.doc_class_options = doc_class_options
        self.strip_html_comments = strip_html_comments


    def _format_latex(self, match_obj):
        self.match_instance += 1

        full_doc = match_obj.group('doc')
        if full_doc:
            if self.prepend:
                split = match_obj.end('docclass') - match.start()
                full_doc = f'{full_doc[:split]}\n{self.prepend}{full_doc[split:]}'
            else:
                pass

        else:
            main_part = match_obj.group('main')
            if match_obj.group('env') != 'document':
                main_part = fr'\begin{{document}}{main_part}\end{{document}}'

            full_doc = (
                f'\\documentclass[{self.doc_class_options}]{{{self.doc_class}}}\n'
                + '\\usepackage{tikz}\n'
                + (self.prepend or "")
                + (match_obj.group('preamble') or "")
                + (main_part)
            )

        self._latex_docs[self.match_instance] = full_doc
        self._latex_attrs[self.match_instance] = match_obj.group('attr')

        return f'{LATEX_PLACEHOLDER_PREFIX}{self.match_instance}{ETX}'


    def run(self, lines):
        self.match_instance = 0
        self._latex_docs = {}
        self._latex_attrs = {}

        raw_text = '\n'.join(lines)
        search_text = raw_text
        if self.strip_html_comments:
            # Blank-out HTML comments.
            search_text = HTML_COMMENT_RE.sub(
                lambda match: ' ' * len(match.group(0)),
                search_text)
            assert len(raw_text) == len(search_text)

        # Here we do a bit of a dance, where we're *searching* one set of text, normally with HTML
        # comments stripped, but we're making string substitutions (replacing the Latex code with
        # placeholders) on the *original* text.
        #
        # The Latex code itself is now stripped of HTML comments (if that option is set), but the
        # rest of the original text will retain them, and any commented-out Latex code will also be
        # retained verbatim.
        #
        # (If the user wants to strip HTML comments *in general* from the document, this is left as
        # an exercise for another component.)
        return_text = []
        last_match_end = 0
        for match in self.TEX_RE.finditer(search_text):
            match_start = match.start()

            if last_match_end < match_start:
                # Some intervening, non-Latex text. Accumulate it in return_text.
                return_text.append(raw_text[last_match_end:match_start])

            # Accumulate the placeholder text in return_text.
            return_text.append(match['indent'])
            return_text.append(self._format_latex(match))
            last_match_end = match.end()

        # Add any trailing non-Latex text.
        if last_match_end < len(raw_text):
            return_text.append(raw_text[last_match_end:])

        # Join all the fragments together, and then split them back into lines, as required by
        # contract.
        return ''.join(return_text).split('\n')

    @property
    def latex_docs(self): return self._latex_docs

    @property
    def latex_attrs(self): return self._latex_attrs

    @property
    def input_repr(self): return (self.prepend, self.doc_class, self.doc_class_options, self.strip_html_comments)


class LatexPostprocessor(Postprocessor):
    """
    The post-processor is responsible for compiling the Latex code identified by the preprocessor,
    converting it to SVG, caching the result, and embedding it the final HTML. It searches for the
    placeholder strings inserted by the preprocessor to determine where to substitute the proper
    HTML.
    """

    #cache: Dict[str,ElementTree.Element] = {}
    CACHE_PREFIX = 'lamarkdown.latex'

    TEX_CMDLINES = {
        'pdflatex': ['pdflatex', '-interaction', 'nonstopmode', 'job'],
        'xelatex':  ['xelatex', '-interaction', 'nonstopmode', 'job'],
    }

    CONVERTER_CMDLINES = {
        'dvisvgm': ['dvisvgm', '--pdf', 'job.pdf'],
        'pdf2svg': ['pdf2svg', 'job.pdf', 'job.svg'],
        'inkscape': ['inkscape', '--pdf-poppler', 'job.pdf', '-o', 'job.svg'],
    }

    EMBEDDERS = {
        'data_uri': DataUriEmbedder,
        'svg_element': SvgElementEmbedder
    }

    def __init__(self, md, preproc: LatexPreprocessor, build_dir: str, cache, progress: Progress,
                 tex: str, pdf_svg_converter: str, embedding: str, strip_html_comments: bool):
        self.md = md
        self.preproc = preproc
        self.build_dir = build_dir
        self.cache = cache
        self.progress = progress

        self.tex_cmdline: Union[List[str],str] = (
            self.TEX_CMDLINES.get(tex) or
            tex.replace('in.tex', 'job.tex').replace('out.pdf', 'job.pdf')
        )

        self.converter_cmdline: Union[List[str],str] = (
            self.CONVERTER_CMDLINES.get(pdf_svg_converter) or
            pdf_svg_converter.replace('in.pdf', 'job.pdf').replace('out.svg', 'job.svg')
        )

        self.embedding = embedding
        self.embedder = self.EMBEDDERS[self.embedding]()

        self.strip_html_comments = strip_html_comments


    def _build(self, latex, attrs):
        # Run Python Markdown's postprocessors.

        # This is important, because Markdown's _pre_processors replace certain constructs,
        # particularly HTML snippets, with special placeholders, which are again replaced by
        # postprocessors once all the block processing and tree manipulation is done.
        #
        # This is exactly what LatexPreprocessor and LatexPostprocessor do themselves, but now
        # we must invoke the _other_ postprocessors too.
        for post_proc in self.md.postprocessors:
            if post_proc != self:
                latex = post_proc.run(latex)

        # Having done this, we now (again) need to strip out HTML comments, because these (in
        # certain circumstances) are given the preprocessor-postprocessor treatment by Python
        # Markdown, and so might not have been removed by _our_ preprocessor.
        if self.strip_html_comments:
            latex = HTML_COMMENT_RE.sub('', latex)

        # Build a representation of all the input information sources.
        cache_key = (self.CACHE_PREFIX, latex, self.preproc.input_repr,
                      self.tex_cmdline, self.converter_cmdline, self.embedding)

        # If not in cache, compile it.
        if cache_key in self.cache:
            self.progress.progress('Latex', 'Cache hit -- skipping compilation')

        else:
            hasher = hashlib.sha1()
            hasher.update(latex.encode('utf-8'))
            file_build_dir = os.path.join(self.build_dir, 'latex-' + hasher.hexdigest())
            os.makedirs(file_build_dir, exist_ok=True)

            tex_file = os.path.join(file_build_dir, 'job.tex')
            pdf_file = os.path.join(file_build_dir, 'job.pdf')
            svg_file = os.path.join(file_build_dir, 'job.svg')

            try:
                with open(tex_file, 'w') as f:
                    f.write(latex)

            except OSError as e:
                return self.progress.error_from_exception('Latex', e).as_html_str()

            try:
                self.progress.progress(self.tex_cmdline[0], 'Compiling .tex to .pdf...')
                check_run(
                    self.tex_cmdline,
                    pdf_file,
                    cwd = file_build_dir,
                    env = {**os.environ, "TEXINPUTS": f'.:{os.getcwd()}:'}
                )

                self.progress.progress(self.converter_cmdline[0], 'Converting .pdf to .svg...')
                check_run(
                    self.converter_cmdline,
                    svg_file,
                    cwd = file_build_dir
                )

                with open(svg_file) as reader:
                    svg_content = reader.read()
                    if "viewBox='0 0 0 0'" in svg_content:
                        return self.progress.error(
                            'Latex',
                            f'Resulting SVG code is empty -- either {self.tex_cmdline[0]} or {self.converter_cmdline[0]} failed',
                            svg_content
                        ).as_html_str()

                # If compilation was successful, cache the result.
                self.cache[cache_key] = self.embedder.generate_html(svg_content)

            except CommandException as e:
                return self.progress.error('Latex', str(e), e.output, latex).as_html_str()

        # We make a copy of the cached element, because different instances of it could
        # conceivably be assigned different attributes below.
        element = copy.copy(self.cache.get(cache_key))

        if attrs:
            # Hijack parts of the attr_list extension to handle the attribute list.
            #
            # (Warning: there is a risk here that a future version of Markdown will change
            # the design of attr_list, such that this call doesn't work anymore. For now, it
            # seems the easiest and most consistent way to go.)
            AttrListTreeprocessor().assign_attrs(element, attrs)

        return ElementTree.tostring(element, encoding = 'unicode')



    def run(self, text):
        html = {}
        # Build all the Latex!
        for i, latex in self.preproc.latex_docs.items():
            html[i] = self._build(latex, self.preproc.latex_attrs[i])

        # Substitute the HTML back into the document
        return LATEX_PLACEHOLDER_RE.sub(
            lambda match: html[int(match.group('id'))],
            text)

    def reset(self):
        self.embedder = self.EMBEDDERS[self.embedding]()


class LatexExtension(Extension):
    def __init__(self, **kwargs):
        # Try to get some objects from the current build parameters:
        # (1) the build dir -- the location where we'll execute latex, and where all its
        #     temporary files will accumulate;
        # (2) the global cache -- allowing us to avoid re-compiling when the Latex code hasn't
        #     changed.
        #
        # This will only work if this extension is being used within the context of lamarkdown.
        # But we do have a fallback on the off-chance that someone wants to use it elsewhere.
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass # Use default defaults

        progress = p.progress if p else Progress()

        self.config = {
            'build_dir': [p.build_dir if p else 'build',    'Location to write temporary files'],
            'cache':     [p.cache     if p else {},         'A dictionary-like cache object to help avoid unnecessary rebuilds.'],
            'progress':  [p.progress  if p else Progress(), 'An object accepting progress messages.'],
            'tex': [
                'xelatex',
                'Program used to compile .tex files to PDF files. Generally, this should be a complete command-line containing the strings "in.tex" and "out.pdf" (which will be replaced with the real names as needed). However, it can also be simply "pdflatex" or "xelatex", in which case pre-defined command-lines for those commands will be used.'
            ],
            'pdf_svg_converter': [
                'dvisvgm',
                'Program used to convert PDF files (produced by Tex) to SVG files to be embedded in the HTML output. Generally, this should be a complete command-line containing the strings "in.pdf" and "out.svg" (which will be replaced with the real names as needed). However, it can also be simply  "dvisvgm", "pdf2svg" or "inkscape", in which case pre-defined command-lines for those commands will be used.'
            ],
            'embedding': [
                'data_uri',
                'Either "data_uri" or "svg_element", specifying how the SVG data will be attached to the HTML document.'
            ],
            'prepend': [
                '',
                'Extra Tex code to be added to the front of each Tex snippet.'
            ],
            'doc_class': [
                'standalone',
                'The Latex document class to use, when not explicitly given.'
            ],
            'doc_class_options': [
                '',
                'Options provided to the Latex document class, as a single string.'
            ],
            'strip_html_comments': [
                True,
                r'Considers "<!--...-->" to be a comment, and removes them before compiling with Latex. Latex would (in most cases) interpret these sequences as ordinary characters, whereas in markdown they would normally be (effectively) ignored. If you need to write a literal "<!--", you can do so by inserting "{}" between the characters. (This option does not affect normal Tex "%" comments.)'
            ]
        }
        super().__init__(**kwargs)

        embedding = self.getConfig('embedding')
        if embedding not in LatexPostprocessor.EMBEDDERS:
            progress.error('latex', f'Invalid value "{embedding}" for config option "embedding"')
            self.setConfig('embedding', 'data_uri')

    def reset(self):
        self.postprocessor.reset()

    def extendMarkdown(self, md):
        md.registerExtension(self)

        self.preprocessor = LatexPreprocessor(
            prepend             = self.getConfig('prepend'),
            doc_class           = self.getConfig('doc_class'),
            doc_class_options   = self.getConfig('doc_class_options'),
            strip_html_comments = self.getConfig('strip_html_comments'),
        )

        self.postprocessor = LatexPostprocessor(
            md,
            self.preprocessor,
            build_dir           = self.getConfig('build_dir'),
            cache               = self.getConfig('cache'),
            progress            = self.getConfig('progress'),
            tex                 = self.getConfig('tex'),
            pdf_svg_converter   = self.getConfig('pdf_svg_converter'),
            embedding           = self.getConfig('embedding'),
            strip_html_comments = self.getConfig('strip_html_comments'),
        )

        md.preprocessors.register(self.preprocessor, 'latex-pre', 15)
        md.postprocessors.register(self.postprocessor, 'latex-post', 25)



def makeExtension(**kwargs):
    return LatexExtension(**kwargs)

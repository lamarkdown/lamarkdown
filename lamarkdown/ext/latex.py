'''
# Latex Extension

The 'la.latex' extension lets you write Latex code inside a .md file. This works in two ways:

(1) Inclusion of an entire Latex document or environment (e.g., to create a PGF/Tikz image).

    Such code will be compiled with an external Latex command, converted to SVG, and embedded in the
    output HTML. The Latex code must start on a new line, and can either:

    (a) Be a complete Latex document, which must begin with '\\documentclass' and end with
        '\\end{document}';

    (b) Be a cut-down form, which must:

        * Begin with '\\usepackage', '\\usetikzlibrary' or '\\begin{<name>}';
        * Contain '\\begin{<name>}' (if it didn't start with it); and
        * End with '\\end{<name>}'.

        The extension prepends an implied '\\documentclass'. If <name> is not 'document', then the
        extension also adds in '\\begin{document}...\\end{document}'.

    There are various configuration options, allowing a choice of Latex compiler, PDF-to-SVG
    converter, method of embedding SVG, optional common Latex code to be inserted after
    '\\documentclass', etc.


(2) Using $...$ and $$...$$ for Latex math code, at any point within a paragraph (except inside
    `...`).

    By default (or if math="mathml"), latex2mathml is used to produce MathML code, which is
    included directly in the output document.

    If math="latex", then math code will instead be compiled and converted the same way as in (1),
    just in math mode.

    Processing of math code can also be turned off with math="ignore" (either to restore the literal
    meaning of '$', or to use an alternate math code processor like pymdownx.arithmatex).
'''


from lamarkdown.lib.progress import Progress, ErrorMsg, ProgressMsg

from markdown import *
from markdown.extensions import *
from markdown.extensions.attr_list import AttrListTreeprocessor
from markdown.preprocessors import Preprocessor
from markdown.inlinepatterns import InlineProcessor
from markdown.postprocessors import Postprocessor
from markdown.util import AtomicString

import latex2mathml.converter

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


def coerce_subtree(elem: ElementTree.Element):
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

    for child in elem:
        coerce_subtree(child)



class Embedder:
    def generate_html(self, svg_content: str) -> ElementTree.Element: raise NotImplementedError


class DataUriEmbedder(Embedder):
    def generate_html(self, svg_content: str) -> ElementTree.Element:
        # Encode SVG data as a data URI in an <img> element.
        data_uri = f'data:image/svg+xml;base64,{base64.b64encode(svg_content.strip().encode()).decode()}'
        return ElementTree.fromstring(f'<img src="{data_uri}" />')


class SvgElementEmbedder(Embedder):
    def generate_html(self, svg_content: str) -> ElementTree.Element:
        svg_element = ElementTree.fromstring(svg_content)
        coerce_subtree(svg_element)
        return svg_element



STX = '\u0002'
ETX = '\u0003'
LATEX_PLACEHOLDER_PREFIX = f'{STX}lamdlatex-uoqwpkayei:'
LATEX_PLACEHOLDER_RE     = re.compile(f'{LATEX_PLACEHOLDER_PREFIX}(?P<id>[0-9]+){ETX}')

HTML_COMMENT_RE = re.compile(r'<!--.*?(-->|$)', flags = re.DOTALL)

ATTR = r'''
    \{\:?[ ]*               # Starts with '{' or '{:' (with optional spaces)
    (?P<attr>
        [^\}\n ][^\}\n]*    # No '}' or newlines, and at least one non-space char.
    )?
    [ ]*\}                  # Ends with '}' (with optional spaces)
'''


class LatexStash:
    def __init__(self, input_repr):
        assert isinstance(input_repr, tuple)

        self._match_instance = 0
        self._latex_docs = {}
        self._latex_attrs = {}
        self._input_repr = input_repr

    @property
    def latex_docs(self): return self._latex_docs

    @property
    def latex_attrs(self): return self._latex_attrs

    @property
    def input_repr(self): return self._input_repr

    def stash(self, full_doc: str, attr: dict[str,str]):
        self._match_instance += 1
        self._latex_docs[self._match_instance] = full_doc
        self._latex_attrs[self._match_instance] = attr
        return f'{LATEX_PLACEHOLDER_PREFIX}{self._match_instance}{ETX}'



class LatexPreprocessor(Preprocessor):
    """
    The preprocessor identifies and parses Latex block snippets found in the document. Each one is
    temporarily replaced by a placeholder, with the actual Latex code held separately in the
    'stash', awaiting the postprocessor.

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
        (
            \n[ \t]*        # Start attributes (if any) on a new line
            {ATTR}
        )?
        ''',
        re.VERBOSE | re.DOTALL | re.MULTILINE)


    def __init__(self, stash: LatexStash, prepend: str, doc_class: str, doc_class_options: str, strip_html_comments: bool):
        self.stash = stash
        self.prepend = prepend
        self.doc_class = doc_class
        self.doc_class_options = doc_class_options
        self.strip_html_comments = strip_html_comments


    def _format_latex(self, match_obj):
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

        return self.stash.stash(full_doc, match_obj.group('attr'))


    def run(self, lines):
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



class EscapeInlineProcessor(InlineProcessor):
    """
    Handles escaping of the '$' sign used for math code. Latex(MathML)InlineProcessor must run
    _before_ the standard EscapeInlineProcessor, because we can't have the latter messing with our
    Latex code (which generally contains lots of backslashes). But that means we have to do our own
    escaping.
    """

    def __init__(self, md):
        super().__init__(r'(?<!\\)((\\\\)*)\\\$', md)

    def handleMatch(self, match, data):
        return '\\' * (len(match.group(1)) // 2) + '$', match.start(0), match.end(0)



MATH_TEX_RE = rf'''(?xs)
    (
        \$\$
        (?P<latex_block>
            [^$]+
        )
        \$\$
        |
        \$
        (?P<latex_inline>
            [^\s$]
            (
                [^$]*
                [^\s$]
            )?
        )
        \$
    )
    ({ATTR})?
'''


class LatexInlineProcessor(InlineProcessor):
    """
    This inline processor identifies and parses Latex math snippets. Each one is temporarily
    replaced by a placeholder, with the actual Latex code held separately in the 'stash', awaiting
    the postprocessor.
    """

    def __init__(self, md, stash, prepend: str, doc_class: str, doc_class_options: str):
        super().__init__(MATH_TEX_RE, md)
        self.stash = stash
        self.prepend = prepend
        self.doc_class = doc_class
        self.doc_class_options = doc_class_options


    def handleMatch(self, match, data):

        latex_inline = match.group('latex_inline')
        latex_block = match.group('latex_block')

        display_cmd = r'\displaystyle{}' if latex_block else ''
        full_doc = rf'''
            \documentclass[{self.doc_class_options}]{{{self.doc_class}}}
            \usepackage{{tikz}}
            \usepackage{{amsmath}}
            {self.prepend or ''}
            \begin{{document}}
                ${display_cmd}{latex_inline or latex_block}$
            \end{{document}}
        '''

        element = ElementTree.Element('span', attrib = {'class': 'la-math'})
        element.text = self.stash.stash(full_doc, match.group('attr'))

        return element, match.start(0), match.end(0)


class LatexMathMLInlineProcessor(InlineProcessor):
    """
    This inline processor also identifies and parses Latex math snippets. For each one, we invoke
    latex2mathml to produce a <math>...</math> element representing the Latex math code.
    """

    def __init__(self, md):
        super().__init__(MATH_TEX_RE, md)

    def handleMatch(self, match, data):

        latex_inline = match.group('latex_inline')
        latex_block = match.group('latex_block')

        display_attr = 'block' if latex_block else 'inline'

        mathml_code = latex2mathml.converter.convert(latex_inline or latex_block,
                                                     display = display_attr)
        element = ElementTree.fromstring(mathml_code)
        coerce_subtree(element)

        attrs = match.group('attr')
        if attrs:
            AttrListTreeprocessor().assign_attrs(element, attrs)

        return element, match.start(0), match.end(0)



class LatexPostprocessor(Postprocessor):
    """
    The post-processor is responsible for compiling the Latex code identified by the preprocessor,
    converting it to SVG, caching the result, and embedding it the final HTML. It searches for the
    placeholder strings inserted by the preprocessor to determine where to substitute the proper
    HTML.
    """

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

    CONVERTER_CORRECTIONS = {
        # pdf2svg leaves off the units on width/height, and the default is technically 'px', but
        # the numbers appear to be expressed in 'pt'. This just adds 'pt' to the SVG dimensions.
        'pdf2svg': lambda svg: re.sub('<svg[^>]*>',
                                      lambda m: re.sub(r'((width|height)="[0-9]+(\.[0-9]+)?)"',
                                                       r'\1pt"',
                                                       m.group()),
                                      svg)
    }

    EMBEDDERS = {
        'data_uri': DataUriEmbedder,
        'svg_element': SvgElementEmbedder
    }

    def __init__(self, md, stash: LatexStash, build_dir: str, cache, progress: Progress,
                 tex: str, pdf_svg_converter: str, embedding: str, strip_html_comments: bool):
        self.md = md
        self.stash = stash
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

        self.converter_correction = (
            self.CONVERTER_CORRECTIONS.get(pdf_svg_converter) or
            (lambda svg: svg)
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
        cache_key = (self.CACHE_PREFIX, latex, self.stash.input_repr,
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

                svg_content = self.converter_correction(svg_content)

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
        for i, latex in self.stash.latex_docs.items():
            html[i] = self._build(latex, self.stash.latex_attrs[i])

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
            ],
            'math': [
                'mathml',
                r'How to handle $...$ and $$...$$ sequences, which are assumed to contain Latex math code. The options are "ignore", "latex" or "mathml" (the default). For "ignore", math code is left untouched by this extension. Use this to avoid conflicts if, for instance, you\'re using another extension (like pymdownx.arithmatex) to handle them. For "latex", math code is compiled in essentially the same way as \begin{}...\end{} blocks (but in math mode). For "mathml", math code is converted to MathML <math> elements, to be rendered by the browser.'
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

        prepend = self.getConfig('prepend')
        doc_class = self.getConfig('doc_class')
        doc_class_options = self.getConfig('doc_class_options')
        strip_html_comments = self.getConfig('strip_html_comments')
        math = self.getConfig('math')

        stash = LatexStash((prepend, doc_class, doc_class_options, strip_html_comments, math))

        preprocessor = LatexPreprocessor(
            stash,
            prepend             = prepend,
            doc_class           = doc_class,
            doc_class_options   = doc_class_options,
            strip_html_comments = strip_html_comments,
        )

        self.postprocessor = LatexPostprocessor(
            md,
            stash,
            build_dir           = self.getConfig('build_dir'),
            cache               = self.getConfig('cache'),
            progress            = self.getConfig('progress'),
            tex                 = self.getConfig('tex'),
            pdf_svg_converter   = self.getConfig('pdf_svg_converter'),
            embedding           = self.getConfig('embedding'),
            strip_html_comments = self.getConfig('strip_html_comments'),
        )

        md.preprocessors.register(preprocessor, 'la-latex-pre', 15)
        md.postprocessors.register(self.postprocessor, 'la-latex-post', 25)


        if math == 'mathml':
            inlineProcessor = LatexMathMLInlineProcessor(md)

        elif math == 'latex':
            inlineProcessor = LatexInlineProcessor(
                md,
                stash,
                prepend             = prepend,
                doc_class           = doc_class,
                doc_class_options   = doc_class_options,
            )
        else:
            inlineProcessor = None

        if inlineProcessor:
            md.ESCAPED_CHARS.append('$')
            md.inlinePatterns.register(EscapeInlineProcessor(md), 'la-latex-inline-escape', 186)
            md.inlinePatterns.register(inlineProcessor, 'la-latex-inline', 185)



def makeExtension(**kwargs):
    return LatexExtension(**kwargs)

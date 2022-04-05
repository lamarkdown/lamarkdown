'''
# Latex Extension

The 'latex' extension lets uses write Latex code inside a .md file, which will be compiled,
converted to SVG, and embedded in the output HTML.

The user must write the Latex code as a block (or blocks), and can either:

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

# Originally adapted from https://github.com/neapel/tikz-markdown, but since modified extensively

#from lamarkdown.lib.error import Error
from lamarkdown.lib.progress import Progress, ErrorMsg, ProgressMsg

from markdown import *
from markdown.extensions import *
from markdown.extensions.attr_list import AttrListTreeprocessor
from markdown.blockprocessors import BlockProcessor
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


HTML_COMMENT_REGEX = re.compile(f'<!--.*?-->', re.DOTALL)


def get_blocks_strip_html_comments(blocks):
    in_comment = False
    while blocks:
        b = blocks.pop(0)
        if in_comment:
            if (i := b.find('-->')) != -1:
                # Strip out comment started in a previous block
                b = b[i + 3:]
                in_comment = False

        if not in_comment:
            # Strip out within-block any comments
            b = HTML_COMMENT_REGEX.sub('', b)

            if (i := b.find('<!--')) != -1:
                # Strip out start of multi-block comment
                b = b[:i]
                in_comment = True

            # Send on what's left of the block
            yield b


class LatexFormatter:
    def extract_blocks(self, block_generator) -> str:  raise NotImplementedError
    def end(self) -> str:                              raise NotImplementedError
    def format(self, prepend: str, latex: str) -> str: raise NotImplementedError


class FullLatex(LatexFormatter):
    DOCUMENTCLASS_REGEX = re.compile(r'^[^%]*\documentclass\s*\[[^]*\]\s*\{[^}]*\}', re.MULTILINE)

    def extract_blocks(self, blocks) -> str:
        end = self.end()
        latex = ''
        for block in blocks:
            latex += '\n' + block
            if end in block:
                break

        return latex

    def end(self) -> str:
        return r'\end{document}'

    def format(self, prepend: str, latex: str) -> str:
        if prepend:
            match = self.DOCUMENTCLASS_REGEX.search(latex)
            split = match.end() if match else 0
            latex = f'{latex[:split]}\n{prepend}{latex[split:]}'

        return latex



class SingleEnvironment(LatexFormatter):
    START_REGEX = re.compile(r'\\begin\{([^}]+)\}')

    def __init__(self, doc_class: str, doc_class_options: str):
        self.doc_class = doc_class
        self.doc_class_options = doc_class_options

    def extract_blocks(self, blocks) -> str:
        block_iter = iter(blocks)
        match = None
        latex = ''
        for block in block_iter:
            latex += '\n' + block
            match = self.START_REGEX.search(block)
            if match:
                first_block = block
                break

        if match:
            self._start = match.group(0)
            self._envName = match.group(1)
            self._end = f'\\end{{{self._envName}}}'

            if not self._end in first_block:
                for block in block_iter:
                    latex += '\n' + block
                    if self._end in block:
                        break

        else:
            # This is an error. The following values are just to ensure the message is sensible.
            self._start = r'\begin{...}'
            self._envName = '...'
            self._end = r'\end{...}'

        return latex

    def end(self) -> str:
        return self._end

    def format(self, prepend: str, latex: str) -> str:
        startIndex = latex.find(self._start)
        preamble = latex[:startIndex]
        main = latex[startIndex:]

        if self._envName != 'document':
            main = r'\begin{document}' + main + r'\end{document}'

        return (
            f'\\documentclass[{self.doc_class_options}]{{{self.doc_class}}}\n' +
            prepend +
            f'\\usepackage{{tikz}}' +
            preamble +
            main
        )



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



class LatexBlockProcessor(BlockProcessor):
    #cache: Dict[str,ElementTree.Element] = {}
    CACHE_PREFIX = 'lamarkdown.latex'

    # Taken from markdown.extensions.attr_list.AttrListTreeprocessor:
    ATTR_REGEX = re.compile(r'\{\:?[ ]*([^\}\n ][^\}\n]*)[ ]*\}')

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

    def __init__(self, parser, build_dir: str, cache, progress: Progress,
                 tex: str, pdf_svg_converter: str, embedding: str, prepend: str, 
                 doc_class: str, doc_class_options: str, strip_html_comments: bool):
        super().__init__(parser)
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

        self.prepend = prepend
        self.doc_class = doc_class
        self.doc_class_options = doc_class_options
        self.strip_html_comments = strip_html_comments


    def reset(self):
        self.embedder = self.EMBEDDERS[self.embedding]()


    def test(self, parent, block):
        b = block.lstrip()
        return (
            b.startswith(r'\documentclass') or
            b.startswith(r'\usepackage') or
            b.startswith(r'\usetikzlibrary') or
            b.startswith(r'\begin')
        )


    def run(self, parent, blocks):
        # Which of the two forms of Latex code determines how we discover the end of the snippet,
        # and of course how we build the complete .tex file.
        if blocks[0].lstrip().startswith(r'\documentclass'):
            formatter = FullLatex()
        else:
            formatter = SingleEnvironment(self.doc_class, self.doc_class_options)

        # The process of extracting blocks must be HTML-comment-aware (if we're intending to
        # strip such comments), because one of the sentinel strings we're looking for may first be
        # within a comment.
        if self.strip_html_comments:
            block_iter = get_blocks_strip_html_comments(blocks)
        else:
            block_iter = get_blocks(blocks)

        latex = formatter.extract_blocks(block_iter)
        end = formatter.end()

        # Run postprocessors. Python markdown's _pre_processors replace certain constructs
        # (particularly HTML snippets) with special "placeholders" (containing invalid characters).
        # These are again replaced by postprocessors once all the block processing and tree
        # manipulation is done.
        #
        # Except the 'latex' code we have is not subject to that process. We have to explicitly
        # run the postprocessors here so that Latex doesn't encounter the raw placeholder text.
        for post_proc in self.parser.md.postprocessors:
            latex = post_proc.run(latex)

        # But now that we've done that, we may have additional HTML comments to strip out:
        if self.strip_html_comments:
            latex = HTML_COMMENT_REGEX.sub('', latex)

        latex_end = latex.rfind(end)
        if latex_end < 0:
            begin = latex.lstrip().split('\n', 1)[0]
            parent.append(self.progress.error(
                'latex', f'Couldn\'t find closing "{end}" after "{begin}"', latex).as_dom_element())
            return

        # There could be some extra 'post_text' after the last \end{...}, which might contain (for
        # instance) an attribute list.
        latex_end += len(end)
        post_text = latex[latex_end:].strip()
        latex = latex[:latex_end]

        # Build a representation of all the input information sources.
        cache_key = (self.CACHE_PREFIX, 
                     latex, self.tex_cmdline, self.converter_cmdline, self.embedding, self.prepend, 
                     self.doc_class, self.doc_class_options, self.strip_html_comments)
        
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
                    full_doc = formatter.format(self.prepend, latex)
                    f.write(full_doc)
            except OSError as e:
                parent.append(self.progress.error_from_exception('Latex', e).as_dom_element())
                return

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
                        parent.append(self.progress.error(
                            'Latex', 
                            f'Resulting SVG code is empty -- either {self.tex_cmdline[0]} or {self.converter_cmdline[0]} failed',
                            svg_content
                        ).as_dom_element())
                
                # If compilation was successful, cache the result.
                #self.cache[cache_key] = self.embedder.generate_html(svg_file)
                self.cache[cache_key] = self.embedder.generate_html(svg_content)
                
            except CommandException as e:
                parent.append(self.progress.error('Latex', str(e), e.output, full_doc).as_dom_element())
                return

        # We make a copy of the cached element, because different instances of it could
        # conceivably be assigned different attributes below.
        element = copy.copy(self.cache.get(cache_key))

        if post_text:
            match = self.ATTR_REGEX.match(post_text)
            if match:
                # Hijack parts of the attr_list extension to handle the attribute list we've just
                # found here.
                #
                # (Warning: there is a risk here that a future version of Markdown will change
                # the design of attr_list, such that this call doesn't work anymore. For now, it
                # seems the easiest and most consistent way to go.)
                AttrListTreeprocessor().assign_attrs(element, match[1])

            else:
                # Miscellaneous trailing text -- put it back on the queue
                blocks.insert(0, post_text)

        parent.append(element)



class LatexExtension(Extension, BlockProcessor):
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
        if embedding not in LatexBlockProcessor.EMBEDDERS:
            progress.error('latex', f'Invalid value "{embedding}" for config option "embedding"')
            self.setConfig('embedding', 'data_uri')
            #raise ValueError(f'Invalid value "{embedding}" for config option "embedding"')

    def reset(self):
        self.processor.reset()

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)

        self.processor = LatexBlockProcessor(
            md.parser,
            build_dir           = self.getConfig('build_dir'),
            cache               = self.getConfig('cache'),
            progress            = self.getConfig('progress'),
            tex                 = self.getConfig('tex'),
            pdf_svg_converter   = self.getConfig('pdf_svg_converter'),
            embedding           = self.getConfig('embedding'),
            prepend             = self.getConfig('prepend'),
            doc_class           = self.getConfig('doc_class'),
            doc_class_options   = self.getConfig('doc_class_options'),
            strip_html_comments = self.getConfig('strip_html_comments'),
        )

        # Priority must be:
        # >10 -- higher/earlier than Python Markdown's ParagraphProcessor (or else the latex code will be formatted as text);
        # <90 -- lower/later than Python Markdown's ListIndentProcessor (or else Latex code nested in lists will screw up list formatting).

        md.parser.blockprocessors.register(self.processor, 'lamarkdown.latex', 50)



def makeExtension(**kwargs):
    return LatexExtension(**kwargs)

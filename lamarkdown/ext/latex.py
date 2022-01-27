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
from typing import Union
from xml.etree import ElementTree


class CommandException(Exception):
    def __init__(self, command: Union[str,list[str]], msg: str):
        if isinstance(command, list):
            command = " ".join(command)
        super().__init__(f'Command "{command}" {msg}')

class SyntaxException(Exception): pass

def check_run(command: Union[str,list[str]], expected_output_file: str, **kwargs):
    start_time = time.time_ns()

    proc = subprocess.run(command, shell=isinstance(command, str), **kwargs)
    if proc.returncode != 0:
        raise CommandException(command, f'reported error code {proc.returncode}')

    try:
        file_time = os.stat(expected_output_file).st_mtime_ns
    except OSError:
        file_time = 0

    if file_time < start_time:
        raise CommandException(command, f'did not create expected file "{expected_output_file}"')


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
    def extractBlocks(self, block_generator) -> str:  raise NotImplementedError
    def end(self) -> str:                             raise NotImplementedError
    def format(self,prepend: str, latex: str) -> str: raise NotImplementedError


class FullLatex(LatexFormatter):
    DOCUMENTCLASS_REGEX = re.compile(r'^[^%]*\documentclass\s*\[[^]*\]\s*\{[^}]*\}', re.MULTILINE)

    def extractBlocks(self, blocks) -> str:
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
        
    def extractBlocks(self, blocks) -> str:
        block_iter = iter(blocks)        
        match = False
        latex = ''
        for block in block_iter:
            latex += '\n' + block
            match = self.START_REGEX.search(block)
            if match:
                break
            
        if match:
            self._start = match.group(0)
            self._envName = match.group(1)
            self._end = f'\\end{{{self._envName}}}'
            
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

        return f'''
            \\documentclass[{self.doc_class_options}]{{{self.doc_class}}}
            {prepend}
            \\usepackage{{tikz}}
            {preamble}
            {main}
            '''


class Embedder:
    def generate_html(self, svg_file: str) -> str: raise NotImplementedError


class DataUriEmbedder(Embedder):
    def generate_html(self, svg_file: str) -> str:
        with open(svg_file) as reader:
            # Encode SVG data as a data URI in an <img> element.
            data_uri = f'data:image/svg+xml;base64,{base64.b64encode(reader.read().strip().encode()).decode()}'
        return ElementTree.fromstring(f'<img src="{data_uri}" />')


class SvgElementEmbedder(Embedder):
    def __init__(self):
        self.svg_index = 0

    def generate_html(self, svg_file: str) -> str:
        with open(svg_file) as reader:
            svg_element = ElementTree.fromstring(reader.read())

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
    cache = {}

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

    def __init__(self, parser, build_dir: str, tex: str, pdf_svg_converter: str, embedding: str, 
                 prepend: str, doc_class: str, doc_class_options: str, strip_html_comments: bool):
        super().__init__(parser)
        self.build_dir = build_dir

        self.tex_cmdline: Union[list[str],str] = (
            self.TEX_CMDLINES.get(tex) or
            tex.replace('in.tex', 'job.tex').replace('out.pdf', 'job.pdf')
        )

        self.converter_cmdline: Union[list[str],str] = (
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

        latex = formatter.extractBlocks(block_iter)
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

        latexEnd = latex.rfind(end)
        if latexEnd < 0:
            raise SyntaxException(f'Couldn\'t find closing "{end}" for latex code """{latex}"""')
        latexEnd += len(end)

        if latexEnd >= 0:
            # There is possibly some extra text 'postText' after the last \end{...}, which
            # might contain (for instance) an attribute list.
            postText = latex[latexEnd:].strip()
            latex = latex[:latexEnd]
        else:
            # \end{...} is missing. This will be an error anyway at some point.
            postText = ''
            
        # Build a representation of all the input information sources.
        input_repr = repr((latex,
                           self.tex_cmdline, self.converter_cmdline, self.embedding,
                           self.prepend, self.doc_class, self.doc_class_options, self.strip_html_comments))

        # If not in cache, compile it.
        if input_repr not in self.cache:
            hasher = hashlib.sha1()
            hasher.update(latex.encode('utf-8'))
            fileBuildDir = os.path.join(self.build_dir, 'latex-' + hasher.hexdigest())
            os.makedirs(fileBuildDir, exist_ok=True)

            tex_file = os.path.join(fileBuildDir, 'job.tex')
            pdf_file = os.path.join(fileBuildDir, 'job.pdf')
            svg_file = os.path.join(fileBuildDir, 'job.svg')

            with open(tex_file, 'w') as f:
                f.write(formatter.format(self.prepend, latex))

            check_run(
                self.tex_cmdline,
                pdf_file,
                cwd=fileBuildDir,
                env={**os.environ, "TEXINPUTS": f'.:{os.getcwd()}:'}
            )

            check_run(
                self.converter_cmdline,
                svg_file,
                cwd=fileBuildDir
            )

            self.cache[input_repr] = self.embedder.generate_html(svg_file)


        # We make a copy of the cached element, because different instances of it could
        # conceivably be assigned different attributes below.
        element = copy.copy(self.cache.get(input_repr))

        if postText:
            match = self.ATTR_REGEX.match(postText)
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
                blocks.insert(0, postText)

        parent.append(element)



class LatexExtension(Extension, BlockProcessor):
    def __init__(self, **kwargs):
        try:
            # Try to get the build dir (the location where we'll execute latex, and where all its
            # temporary files will accumulate) from the actual current build parameters. This will
            # only work if this extension is being used within the context of lamarkdown.
            #
            # But we do have a fallback on the off-chance that someone wants to use it elsewhere.

            from lamarkdown.lib.build_params import BuildParams
            default_build_dir = BuildParams.current.build_dir if BuildParams.current else 'build'

        except ModuleNotFoundError:
            default_build_dir = 'build'

        self.config = {
            'build_dir': [default_build_dir, 'Location to write temporary files'],
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

    def reset(self):
        self.processor.reset()

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)

        self.processor = LatexBlockProcessor(
            md.parser,
            build_dir           = self.getConfig('build_dir'),
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

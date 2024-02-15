'''
# Markdown Demo Extension

This supports the Lamarkdown documentation. It defines a type of 'block'* containing build logic
and markdown code. It syntax highlights these, but also _compiles_ them (by invoking Lamarkdown
itself, possibly recursively), and embeds the output in an <iframe>, with a data URI.

Thus, we can embed markdown examples within a markdown document, next to the (auto-generated)
output.

(*) Blocks are a construct defined in Pymdown Extensions.
See https://facelessuser.github.io/pymdown-extensions/extensions/blocks/.

'''
from lamarkdown.lib.build_params import BuildParams
from lamarkdown.lib.lamd import get_fetch_cache_dir
from lamarkdown.lib.md_compiler import compile
from lamarkdown.lib.directives import Directives
from lamarkdown.lib.progress import Progress

from pymdownx.blocks import BlocksExtension  # type: ignore
from pymdownx.blocks.block import Block      # type: ignore

import diskcache  # type: ignore
import lxml
import pygments
import pygments.lexers
import pygments.formatters

import atexit
import base64
import os
import os.path
import re
import shutil
import tempfile
from textwrap import dedent
from xml.etree import ElementTree

NAME = 'la.markdown_demo'  # For error messages

BUILD_FILE    = 'example.py'
MARKDOWN_FILE = 'example.md'
TARGET_FILE   = 'example.html'

SEPARATOR = '---'
SEPARATOR_REGEX = re.compile(fr'(?m)^\s*{SEPARATOR}\s*$')
LITERAL_SEPARATOR_REGEX = re.compile(fr'(?m)^[ ]*\\{SEPARATOR}[ ]*$')

HTML_SEMI_NEWLINE_TAGS = {'caption', 'figcaption', 'p'}
HTML_NEWLINE_TAGS = {'div', 'figure', 'picture', 'table', 'tbody', 'tfoot', 'thead'}
HTML_NEWLINE_TAG_REGEX = re.compile(
    fr'<\s*(?P<end>/)?(?P<tag>{"|".join(HTML_NEWLINE_TAGS.union(HTML_SEMI_NEWLINE_TAGS))})>')
HTML_BLANK_LINES_REGEX = re.compile(r'(\s*\n){2,}')

def extra_files(file_list):
    if not (isinstance(file_list, list) or isinstance(file_list, tuple)):
        raise ValueError

    for file_name, description, language, visible in file_list:
        if any(not isinstance(v, str) for v in [file_name, description, language, visible]):
            raise ValueError

    return file_list


def pretty_print_html(html: str) -> str:

    def repl(match):
        both_newlines = match.group('tag') in HTML_NEWLINE_TAGS
        start_tag = match.group('end') is None
        return (
            ('\n' if both_newlines or start_tag else '')
            + match.group(0)
            + ('\n' if both_newlines or not start_tag else '')
        )

    html = HTML_NEWLINE_TAG_REGEX.sub(repl, html)
    html = HTML_BLANK_LINES_REGEX.sub('\n', html)
    return html



class MarkdownDemoBlock(Block):
    NAME = 'markdown-demo'
    OPTIONS = {
        'output_height': ['', str],
        'file_labels': [False, bool],
        'show_build_file': [True, bool],
        'extra_files': [[], extra_files],
        'show_extra_files': [True, lambda v: v],
        'resources': [[], list],
        'show_html_body': [False, bool],
    }

    def on_init(self):
        p = BuildParams.current
        self._build_cache = p.build_cache if p else {}
        self._fetch_cache = p.fetch_cache if p else diskcache.Cache(get_fetch_cache_dir())
        self._html_formatter = pygments.formatters.HtmlFormatter(wrapcode = True)

    def on_create(self, parent):
        container = ElementTree.SubElement(parent, 'div')
        container.set('class', 'markdown-demo')
        return container

    def on_markdown(self) -> str:
        return 'raw'

    def on_end(self, block: ElementTree.Element):
        text = dedent(block.text or '')
        block.text = None

        input_col = ElementTree.SubElement(block, 'div')
        output_col = ElementTree.SubElement(block, 'div')
        input_col.set('class', 'markdown-demo-input')
        output_col.set('class', 'markdown-demo-output')

        if output_height := self.options['output_height']:
            output_col.set('style', f'height: {output_height}')

        files = [(BUILD_FILE, 'Build file', 'python', self.options['show_build_file']),
                 *self.options['extra_files'],
                 (MARKDOWN_FILE, 'Markdown', 'markdown', True)]

        with tempfile.TemporaryDirectory() as build_dir:

            all_file_content = zip(files, SEPARATOR_REGEX.split(text))
            for (filename, descrip, lang, visible), content in all_file_content:
                content = LITERAL_SEPARATOR_REGEX.sub(SEPARATOR, content)

                if visible:
                    if self.options['file_labels']:
                        header = ElementTree.SubElement(input_col, 'p')
                        header.text = descrip

                    if content.strip() != '':
                        placeholder_text = self.md.htmlStash.store(pygments.highlight(
                            content,
                            pygments.lexers.get_lexer_by_name(lang),
                            self._html_formatter))

                        if len(input_col) == 0:
                            input_col.text = (input_col.text or '') + placeholder_text
                        else:
                            input_col[-1].tail = placeholder_text

                with open(os.path.join(build_dir, filename), 'w') as writer:
                    writer.write(content)

            for res_filename in self.options['resources']:
                shutil.copy(res_filename, build_dir)

            target_dir = os.path.join(build_dir, 'output')
            target_file = os.path.join(target_dir, TARGET_FILE)
            os.makedirs(target_dir, exist_ok = True)

            progress = Progress()
            build_params = BuildParams(
                src_file = os.path.join(build_dir, MARKDOWN_FILE),
                target_file = target_file,
                build_files = [os.path.join(build_dir, BUILD_FILE)],
                build_dir = build_dir,
                build_defaults = False,
                build_cache = self._build_cache,
                fetch_cache = self._fetch_cache,
                progress = progress,
                directives = Directives(progress),
                is_live = False,
                allow_exec_cmdline = True,
                allow_exec = True
            )

            preserve_cwd = os.getcwd()
            os.chdir(build_dir)
            compile(build_params)
            os.chdir(preserve_cwd)

            output_files = os.listdir(target_dir)
            for output_file in output_files:
                if len(output_files) > 1:
                    header = ElementTree.SubElement(output_col, 'p')
                    header.text = output_file

                with open(os.path.join(target_dir, output_file), 'rb') as reader:
                    output_bytes = reader.read()

                if self.options['show_html_body']:
                    output_html = output_bytes.decode()
                    if body := lxml.html.fromstring(output_html).find('.//body'):
                        output_html = pretty_print_html(
                            ''.join(lxml.html.tostring(element,
                                                    encoding = 'unicode',
                                                    pretty_print = True)
                                    for element in body))

                    placeholder_text = self.md.htmlStash.store(pygments.highlight(
                        output_html,
                        pygments.lexers.get_lexer_by_name('html'),
                        self._html_formatter))

                    if len(output_col) == 0:
                        output_col.text = (output_col.text or '') + placeholder_text
                    else:
                        output_col[-1].tail = placeholder_text

                data_uri = f'data:text/html;base64,{base64.b64encode(output_bytes).decode()}'
                ElementTree.SubElement(output_col, 'iframe', src = data_uri)


class MarkdownDemoExtension(BlocksExtension):
    def __init__(self, *args, **kwargs):
        self._enabled = True
        if (p := BuildParams.current) is not None and not p.allow_exec:
            p.progress.error(NAME, msg = f'{NAME} requires "allow_exec" to be True')
            self._enabled = False

        super().__init__(*args, **kwargs)

    def extendMarkdownBlocks(self, md, block_mgr):
        if self._enabled:
            block_mgr.register(MarkdownDemoBlock, self.getConfigs())


def makeExtension(*args, **kwargs):
    return MarkdownDemoExtension(*args, **kwargs)

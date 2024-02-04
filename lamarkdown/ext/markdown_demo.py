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

SEPARATOR = re.compile(r'(?m)^\s*---\s*$')


def extra_files(file_list):
    if not (isinstance(file_list, list) or isinstance(file_list, tuple)):
        raise ValueError

    for file_name, description, language in file_list:
        if any(not isinstance(v, str) for v in [file_name, description, language]):
            raise ValueError

    return file_list


class MarkdownDemoBlock(Block):
    NAME = 'markdown-demo'
    OPTIONS = {
        'output_height': ['', str],
        'file_labels': [False, bool],
        'extra_files': [[], extra_files],
    }

    def on_init(self):
        build_dir = tempfile.mkdtemp()
        self._build_dir = build_dir

        @atexit.register
        def cleanup():
            shutil.rmtree(build_dir)

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

        files = [(BUILD_FILE, 'Build file', 'python'),
                 *self.options['extra_files'],
                 (MARKDOWN_FILE, 'Markdown', 'markdown')]

        for (filename, descrip, lang), content in zip(files, SEPARATOR.split(text)):
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

            with open(os.path.join(self._build_dir, filename), 'w') as writer:
                writer.write(content)

        target_dir = os.path.join(self._build_dir, 'output')
        target_file = os.path.join(target_dir, TARGET_FILE)
        os.makedirs(target_dir, exist_ok = True)

        progress = Progress()
        build_params = BuildParams(
            src_file = os.path.join(self._build_dir, MARKDOWN_FILE),
            target_file = target_file,
            build_files = [os.path.join(self._build_dir, BUILD_FILE)],
            build_dir = self._build_dir,
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
        os.chdir(self._build_dir)
        compile(build_params)
        os.chdir(preserve_cwd)

        # TODO: look for variants, not just one target_file

        output_files = os.listdir(target_dir)
        for output_file in output_files:
            if len(output_files) > 1:
                header = ElementTree.SubElement(output_col, 'p')
                header.text = output_file

            with open(os.path.join(target_dir, output_file), 'rb') as reader:
                output_bytes = reader.read()

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

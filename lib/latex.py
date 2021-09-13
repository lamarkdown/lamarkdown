# Originally adapted from https://github.com/neapel/tikz-markdown, but since modified extensively

from markdown import *
from markdown.extensions import *
from markdown.blockprocessors import BlockProcessor
from markdown.util import AtomicString

import base64
import glob
import hashlib
import os
import re
import subprocess
from xml.etree import ElementTree


class CommandException(Exception): pass
    
def check_run(command, **kwargs):
    proc = subprocess.run(command, **kwargs)
    if proc.returncode != 0:
        raise CommandException
        

class TikzBlockProcessor(BlockProcessor):
    cache = {}
    PREAMBLE_BEGIN = r'\usetikzlibrary'
    TIKZ_BEGIN = r'\begin{tikzpicture}'
    END = r'\end{tikzpicture}'
    
    def __init__(self, parser, buildDir):
        super().__init__(parser)
        self.buildDir = buildDir

    def test(self, parent, block):
        b = block.lstrip()
        return b.startswith(self.PREAMBLE_BEGIN) or b.startswith(self.TIKZ_BEGIN)

    def run(self, parent, blocks):
        
        # Gather latex code
        latex = blocks.pop(0)        
        while blocks and not latex.rstrip().endswith(self.END):
            latex += '\n' + blocks.pop(0)
            
        # If not in cache, compile it.
        if latex not in self.cache:
            hasher = hashlib.sha1()
            hasher.update(latex.encode('utf-8'))
            fileBuildDir = os.path.join(self.buildDir, 'tikz-' + hasher.hexdigest())
            os.makedirs(fileBuildDir, exist_ok=True)
            tex = os.path.join(fileBuildDir, 'job.tex')
            svg = os.path.join(fileBuildDir, 'job.svg')
            
            if latex.lstrip().startswith(self.PREAMBLE_BEGIN):
                tikzIndex = latex.find(self.TIKZ_BEGIN)
                latexPreamble = latex[:tikzIndex]
                tikz = latex[tikzIndex:]                
            else:
                latexPreamble = ''                
                tikz = latex
            
            with open(tex, 'w') as f:
                f.write(f'''
                    \\documentclass{{standalone}}
                    \\usepackage{{tikz}}
                    \\usepackage[default]{{opensans}}
                    {latexPreamble}
                    \\begin{{document}}\Large
                    {tikz}
                    \\end{{document}}''')

            check_run(
                ['xelatex', '-interaction', 'nonstopmode', 'job'],
                cwd=fileBuildDir,
                env={**os.environ, "TEXINPUTS": f'.:{os.getcwd()}:'}
            )
            
            check_run(
                ['pdf2svg', 'job.pdf', 'job.svg'],
                cwd=fileBuildDir
            )
                
            with open(svg) as svgReader:
                # Encode SVG data as a Data URI.
                dataUri = f'data:image/svg+xml;base64,{base64.b64encode(svgReader.read().strip().encode()).decode()}'
                self.cache[latex] = ElementTree.fromstring(f'<img src="{dataUri}" />')
                
                # Note: embedding SVG tags directly in the HTML is possible, but I encountered an 
                # issue where one SVG seemed to cause other subsequent SVGs to fail in rendering 
                # specific glyphs correctly. This may be related to the <defs> element created by 
                # pdf2svg.
                #
                # The issue appears not to arise when SVGs are encoded in base64 data URIs, perhaps
                # because the browser then treats them as separate "files".                             
        
        parent.append(self.cache.get(latex))


class TikzExtension(Extension, BlockProcessor):
    def __init__(self, **kwargs):
        self.config = {
            'build_dir': ['build', 'Location to write temporary files'],
        }
        super().__init__(**kwargs)
    
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.parser.blockprocessors.add(
            'tikz', 
            TikzBlockProcessor(md.parser, self.getConfig('build_dir')), 
            '>code')

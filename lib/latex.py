# Originally adapted from https://github.com/neapel/tikz-markdown, but since modified extensively

from markdown import *
from markdown.extensions import *
from markdown.extensions.attr_list import AttrListTreeprocessor
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
    
    # Taken from markdown.extensions.attr_list.AttrListTreeprocessor:
    ATTR_RE = re.compile(r'\{\:?[ ]*([^\}\n ][^\}\n]*)[ ]*\}')
    
    def __init__(self, parser, buildDir):
        super().__init__(parser)
        self.buildDir = buildDir

    def test(self, parent, block):
        b = block.lstrip()
        return b.startswith(self.PREAMBLE_BEGIN) or b.startswith(self.TIKZ_BEGIN)

    def run(self, parent, blocks):
        
        # Gather latex code
        latex = blocks.pop(0)        
        while blocks and not self.END in latex:
            latex += '\n' + blocks.pop(0)
            
        latexEnd = latex.rfind(self.END) + len(self.END)            
        if latexEnd >= 0:
            # There is possibly some extra text 'postText' after the last \end{tikzpicture}, which
            # might contain (for instance) an attribute list.
            postText = latex[latexEnd:].strip()
            latex = latex[:latexEnd]            
        else:
            # \end{tikzpicture} is missing. This will be an error anyway at some point.
            postText = ''
                        
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
                self.cache[latex] = dataUri
                
                # Note: embedding SVG tags directly in the HTML is possible, but I encountered an 
                # issue where one SVG seemed to cause other subsequent SVGs to fail in rendering 
                # specific glyphs correctly. This may be related to the <defs> element created by 
                # pdf2svg.
                #
                # The issue appears not to arise when SVGs are encoded in base64 data URIs, perhaps
                # because the browser then treats them as separate "files".                             
        
        
        element = ElementTree.fromstring(f'<img src="{self.cache.get(latex)}" />')
        
        if postText:
            match = self.ATTR_RE.match(postText)
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

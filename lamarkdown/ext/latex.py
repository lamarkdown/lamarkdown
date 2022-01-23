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

class SyntaxException(Exception): pass
    
def check_run(command, **kwargs):
    proc = subprocess.run(command, **kwargs)
    if proc.returncode != 0:
        raise CommandException



class LatexFormatter:
    def extractBlocks(self, blocks) -> str: raise NotImplementedError
    def end(self) -> str:                   raise NotImplementedError
    def format(self, latex: str) -> str:    raise NotImplementedError
    
    
    
class FullLatex(LatexFormatter):
    def extractBlocks(self, blocks) -> str:
        end = self.end()
        latex = blocks.pop(0)
        while blocks and not end in latex:
            latex += '\n' + blocks.pop(0)
            
    def end(self) -> str: 
        return r'\end{document}'

    def format(self, latex: str) -> str:
        return latex
    

            
class SingleEnvironment(LatexFormatter):
    START_REGEX = re.compile(r'\\begin\{([^}]+)\}')

    def extractBlocks(self, blocks) -> str:
        latex = blocks.pop(0)
        match = self.START_REGEX.search(latex)
        while blocks and not match:
            nextBlock = blocks.pop(0)
            latex += '\n' + nextBlock
            match = self.START_REGEX.search(nextBlock)
            
        if match:            
            self._start = match.group(0)            
            self._envName = match.group(1)
            self._end = f'\\end{{{self._envName}}}'
            while blocks and not self._end in latex:
                latex += '\n' + blocks.pop(0)
                
        else:
            # This is an error. The following values are just to ensure the message is sensible.
            self._start = r'\begin{...}'
            self._envName = '...'
            self._end = r'\end{...}'            
            
        return latex
        
    def end(self) -> str:
        return self._end

    def format(self, latex: str) -> str:
        startIndex = latex.find(self._start)
        preamble = latex[:startIndex]
        main = latex[startIndex:]
        
        if self._envName != 'document':
            main = r'\begin{document}' + main + r'\end{document}'
            
        return f'''
            \\documentclass{{standalone}}
            \\usepackage{{tikz}}
            \\usepackage[default]{{opensans}}
            {preamble}
            {main}
            '''
            


class TikzBlockProcessor(BlockProcessor):
    cache = {}    
    
    # Taken from markdown.extensions.attr_list.AttrListTreeprocessor:
    ATTR_RE = re.compile(r'\{\:?[ ]*([^\}\n ][^\}\n]*)[ ]*\}')
    
    def __init__(self, parser, buildDir):
        super().__init__(parser)
        self.buildDir = buildDir
        
    def test(self, parent, block):
        b = block.lstrip()
        return (
            b.startswith(r'\documentclass') or 
            b.startswith(r'\usepackage') or 
            b.startswith(r'\usetikzlibrary') or
            b.startswith(r'\begin')
        )
    

    def run(self, parent, blocks):
        
        if blocks[0].lstrip().startswith(r'\documentclass'):
            formatter = FullLatex()        
        else:
            formatter = SingleEnvironment()
        
        latex = formatter.extractBlocks(blocks)
        end = formatter.end()
                        
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
                        
                        
        # If not in cache, compile it.
        if latex not in self.cache:
            hasher = hashlib.sha1()
            hasher.update(latex.encode('utf-8'))
            fileBuildDir = os.path.join(self.buildDir, 'latex-' + hasher.hexdigest())
            os.makedirs(fileBuildDir, exist_ok=True)
            tex = os.path.join(fileBuildDir, 'job.tex')
            svg = os.path.join(fileBuildDir, 'job.svg')
                                
            with open(tex, 'w') as f:
                f.write(formatter.format(latex))

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

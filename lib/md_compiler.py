import html
import importlib.util
import os
import re


class CompileException(Exception): pass


class BuildParams:
    def __init__(self, srcFile: str, targetFile: str, buildFiles: list[str], buildDir: str):
        self.src_file = srcFile
        self.target_file = targetFile
        self.build_files = buildFiles
        self.build_dir = buildDir
        self.extensions = []
        self.extension_configs = {}
        self.css = ''

            
def compile(srcFile: str, 
            targetFile: str, 
            buildFiles: list[str],
            buildDir: str):
    
    buildParams = BuildParams(srcFile=srcFile, targetFile=targetFile, buildFiles=buildFiles, buildDir=buildDir)
        
    for buildFile in buildFiles:
        if buildFile is not None and os.path.exists(buildFile):
            moduleSpec = importlib.util.spec_from_file_location('buildfile', buildFile)
            buildMod = importlib.util.module_from_spec(moduleSpec)
            try:
                moduleSpec.loader.exec_module(buildMod)
            except Exception as e:
                raise CompileException from e
            
            initFn = buildMod.__dict__.get('init')
            if initFn:
                if not callable(initFn):
                    raise CompileException(f'In {buildFile}, expected "init" to be callable')
                initFn(buildParams)
            
            buildParams.extensions       .extend(buildMod.__dict__.get('extensions',        []))
            buildParams.extension_configs.update(buildMod.__dict__.get('extension_configs', {}))
            buildParams.css += buildMod.__dict__.get('css', '')
            
    css = buildParams.css
    
    # Strip CSS comments at the beginning of lines
    css = re.sub('(^|\n)\s*/\*.*?\*/', '\n', css, flags = re.DOTALL)
    
    # Strip CSS comments at the end of lines
    css = re.sub('/\*.*?\*/\s*($|\n)', '\n', css, flags = re.DOTALL)
        
    # Normalise line breaks
    css = re.sub('(\s*\n)+\s*', '\n', css, flags = re.DOTALL)
        
    import markdown
    md = markdown.Markdown(extensions = buildParams.extensions,
                           extension_configs = buildParams.extension_configs)
    
    with (
        open(srcFile, 'r') as src,
        open(targetFile, 'w') as target
    ):
        contentHtml = md.convert(src.read())
        
        # Strip HTML comments
        contentHtml = re.sub('<!--.*?-->', '', contentHtml, flags = re.DOTALL)
        
        # Default title, if we can't a better one
        titleHtml = os.path.basename(targetFile.removesuffix('.html'))
        
        # Find a better title, first by checking the embedded metadata (if any)
        if 'Meta' in md.__dict__ and 'title' in md.Meta:            
            titleHtml = html.escape(md.Meta['title'][0])
            contentHtml = f'<h1>{titleHtml}</h1>\n{contentHtml}'
            
        # Then check the HTML heading tags
        else:
            for n in range(1, 7):
                matches = re.findall(f'<h{n}>(.*?)</h{n}>', contentHtml, flags = re.DOTALL)
                if matches:
                    if len(matches) == 1:
                        # Only use the <hN> element as a title if there's exactly one it, for
                        # whichever N is the lowest. e.g., if there's no <H1> elements but one 
                        # <H2>, use the <H2>. But if there's two <H1> elements, we consider that
                        # to be ambiguous.
                        titleHtml = html.escape(matches[0])
                    break
                        
            
        fullHtml = '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8" />
                <title>{titleHtml:s}</title>
                <style>{css:s}</style>
            </head>
            <body>
                {contentHtml:s}
            </body>
            </html>
        '''
        fullHtml = re.sub('\n\s*', '\n', fullHtml).format(
            titleHtml = titleHtml,
            css = css,
            contentHtml = contentHtml
        )        
        target.write(fullHtml)

from lamarkdown.lib import build_params
from lamarkdown.ext import pruner
import markdown
import html
import importlib.util
import locale
import os
import re


class CompileException(Exception): pass


def compile(buildParams: build_params.BuildParams):

    buildParams.reset()
    buildParams.set_current()

    for buildFile in buildParams.build_files:
        if buildFile is not None and os.path.exists(buildFile):
            moduleSpec = importlib.util.spec_from_file_location('buildfile', buildFile)
            buildMod = importlib.util.module_from_spec(moduleSpec)
            try:
                moduleSpec.loader.exec_module(buildMod)
            except Exception as e:
                raise CompileException from e
            
            buildParams.env.update(buildMod.__dict__)


    if buildParams.variants:
        allClasses = {cls for classSpec in buildParams.variants.values()
                          for cls in classSpec}
        baseMdExtensions = buildParams.extensions

        for variant, retainedClasses in buildParams.variants.items():

            pruneClasses = allClasses.difference(retainedClasses)
            if pruneClasses:
                prunerExt = pruner.PrunerExtension(classes=pruneClasses)
                buildParams.extensions = baseMdExtensions + [prunerExt]
            else:
                buildParams.extensions = baseMdExtensions

            compileVariant(buildParams, altTargetFile = buildParams.alt_target_file(variant))

    else:
        compileVariant(buildParams)


def compileVariant(buildParams: build_params.BuildParams, altTargetFile: str = None):

    css = buildParams.css
    js = buildParams.js

    # Strip CSS comments at the beginning of lines
    css = re.sub('(^|\n)\s*/\*.*?\*/', '\n', css, flags = re.DOTALL)

    # Strip CSS comments at the end of lines
    css = re.sub('/\*.*?\*/\s*($|\n)', '\n', css, flags = re.DOTALL)

    # Normalise line breaks
    css = re.sub('(\s*\n)+\s*', '\n', css, flags = re.DOTALL)

    # TODO: we could run the 'slimit' Javascript minifier here.

    md = markdown.Markdown(extensions = buildParams.extensions,
                           extension_configs = buildParams.extension_configs)

    with (
        open(buildParams.src_file, 'r') as src,
        open(altTargetFile or buildParams.target_file, 'w') as target
    ):
        contentHtml = md.convert(src.read())

        # Strip HTML comments
        contentHtml = re.sub('<!--.*?-->', '', contentHtml, flags = re.DOTALL)

        # Default title, if we can't a better one
        titleHtml = os.path.basename(buildParams.target_file.removesuffix('.html'))

        # Find a better title, first by checking the embedded metadata (if any)
        if 'Meta' in md.__dict__ and 'title' in md.Meta:
            titleHtml = html.escape(md.Meta['title'][0])
            contentHtml = f'<h1>{titleHtml}</h1>\n{contentHtml}'

        else:
            # Then check the HTML heading tags
            for n in range(1, 7):
                matches = re.findall(f'<h{n}[^>]*>(.*?)</\s*h{n}\s*>', contentHtml, flags = re.IGNORECASE | re.DOTALL)
                if matches:
                    if len(matches) == 1:
                        # Only use the <hN> element as a title if there's exactly one it, for
                        # whichever N is the lowest. e.g., if there's no <H1> elements but one
                        # <H2>, use the <H2>. But if there's two <H1> elements, we consider that
                        # to be ambiguous.
                        titleHtml = html.escape(matches[0])
                    break

        # Detect the language
        if 'Meta' in md.__dict__ and 'lang' in md.Meta:
            langHtml = html.escape(md.Meta['lang'][0])

        else:
            # Quick-and-dirty extraction of language code, minus the region, from the default
            # locale. This is not 100% guaranteed to work, for a few reasons:
            # (1) HTML lang="..." expects an IETF language tag, whereas Python's locale module
            #     gives us an ISO locale.
            # (2) The convention (for specifying the HTML language) allows a full language tag,
            #     but the examples appear to favour the language only, without the region.

            localeParts = locale.getdefaultlocale()[0].split('_')
            langHtml = html.escape('-'.join(localeParts[:-1] or localeParts))


        fullHtml = '''
            <!DOCTYPE html>
            <html lang="{lang_html:s}">
            <head>
                <meta charset="utf-8" />
                <title>{title_html:s}</title>
                {css_list:s}<style>{css:s}</style>
            </head>
            <body>
            {content_start:s}{content_html:s}{content_end:s}
            {js_list:s}{js:s}</body>
            </html>
        '''
        fullHtml = re.sub('\n\s*', '\n', fullHtml.strip()).format(
            lang_html = langHtml,
            title_html = titleHtml,
            css_list = ''.join(f'<link rel="stylesheet" href="{f}" />\n' for f in buildParams.css_files),
            css = css,
            content_start = buildParams.content_start,
            content_html = contentHtml,
            content_end = buildParams.content_end,
            js_list = ''.join(f'<script src="{f}"></script>\n' for f in buildParams.js_files),
            js = f'<script>\n{js}\n</script>\n' if js else ''
        )
        target.write(fullHtml)

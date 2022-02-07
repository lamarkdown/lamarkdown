'''
This is where we invoke Python Markdown, but also:

* We find and invoke the build modules ('md_build.py', etc.)
* We determine what variants (if any) the document has.
* We build the complete HTML document around Python Markdown's output.
'''

from lamarkdown.lib.build_params import BuildParams
from lamarkdown.ext import pruner
import markdown
import html
import importlib.util
import locale
import os
import re
from typing import Dict, List


class CompileException(Exception): pass


def compile(build_params: BuildParams):

    build_params.reset()
    build_params.set_current()

    for build_file in build_params.build_files:
        if build_file is not None and os.path.exists(build_file):
            module_spec = importlib.util.spec_from_file_location('buildfile', build_file)
            if module_spec is None:
                raise CompileException(f'Could not load build module "{build_file}"')
            build_module = importlib.util.module_from_spec(module_spec)
            try:
                module_spec.loader.exec_module(build_module)
            except Exception as e:
                raise CompileException from e

            build_params.env.update(build_module.__dict__)


    if build_params.variants:
        all_classes = {cls for class_spec in build_params.variants.values()
                           for cls in class_spec}
        base_md_extensions = build_params.extensions

        for variant, retained_classes in build_params.variants.items():

            prune_classes = all_classes.difference(retained_classes)
            if prune_classes:
                pruner_ext = pruner.PrunerExtension(classes = prune_classes)
                build_params.extensions = base_md_extensions + [pruner_ext]
            else:
                build_params.extensions = base_md_extensions

            compile_variant(build_params, alt_target_file = build_params.alt_target_file(variant))

    else:
        compile_variant(build_params)


def compile_variant(build_params: BuildParams, alt_target_file: str = None):

    css = build_params.css
    js = build_params.js

    # Strip CSS comments at the beginning of lines
    css = re.sub('(^|\n)\s*/\*.*?\*/', '\n', css, flags = re.DOTALL)

    # Strip CSS comments at the end of lines
    css = re.sub('/\*.*?\*/\s*($|\n)', '\n', css, flags = re.DOTALL)

    # Normalise line breaks
    css = re.sub('(\s*\n)+\s*', '\n', css, flags = re.DOTALL)

    # TODO: we could run the 'slimit' Javascript minifier here.

    md = markdown.Markdown(extensions = build_params.extensions,
                           extension_configs = build_params.extension_configs)

    with (
        open(build_params.src_file, 'r') as src,
        open(alt_target_file or build_params.target_file, 'w') as target
    ):
        content_html = md.convert(src.read())
        meta: Dict[str,List[str]] = md.__dict__.get('Meta', {})

        # Strip HTML comments
        content_html = re.sub('<!--.*?-->', '', content_html, flags = re.DOTALL)

        # Default title, if we can't a better one
        title_html = os.path.basename(build_params.target_base)

        # Find a better title, first by checking the embedded metadata (if any)
        if 'title' in meta:
            title_html = html.escape(meta['title'][0])
            content_html = f'<h1>{title_html}</h1>\n{content_html}'

        else:
            # Then check the HTML heading tags
            for n in range(1, 7):
                matches = re.findall(f'<h{n}[^>]*>(.*?)</\s*h{n}\s*>', content_html, flags = re.IGNORECASE | re.DOTALL)
                if matches:
                    if len(matches) == 1:
                        # Only use the <hN> element as a title if there's exactly one it, for
                        # whichever N is the lowest. e.g., if there's no <H1> elements but one
                        # <H2>, use the <H2>. But if there's two <H1> elements, we consider that
                        # to be ambiguous.
                        title_html = html.escape(matches[0])
                    break

        # Detect the language
        if 'lang' in meta:
            lang_html = html.escape(meta['lang'][0])

        else:
            # Quick-and-dirty extraction of language code, minus the region, from the default
            # locale. This is not 100% guaranteed to work, for a few reasons:
            # (1) HTML lang="..." expects an IETF language tag, whereas Python's locale module
            #     gives us an ISO locale.
            # (2) The convention (for specifying the HTML language) allows a full language tag,
            #     but the examples appear to favour the language only, without the region.

            locale_parts = (locale.getdefaultlocale()[0] or 'en').split('_')
            lang_html = html.escape('-'.join(locale_parts[:-1] or locale_parts))


        full_html = '''
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
        full_html = re.sub('\n\s*', '\n', full_html.strip()).format(
            lang_html = lang_html,
            title_html = title_html,
            css_list = ''.join(f'<link rel="stylesheet" href="{f}" />\n' for f in build_params.css_files),
            css = css,
            content_start = build_params.content_start,
            content_html = content_html,
            content_end = build_params.content_end,
            js_list = ''.join(f'<script src="{f}"></script>\n' for f in build_params.js_files),
            js = f'<script>\n{js}\n</script>\n' if js else ''
        )
        target.write(full_html)

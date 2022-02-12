'''
This is where we invoke Python Markdown, but also:

* We find and invoke the build modules ('md_build.py', etc.)
* We determine what variants (if any) the document has.
* We build the complete HTML document around Python Markdown's output.
'''

from lamarkdown.lib.build_params import BuildParams, Resource
from lamarkdown.lib.error import Error
from lamarkdown.ext.pruner import PrunerExtension

import lxml.html
import markdown

import html
import importlib.util
from io import StringIO
import locale
import os
import re
from typing import Dict, List, Set
from xml.etree import ElementTree


class CompileException(Exception): pass


def compile(build_params: BuildParams):

    build_params.reset()
    build_params.set_current()

    pre_errors: List[Error] = []

    for build_file in build_params.build_files:
        if build_file is not None and os.path.exists(build_file):
            module_spec = importlib.util.spec_from_file_location('buildfile', build_file)
            if module_spec is None:
                pre_errors.append(Error(
                    build_file, f'Could not load build module "{build_file}"'))

            build_module = importlib.util.module_from_spec(module_spec)
            try:
                module_spec.loader.exec_module(build_module)
            except Exception as e:
                try:
                    with open(build_file) as reader:
                        build_file_contents = reader.read()
                except OSError:
                    build_file_contents = '[could not read file]'
                pre_errors.append(Error.from_exception(build_file, e, build_file_contents))

            build_params.env.update(build_module.__dict__)


    if build_params.variants:
        all_classes = {cls for class_spec in build_params.variants.values()
                           for cls in class_spec}
        base_md_extensions = build_params.extensions

        for variant, retained_classes in build_params.variants.items():

            prune_classes = all_classes.difference(retained_classes)
            if prune_classes:
                pruner_ext = PrunerExtension(classes = prune_classes)
                build_params.extensions = base_md_extensions + [pruner_ext]
            else:
                build_params.extensions = base_md_extensions

            compile_variant(build_params,
                            alt_target_file = build_params.alt_target_file(variant),
                            pre_errors = pre_errors)

    else:
        compile_variant(build_params,
                        pre_errors = pre_errors)


def _find_xpaths(content_html: str, xpaths: Set[str]) -> Set[str]:
    '''
    Re-parses the Python-Markdown-produced HTML using lxml, and attempts to match a set of XPath
    expressions against it. Returns the expressions that matched.
    '''
    root = lxml.html.parse(StringIO(content_html))
    return {xp for xp in xpaths if root.xpath(xp)}


def _resource_values(res_list: List[Resource], xpaths_found: Set[str]):
    '''
    Generates a sequence of resource values (which could be CSS/JS code, or CSS/JS URLs),
    by calling the value factory for each resource.

    The value factory needs to know the subset of its XPaths that matched. *In most cases*, it will
    either return a fixed value regardless, OR return a single specific value iff any of the
    XPaths matched, and None otherwise. (However, it is technically free to use more elaborate
    decision making.)
    '''
    for res in res_list:
        value = res.value_factory(xpaths_found.intersection(res.xpaths))
        if value:
            yield value


def compile_variant(build_params: BuildParams,
                    alt_target_file: str = None,
                    pre_errors: List[ElementTree.Element] = []):

    content_html = ''
    meta: Dict[str,List[str]] = {}
    pre_errors: List[Error] = list(pre_errors)

    try:
        with open(build_params.src_file, 'r') as src:
            content_markdown = src.read()
    except OSError as e:
        pre_errors.append(Error.from_exception(build_params.src_file, e))

    else:
        try:
            md = markdown.Markdown(extensions = build_params.extensions,
                                   extension_configs = build_params.extension_configs)
            content_html = md.convert(content_markdown)
            meta = md.__dict__.get('Meta', {})

        except Exception as e:
            pre_errors.append(Error.from_exception('Python Markdown', e))

    # Display pre-errors. (TODO: make this display in-document errors too?)
    for error in pre_errors:
        error.print()
        print()

    # Determien which XPath expressions match the document. This helps us understand which
    # 'resources' (CSS/JS code) we need to include in the output.
    xpaths_found = _find_xpaths(content_html, build_params.xpaths)

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


    # Stylesheets
    css = '\n'.join(_resource_values(build_params.css, xpaths_found))

    # Strip CSS comments at the beginning of lines
    css = re.sub('(^|\n)\s*/\*.*?\*/', '\n', css, flags = re.DOTALL)

    # Strip CSS comments at the end of lines
    css = re.sub('/\*.*?\*/\s*($|\n)', '\n', css, flags = re.DOTALL)

    # Normalise line breaks
    css = re.sub('(\s*\n)+\s*', '\n', css, flags = re.DOTALL)


    # Scripts
    js = '\n'.join(_resource_values(build_params.js, xpaths_found))
    if js:
        # TODO: run the 'slimit' Javascript minifier here?
        js = f'<script>{js}\n</script>\n'


    full_html_template = '''
        <!DOCTYPE html>
        <html lang="{lang_html:s}">
        <head>
            <meta charset="utf-8" />
            <title>{title_html:s}</title>
            {css_list:s}<style>{css:s}</style>
        </head>
        <body>{pre_errors:s}
        {content_start:s}{content_html:s}{content_end:s}
        {js_list:s}{js:s}</body>
        </html>
    '''
    full_html = re.sub('\n\s*', '\n', full_html_template.strip()).format(
        lang_html = lang_html,
        title_html = title_html,
        css_list = ''.join(f'<link rel="stylesheet" href="{value}" />\n'
                           for value in _resource_values(build_params.css_files, xpaths_found)),
        css = css,
        pre_errors = ''.join('\n' + error.to_html() for error in pre_errors),
        content_start = build_params.content_start,
        content_html = content_html,
        content_end = build_params.content_end,
        js_list = ''.join(f'<script src="{value}"></script>\n'
                          for value in _resource_values(build_params.js_files, xpaths_found)),
        js = js
    )

    with open(alt_target_file or build_params.target_file, 'w') as target:
        target.write(full_html)

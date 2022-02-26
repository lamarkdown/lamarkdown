'''
This is where we invoke Python Markdown, but also:

* We find and invoke the build modules ('md_build.py', etc.)
* We determine what variants (if any) the document has.
* We build the complete HTML document around Python Markdown's output.
'''

import lamarkdown
from lamarkdown.lib.build_params import BuildParams, Resource, Variant
from lamarkdown.lib.error import Error

import lxml.html
import markdown

from copy import deepcopy
import html
import importlib.util
import inspect
from io import StringIO
import locale
import os
import re
from typing import Dict, List, Set
from xml.etree import ElementTree


class CompileException(Exception): pass


def set_default_build_params(build_parms: BuildParams):
    lamarkdown.include('doc')


def compile(build_params: BuildParams):

    build_params.reset()
    build_params.set_current()

    pre_errors: List[Error] = []

    any_build_modules = False

    for build_file in build_params.build_files:
        if os.path.exists(build_file):
            any_build_modules = True
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

    if not any_build_modules and build_params.build_defaults:
        set_default_build_params(build_params)

    if build_params.variants:
        all_build_params = []
        for variant in build_params.variants:
            all_build_params += compile_variant(variant, build_params, pre_errors)
        return all_build_params

    else:
        content_html, meta = invoke_python_markdown(build_params, pre_errors)
        write_html(content_html, meta, build_params, pre_errors)
        return [build_params]



def compile_variant(variant: Variant,
                    build_params: BuildParams,
                    pre_errors: List[ElementTree.Element] = []):
    prev_build_params = BuildParams.current
    build_params = deepcopy(build_params)
    build_params.set_current()

    build_params.name = variant.name

    def default_output_namer(t):
        split = prev_build_params.output_namer(t).rsplit('.', 1)
        return (
            split[0]
            + prev_build_params.variant_name_sep
            + variant.name
            + '.'
            + (split[1] if len(split) == 2 else '')
        )

    build_params.output_namer = default_output_namer

    # A variant doesn't inherit the set of variants, or we would have infinite recursion.
    build_params.variants = []

    pre_errors = deepcopy(pre_errors)

    try:
        variant.build_fn()
    except Exception as e:
        try:
            variant_fn_source = inspect.getsource(variant.build_fn)
        except OSError:
            variant_fn_source = '[could not obtain source]'
        pre_errors.append(Error.from_exception(variant.name, e, variant_fn_source))

    if build_params.variants:
        all_build_params = []
        for sub_variant in build_params.variants:
            all_build_params += compile_variant(sub_variant, build_params, pre_errors)
    else:
        content_html, meta = invoke_python_markdown(build_params, pre_errors)
        write_html(content_html, meta, build_params, pre_errors)
        all_build_params = [build_params]

    prev_build_params.set_current()
    return all_build_params



def invoke_python_markdown(build_params: BuildParams,
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

    return content_html, meta



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



_parser = lxml.html.HTMLParser(default_doctype = False,
                               remove_blank_text = True,
                               remove_comments = True)

def write_html(content_html: str,
               meta: Dict[str,List[str]],
               build_params: BuildParams,
               pre_errors: List[ElementTree.Element] = []):

    root_element = lxml.html.parse(StringIO(content_html), _parser).find('body')

    # Run hook functions
    for fn in build_params.tree_hooks:
        fn(root_element)

    # Determine which XPath expressions match the document. This helps us understand which
    # 'resources' (CSS/JS code) we need to include in the output.
    xpaths_found = {xp for xp in build_params.resource_xpaths if root_element.xpath(xp)}

    # Serialise document tree. ('root_element' is the <body> element, and we want to exclude
    # that tag for now, so we serialise each child element separately.)
    content_html = ''.join(lxml.etree.tostring(elem, encoding = 'unicode', method = 'html')
                           for elem in root_element)

    # Default title, if we can't a better one
    title_html = os.path.basename(build_params.target_base)

    # Find a better title, first by checking the embedded metadata (if any)
    if 'title' in meta:
        title_html = html.escape(meta['title'][0])

    else:
        # Then check the HTML heading tags
        for n in range(1, 7):
            heading_elements = root_element.findall(f'.//h{n}')
            count = len(heading_elements)
            if count > 0:
                if count == 1:
                    # Only use the <hN> element as a title if there's exactly one it, for
                    # whichever N is the lowest. e.g., if there's no <H1> elements but one
                    # <H2>, use the <H2>. But if there's two <H1> elements, we consider that
                    # to be ambiguous.
                    title_html = html.escape(heading_elements[0].text)
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

    if css:
        css = f'<style>{css}</style>'


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
        {css_list:s}{css:s}</head>
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

    with open(build_params.output_file, 'w') as target:
        target.write(full_html)

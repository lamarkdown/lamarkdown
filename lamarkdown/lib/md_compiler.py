'''
This is where we invoke Python Markdown, but also:

* We find and invoke the build files ('md_build.py', etc.)
* We determine what variants (if any) the document has.
* We build the complete HTML document around Python Markdown's output.
'''

import lamarkdown
from .build_params import BuildParams, Variant
from .resources import ResourceSpec, Resource, ContentResource, ContentResourceSpec
from .progress import Progress
from . import resources
from . import resource_writers
from . import image_scaling

import lxml.html
import markdown

import collections
from copy import deepcopy
import html
import importlib.util
import inspect
from io import StringIO
import locale
import os
import re
from typing import Callable, Dict, List, Set
from xml.etree import ElementTree


class CompileException(Exception): pass


def set_default_build_params(build_parms: BuildParams):
    lamarkdown.m.doc()


def compile(base_build_params: BuildParams):

    build_params = deepcopy(base_build_params)
    build_params.set_current()
    progress = build_params.progress

    build_params.progress.progress(os.path.basename(build_params.src_file), 'Configuring')

    any_build_modules = False

    for build_file in build_params.build_files:
        if os.path.exists(build_file):
            any_build_modules = True
            module_spec = importlib.util.spec_from_file_location('buildfile', build_file)
            if module_spec is None:
                progress.error(build_file, f'Could not load build module "{build_file}"')

            build_module = importlib.util.module_from_spec(module_spec)
            try:
                module_spec.loader.exec_module(build_module)
            except Exception as e:
                try:
                    with open(build_file) as reader:
                        build_file_contents = reader.read()
                except OSError:
                    build_file_contents = '[could not read file]'
                progress.error_from_exception(build_file, e, build_file_contents)

            build_params.env.update(build_module.__dict__)

    if not any_build_modules and build_params.build_defaults:
        set_default_build_params(build_params)

    if build_params.variants:
        all_build_params = []
        for variant in build_params.variants:
            all_build_params += compile_variant(variant, build_params)
        return all_build_params

    else:
        content_html, meta = invoke_python_markdown(build_params)
        write_html(content_html, meta, build_params)
        return [build_params]



def compile_variant(variant: Variant,
                    build_params: BuildParams):
    prev_build_params = BuildParams.current
    build_params = deepcopy(build_params)
    build_params.set_current()

    build_params.name = variant.name

    def default_output_namer(t):
        split = prev_build_params.output_namer(t).rsplit('.', 1)
        return (
            split[0]
            + prev_build_params.variant_name_sep
            + build_params.name
            + '.'
            + (split[1] if len(split) == 2 else '')
        )

    build_params.output_namer = default_output_namer

    # A variant doesn't inherit the set of variants, or we would have infinite recursion.
    build_params.variants = []

    try:
        variant.build_fn()
    except Exception as e:
        try:
            variant_fn_source = inspect.getsource(variant.build_fn)
        except OSError:
            variant_fn_source = '[could not obtain source]'
        build_params.progress.error_from_exception(variant.name, e, variant_fn_source)

    if build_params.variants:
        all_build_params = []
        for sub_variant in build_params.variants:
            all_build_params += compile_variant(sub_variant, build_params)
    else:
        content_html, meta = invoke_python_markdown(build_params)
        write_html(content_html, meta, build_params)
        all_build_params = [build_params]

    prev_build_params.set_current()
    return all_build_params



def invoke_python_markdown(build_params: BuildParams):

    build_params.progress.progress(os.path.basename(build_params.output_file), 'Invoking Python Markdown')
    content_html = ''
    meta: Dict[str,List[str]] = {}

    try:
        with open(build_params.src_file, 'r') as src:
            content_markdown = src.read()
    except OSError as e:
        build_params.progress.error_from_exception(build_params.src_file, e)

    else:
        try:
            md = markdown.Markdown(
                extensions = build_params.obj_extensions + list(build_params.named_extensions.keys()),
                extension_configs = build_params.named_extensions
            )

            content_html = md.convert(content_markdown)
            meta = md.__dict__.get('Meta', {})

        except Exception as e:
            build_params.progress.error_from_exception('Python Markdown', e)

    return content_html, meta


def resource_list(spec_list: List[ResourceSpec],
                  xpaths_found: Set[str],
                  build_params: Progress) -> List[Resource]:
    res_list = []
    for spec in spec_list:
        res = spec.make_resource(xpaths_found, build_params)
        if res:
            res_list.append(res)
    return res_list


_parser = lxml.html.HTMLParser(default_doctype = False,
                               remove_blank_text = True,
                               remove_comments = True)

CSS_VAR_REGEX = re.compile(
    r'''
    (?<![\w-])   # Starts after a non-word/dash char
    --           # Starts with this
    [\w-]+       # Contains letters, digits, _ and -.
    ''',         # Also matches greedily, so we don't need a negative lookahead.
    re.VERBOSE)

def write_html(content_html: str,
               meta: Dict[str,List[str]],
               build_params: BuildParams):

    build_params.progress.progress(os.path.basename(build_params.output_file), 'Creating output document')

    # Run HTML hook functions
    # (Note: content_html *does not* have a <body> element wrapped around it at this point.)
    for fn in build_params.html_hooks:
        new_content_html = fn(content_html)
        if new_content_html is not None:
            content_html = new_content_html

    buf = StringIO(content_html or '<body></body>')
    try:
        root_element = lxml.html.parse(buf, _parser).find('body')
    except Exception as e: # Unfortunately lxml raises 'AssertionError', which I don't want to catch explicitly.
        build_params.progress.error(os.path.basename(build_params.output_file), 'No document created')
        return

    # Run tree hook functions
    for fn in build_params.tree_hooks:
        new_root = fn(root_element)
        if new_root is not None:
            # Allow hook functions to replace (and return) the whole root element if they want.
            root_element = new_root

    image_scaling.scale_images(root_element, build_params)

    # Embed external resources, if needed. (Note: stylesheets and scripts are handled separately.
    # We're still only dealing with the output of Python Markdown here.)
    resource_writers.embed_media(root_element, build_params.resource_base_url, build_params)

    disentangle_svgs(root_element)

    # Find all used codepoints
    build_params.font_codepoints.update(
        ord(ch)
        for text in root_element.itertext()
        for ch in text)
    build_params.font_codepoints.update(range(0x00, 0x80)) # Add all ASCII chars too

    # Determine which XPath expressions match the document (so we know later which css/js
    # resources to include).
    xpaths_found = {xp for xp in build_params.resource_xpaths if root_element.xpath(xp)}

    # Serialise document tree.
    if root_element.tag == 'body':
        # Exclude the <body> element for now -- just serialise each child element separately.
        content_html = ''.join(lxml.etree.tostring(elem, encoding = 'unicode', method = 'html')
                               for elem in root_element)
    else:
        # This isn't <body> (presumably because a hook function has changed it), so serialise it
        # as-is.
        content_html = lxml.etree.tostring(root_element, encoding = 'unicode', method = 'html')

    # Default title, if we can't a better one
    title_html = os.path.basename(build_params.target_base)

    # Find a better title, first by checking the embedded metadata (if any)
    if 'title' in meta:
        title_html = html.escape(meta['title'][0])

    else:
        # Then check the HTML heading tags
        for n in range(1, 7):
            heading_elements = root_element.xpath(f'.//h{n}')
            count = len(heading_elements)
            if count > 0:
                if count == 1:
                    # Only use the <hN> element as a title if there's exactly one it, for
                    # whichever N is the lowest. e.g., if there's no <H1> elements but one
                    # <H2>, use the <H2>. But if there's two <H1> elements, we consider that
                    # to be ambiguous.
                    title_html = html.escape(heading_elements[0].text or '')
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

        locale_parts = (locale.getlocale()[0] or 'en').split('_')
        lang_html = html.escape('-'.join(locale_parts[:-1] or locale_parts))

    # Instantiate all CSS resources
    css_list = resource_list(build_params.css, xpaths_found, build_params.progress)

    if any(isinstance(s, ContentResource) for s in css_list):
        # Figure out which CSS variables (custom properties) we need to define, based on whether
        # they're actually being used. We do this through simple regexes, rather than elaborate CSS
        # parsing, because it's far easier, and false positives (e.g., if a property is named
        # inside a string) don't do any real damage.

        vars_used = set()
        for res in css_list:
            if isinstance(res, ContentResource):
                vars_used.update(CSS_VAR_REGEX.findall(res.content))

        vars_to_be_defined = {}
        while len(vars_used) > 0:
            css_var_name = vars_used.pop()[2:] # Strip '--' prefix
            if css_var_name in build_params.css_vars:
                value = build_params.css_vars[css_var_name]
                vars_to_be_defined[css_var_name] = value

                # A variable definition may reference other variables. If so, add them to the set.
                vars_used.update(CSS_VAR_REGEX.findall(value))

        if vars_to_be_defined:
            # If we found any variables we can define, create an extra ContentResource, to be
            # prepended to the existing embedded CSS.
            css_list.insert(0, ContentResource(
                ':root {\n' + '\n'.join(
                    f'--{name}: {value};'
                    for name, value in sorted(vars_to_be_defined.items())
                ) + '\n}'
            ))

    css = resource_writers.StylesheetWriter(build_params).format(css_list)
    js = resource_writers.ScriptWriter(build_params).format(
        resource_list(build_params.js, xpaths_found, build_params.progress))

    full_html_template = '''
        <!DOCTYPE html>
        <html lang="{lang_html:s}">
        <head>
        <meta charset="utf-8" />
        {title_html:s}{css:s}</head>
        <body>{errors:s}
        {content_html:s}
        {js:s}</body>
        </html>
    '''
    full_html = re.sub('\n\s*', '\n', full_html_template.strip()).format(
        lang_html = lang_html,
        title_html = f'<title>{title_html}</title>\n' if title_html else '',
        css = css,
        errors = ''.join('\n' + error.as_html_str()
                         for error in build_params.progress.get_errors()
                         if not error.consumed),
        content_html = content_html,
        js = js
    )

    with open(build_params.output_file, 'w') as target:
        target.write(full_html)


def disentangle_svgs(root_element):
    all_original_ids = collections.Counter(root_element.xpath('//@id'))

    i = 0
    for svg_element in root_element.xpath('//svg'):
        # Find elements with IDs, and give them new ones.
        id_map = {}
        for id_element in svg_element.xpath('.//*[@id]'):
            orig_id = id_element.get('id')
            # Already-unique IDs are allowed to remain as-is.
            if all_original_ids[orig_id] > 1:
                while True:
                    new_id = f'{orig_id}_{i}'
                    i += 1
                    if new_id not in all_original_ids: break
                id_element.set('id', new_id)
                id_map[orig_id] = new_id

        # Find/convert elements referring to those IDs.
        for ref_element in svg_element.xpath('.//*[@href]'):
            href = ref_element.get('href')
            if href.startswith('#'):
                id = href[1:]
                ref_element.set('href', '#' + id_map.get(id, id))

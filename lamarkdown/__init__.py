'''
# Build Module API

The functions here are to be used by build modules (md_build.py, etc) to define extensions,
variants, css styles, etc. Build modules just need to 'import lamarkdown'.

(The get_params() function further exposes the BuildParams object directly, which permits greater
flexibility.)
'''

from .lib.build_params import BuildParams, Variant
from .lib.resources import ResourceSpec, ContentResourceSpec, UrlResourceSpec
from markdown.extensions import Extension
from lxml.cssselect import CSSSelector

import importlib
import os.path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union


class BuildParamsException(Exception): pass

def _params():
    if BuildParams.current is None:
        raise BuildParamsException(f'Build params not yet initialised')
    return BuildParams.current


def get_build_dir():
    return _params().build_dir

def get_env():
    return _params().env

def get_params():
    return _params()


def name(n: str):
    _params().name = n

def _callable(fn):
    if not callable(fn):
        raise ValueError(f'Expected a function/callable, but received {type(fn).__name__} (value {fn})')

def target(fn: Callable[[str],str]):
    _callable(fn)
    _params().output_namer = fn

def base_name():
    _params().output_namer = lambda t: t

def variants(*args, **kwargs):
    p = _params()
    for variant_fn in args:
        _callable(variant_fn)
        p.variants.append(Variant(name = variant_fn.__name__,
                                  build_fn = variant_fn))

    for name, variant_fn in kwargs.items():
        _callable(variant_fn)
        p.variants.append(Variant(name = name, build_fn = variant_fn))

def prune(selector: Optional[str] = None,
          xpath: Optional[str] = None):

    if selector is None and xpath is None:
        raise ValueError('Must specify at least one argument')

    hook = lambda elem: elem.getparent().remove(elem)

    if selector is not None:
        with_selector(selector, hook)

    if xpath is not None:
        with_xpath(xpath, hook)

def with_selector(selector: str, fn: Callable):
    with_xpath(CSSSelector(selector).path, fn)

def with_xpath(xpath: str, fn: Callable):
    _callable(fn)
    def hook(root):
        for element in root.xpath(xpath):
            fn(element)
    with_tree(hook)

def with_tree(fn: Callable):
    _callable(fn)
    _params().tree_hooks.append(fn)

def extensions(*extensions: Union[str,Extension]):
    for e in extensions:
        extension(e)

def extension(extension: Union[str,Extension], cfg_dict = {}, **cfg_kwargs):
    p = _params()
    new_config = {**cfg_dict, **cfg_kwargs}

    if isinstance(extension, Extension):
        if new_config:
            raise ValueError('Cannot supply configuration values to an already-instantiated Extension')
        else:
            p.obj_extensions.append(extension)
        return None

    else:
        config = p.named_extensions.get(extension)
        if config:
            config.update(new_config)
            return config
        else:
            p.named_extensions[extension] = new_config
            return new_config


def _res_values(value: Union[str,Callable[[Set[str]],Optional[str]]],
                if_xpaths:    Union[str,Iterable[str]] = [],
                if_selectors: Union[str,Iterable[str]] = []
               ) -> Tuple[List[str],Callable[[Set[str]],Optional[str]]]:

    value_factory: Callable[[Set[str]],Optional[str]]

    if callable(value):
        value_factory = value
    elif if_xpaths or if_selectors:
        # If a literal value is given as well as one or more XPath expressions, we'll produce that
        # value if any of the expressions are found.
        value_factory = lambda subset_found: value if subset_found else None
    else:
        # If a literal value is given with no XPaths, then we'll produce that value unconditionally.
        value_factory = lambda _: value

    xpath_iterable    = [if_xpaths]    if isinstance(if_xpaths,    str) else if_xpaths
    selector_iterable = [if_selectors] if isinstance(if_selectors, str) else if_selectors

    xpaths = []
    xpaths.extend(xpath_iterable)
    xpaths.extend(CSSSelector(sel).path for sel in selector_iterable)

    return (xpaths, value_factory)


def css_rule(selectors: Union[str,Iterable[str]], properties: str):
    '''
    Sets a CSS rule, consisting of one or more selectors and a set of properties (together in a
    single string).

    The selector(s) are used at 'compile-time' as well as 'load-time', to determine whether the
    rule becomes part of the output document at all. Only selectors that actually match the
    document are included in the output.
    '''
    if isinstance(selectors, str):
        selectors = [selectors]

    xpath_to_sel = {CSSSelector(sel).path: sel for sel in selectors}

    def content_factory(found: Set[str]) -> Optional[str]:
        if not found: return None
        return ', '.join(xpath_to_sel[xp] for xp in sorted(found)) + ' { ' + properties + ' }'

    _params().css.append(ContentResourceSpec(xpaths_required = list(xpath_to_sel.keys()),
                                             content_factory = content_factory))


def css(content, **kwargs):
    (xpaths_required, content_factory) = _res_values(content, **kwargs)
    _params().css.append(ContentResourceSpec(xpaths_required = xpaths_required,
                                             content_factory = content_factory))

def js(content: str, **kwargs):
    (xpaths_required, content_factory) = _res_values(content, **kwargs)
    _params().js.append(ContentResourceSpec(xpaths_required = xpaths_required,
                                            content_factory = content_factory))

def _url_resources(url_list: List[str],
                   embed: Optional[bool] = None,
                   hash_type: Optional[str] = None,
                   mime_type: Optional[str] = None,
                   **kwargs):
    p = _params()
    for url in url_list:
        (xpaths_required, url_factory) = _res_values(url, **kwargs)
        yield UrlResourceSpec(xpaths_required = xpaths_required,
                              url_factory = url_factory,
                              cache = p.cache,
                              embed = embed,
                              hash_type = hash_type,
                              base_path = p.resource_path or os.path.dirname(os.path.abspath(p.src_file)),
                              mime_type = mime_type,
                              embed_policy = lambda: p.embed_resources,
                              hash_type_policy = lambda: p.resource_hash_type)


def css_files(*url_list: List[str], **kwargs):
    _params().css.extend(_url_resources(url_list, mime_type = 'text/css', **kwargs))


def js_files(*url_list: List[str], **kwargs):
    _params().js.extend(_url_resources(url_list, mime_type = 'text/javascript', **kwargs))


def wrap_content(start: str, end: str):
    p = _params()
    p.content_start = start + p.content_start
    p.content_end += end

def wrap_content_inner(start: str, end: str):
    p = _params()
    p.content_start += start
    p.content_end = end + p.content_end

def embed_resources(embed: Optional[bool] = True):
    _params().embed_resources = embed


def __getattr__(name):
    if name == 'css_vars':
        return _params().css_vars

    try:
        mod = importlib.import_module(f'lamarkdown.mods.{name}')
    except ModuleNotFoundError as e:
        raise AttributeError(f'No such attribute {name} (no such module)') from e

    try:
        apply_fn = getattr(mod, 'apply')
    except AttributeError as e:
        raise AttributeError(f'No such attribute {name} (missing "apply" function)') from e

    return apply_fn

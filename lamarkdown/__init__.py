from lamarkdown.lib.build_params import BuildParams
import markdown
import importlib
from typing import Any, Union

# The functions defined here form (most of) the API exposed to md_build.py setup files.
#
# (The get_params() function further exposes the BuildParams object directly, which permits greater
# flexibility.)

class BuildParamsException(Exception): pass

def __params():
    if BuildParams.current is None:
        raise BuildParamsException(f'Build params not yet initialised')
    return BuildParams.current


def use(*module_names, pkg = 'lamarkdown'):
    """
    Imports a build module, or modules, by name. You can also use the standard 'import' statement,
    but that breaks on live updating, because we need build modules to reload in that case.
    """

    for name in module_names:
        if pkg is None or pkg == '':
            module_spec = importlib.util.find_spec(name)
        else:
            module_spec = importlib.util.find_spec('.' + name, package = pkg)

        if module_spec is None:
            raise BuildParamsException(f'Cannot find module "{name}"')

        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)


def get_build_dir():
    return __params().build_dir

def get_env():
    return __params().env

def get_params():
    return __params()

def variant(name: str, classes: Union[str, list[str], None]):
    if classes is None:
        classes = []
    elif isinstance(classes, str):
        classes = [classes]
    else:
        classes = list(classes)
    __params().variants[name] = classes

def base_variant(classes: Union[str, list[str], None]):
    variant('', classes)

def variants(variant_dict = {}, **variant_kwargs):
    for name, classes in variant_dict.items():
        variant(name, classes)
    for name, classes in variant_kwargs.items():
        variant(name, classes)

def extension(ext: Union[str,markdown.extensions.Extension], config: dict[str,Any] = None):
    if config:
        if isinstance(ext, markdown.extensions.Extension):
            raise BuildParamsException('extension(): the 2nd "config" parameter is only supported when adding an extension by name (string). When adding an extension object directly, configure it directly.')
        else:
            __params().extension_configs[ext] = config

    __params().extensions.append(ext)

def extensions(*extensions: list[Union[str,markdown.extensions.Extension]]):
    __params().extensions.extend(extensions)

def extension_configs(**configs: dict[str,dict[str,Any]]):
    __params().extension_configs.update(configs)

def css(css: str):
    __params().css += css + '\n'

def css_files(css_files: list[str]):
    __params().css_files.extend(css_files)

def js(js: str):
    __params().js += js + '\n'

def js_files(js_files: list[str]):
    __params().js_files.extend(js_files)

def wrap_content(start: str, end: str):
    p = __params()
    p.content_start = start + p.content_start
    p.content_end += content_end

def wrap_content_inner(start: str, end: str):
    p = __params()
    p.content_start += start
    p.content_end = end + p.content_end

from __future__ import annotations
from .build_params import BuildParams

import io
import os.path
import subprocess
from typing import Any, Protocol
from xml.etree import ElementTree


class Formatter(Protocol):
    def __call__(self,
                 source: str, language: str, css_class: str, options: dict[Any, Any], md,
                 *, classes = [], id_value = '', attrs = {}, **kwargs):
        ...


def command_formatter(build_params: BuildParams,
                      command: list[str]) -> Formatter:
    def formatter(source, language, css_class, options, md, **kwargs):

        try:
            build_params.progress.progress(command[0], msg = f'running {command[0]}...')
            proc = subprocess.run(
                command,
                text = True,
                input = source,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )

            if proc.returncode != 0:
                return build_params.progress.error(
                    command[0],
                    msg = f'"{command[0]}" returned error code {proc.returncode}',
                    output = proc.stderr,
                    code = source
                ).as_html_str()

            return proc.stdout

        except Exception as e:
            return build_params.progress.error(command[0], exception = e).as_html_str()

    return formatter


def caching_formatter(build_params: BuildParams,
                      name: str,
                      base_formatter: Formatter) -> Formatter:
    def formatter(source, language, css_class, options, md, **kwargs):
        try:
            # We don't include kwargs in the cache_key, because it's just metadata
            # (id/class/attrs), and shouldn't affect the generation of the HTML.
            cache_key = (source, language, css_class, tuple(sorted((options or {}).items())))

            result = build_params.build_cache.get(cache_key)

            if result is None:
                result = base_formatter(source, language, css_class, options, md, **kwargs)
                build_params.build_cache[cache_key] = result
            else:
                build_params.progress.cache_hit(name)

            return result

        except Exception as e:
            # Not expecting an exception, but any internal errors will be swallowed by
            # pymdownx.superfences.
            return build_params.progress.error(name, exception = e).as_html_str()

    return formatter


def exec_formatter(build_params: BuildParams,
                   name: str,
                   base_formatter: Formatter) -> Formatter:
    def formatter(source, language, css_class, options, md, **kwargs):
        if not build_params.allow_exec:
            return build_params.progress.error(
                name,
                msg = 'The "allow_exec" option is False, so we cannot execute code.'
            ).as_html_str()

        return base_formatter(source, language, css_class, options, md, **kwargs)

    return formatter


def attr_formatter(base_formatter: Formatter) -> Formatter:

    def formatter(source, language, css_class, options, md,
                  classes=[], id_value='', attrs={}, **kwargs):

        html = base_formatter(source, language, css_class, options, md,
                              classes=None, id_value=id_value, attrs=None, **kwargs)

        if css_class or classes or id_value or attrs:

            # Theoretically we don't need to parse the entire html, since we only want to modify
            # the root element, but it's programmatically simpler.
            root = ElementTree.fromstring(html)

            new_classes = [*([css_class] if css_class else []),
                           *classes]
            if len(new_classes) > 0:
                if 'class' in root.attrib:
                    root.attrib['class'] += ' ' + ' '.join(new_classes)
                else:
                    root.attrib['class'] = ' '.join(new_classes)

            if id_value:
                root.set('id', str(id_value))
            if attrs:
                for key, value in attrs.items():
                    root.attrib[key] = str(value)

            return ElementTree.tostring(root, encoding = 'unicode')

        else:
            return html

    return formatter


def matplotlib_formatter(build_params: BuildParams) -> Formatter:
    NAME = 'matplotlib'  # Progress/error messages

    def formatter(source, language, css_class, options, md, **kwargs):
        try:
            # Matplotlib _isn't_ a core dependency of Lamarkdown, so we (try to) import it locally.
            build_params.progress.progress(NAME, msg = 'running code...')
            import matplotlib.pyplot as plot
        except ModuleNotFoundError:
            build_params.progress.error(
                NAME,
                msg = 'Module not found; you may need to run "pip install matplotlib"'
            ).as_html_str()
        else:
            try:
                exec(source, build_params.env)
                buf = io.BytesIO()
                plot.savefig(buf, format = 'svg')
                plot.clf()  # Clear the current figure (so we start from a clean slate next time)
                return buf.getvalue().decode()
            except Exception as e:
                return build_params.progress.error(NAME, exception = e).as_html_str()

    return formatter


def r_plot_formatter(build_params: BuildParams) -> Formatter:

    NAME = 'R'  # Progress/error messages

    base_formatter = command_formatter(build_params, ['R', '-q', '-s'])

    def escape_r_string(s):
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\'', '\\\'')

    def only_svg(s):
        start = s.find('<svg')
        if start == -1:
            return s
        end = s.find('</svg>') + 6
        return s[start:end]

    def formatter(source, language, css_class, options, md, **kwargs):
        try:
            out_file = escape_r_string(os.path.join(build_params.build_dir, 'out.svg'))

            source = f'''
                svg("{out_file}")
                {source}
                graphics.off()
                write(readChar('{out_file}', file.info('{out_file}')$size), stdout())
            '''

            return only_svg(
                base_formatter(source, language, css_class, options, md, **kwargs)
            )

        except Exception as e:
            return build_params.progress.error(NAME, exception = e).as_html_str()

    return formatter

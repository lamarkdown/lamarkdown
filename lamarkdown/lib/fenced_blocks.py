from .build_params import BuildParams

import io
import os.path
import subprocess
from typing import Callable, List

def command_formatter(build_params: BuildParams,
                      command: List[str]):
    def formatter(source, language, css_class, options, md, **kwargs):
        try:
            build_params.progress.progress(command[0], f'Running {command[0]}...')
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
                    f'"{command[0]}" returned error code {proc.returncode}',
                    proc.stderr,
                    source
                ).as_html_str()

            return proc.stdout

        except Exception as e:
            return build_params.progress.error_from_exception(name, e).as_html_str()

    return formatter


def caching_formatter(build_params: BuildParams,
                      name: str,
                      base_formatter: Callable):
    def formatter(source, language, css_class, options, md, **kwargs):
        try:
            cache_key = (source, language, css_class, options)
            result = build_params.cache.get(cache_key)

            if result is None:
                result = base_formatter(source, language, css_class, options, md, **kwargs)
                build_params.cache[cache_key] = result
            else:
                build_params.progress.progress(name, 'Cache hit -- skipping formatting')

            return result

        except Exception as e: # Not expecting an exception, but any internal errors will be
                               # swallowed by pymdownx.superfences.
            return build_params.progress.error_from_exception(name, e).as_html_str()

    return formatter


def exec_formatter(build_params: BuildParams,
                   name: str,
                   base_formatter: Callable):
    def formatter(source, language, css_class, options, md, **kwargs):
        if not build_params.allow_exec:
            return build_params.progress.error(
                name,
                f'The "allow_exec" option is False, so we cannot execute code.'
            ).as_html_str()

        return base_formatter(source, language, css_class, options, md, **kwargs)

    return formatter


def matplotlib_formatter(build_params):
    def formatter(source, language, css_class, options, md, **kwargs):
        try:
            # Matplotlib _isn't_ a core dependency of Lamarkdown, so we (try to) import it locally.
            build_params.progress.progress('matplotlib', f'Invoking matplotlib...')
            import matplotlib.pyplot as plot
        except ModuleNotFoundError:
            build_params.progress.error('matplotlib', 'Module not found; you probably need to run "pip install matplotlib"').as_html_str()
        else:
            try:
                exec(source)
                buf = io.BytesIO()
                plot.savefig(buf, format = 'svg')
                plot.clf() # Clear the current figure (so we start from a clean slate next time)
                return buf.getvalue().decode()
            except Exception as e:
                return build_params.progress.error_from_exception('matplotlib', e).as_html_str()

    return formatter


def r_plot_formatter(build_params: BuildParams):

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
            return build_params.progress.error_from_exception('r', e).as_html_str

    return formatter


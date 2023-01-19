from .build_params import BuildParams

import io
import subprocess
from typing import List

def command_formatter(build_params: BuildParams,
                      command: List[str],
                      title: str):
    def format(source, language, css_class, options, md, **kwargs):
        try:
            proc = subprocess.run(
                command,
                text = True,
                input = source,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )

            if proc.returncode != 0:
                return build_params.progress.error(
                    title,
                    f'"{command[0]}" returned error code {proc.returncode}',
                    proc.stderr,
                    source
                ).as_html_str()

            return proc.stdout

        except Exception as e:
            return build_params.progress.error_from_exception(title, e).as_html_str()

    return format


def matplotlib_formatter(build_params):
    def format(source, language, css_class, options, md, **kwargs):
        if not build_params.allow_exec:
            return build_params.progress.error(
                'Matplotlib',
                f'The "allow_exec" option is False, so we cannot execute any matplotlib code.',
                source
            ).as_html_str()

        try:
            # Matplotlib _isn't_ a core dependency of Lamarkdown, so we (try to) import it locally.
            import matplotlib.pyplot as plot

            exec(source)
            buf = io.BytesIO()
            plot.savefig(buf, format = 'svg')
            plot.clf() # Clear the current figure (so we start from a clean slate next time)
            return buf.getvalue().decode()

        except Exception as e:
            return build_params.progress.error_from_exception('Matplotlib', e).as_html_str()

    return format

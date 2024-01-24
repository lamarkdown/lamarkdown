# mypy: disable-error-code="attr-defined,operator"

import lamarkdown as la
from ..lib import fenced_blocks


def apply():
    for cmd in ['dot', 'neato', 'circo', 'fdp', 'osage', 'patchwork', 'sfdp', 'twopi']:
        la.fenced_block(f'graphviz-{cmd}', la.command_formatter([cmd, '-Tsvg']))

    la.fenced_block('plantuml', la.command_formatter(['plantuml', '-tsvg', '-p']))

    la.fenced_block(
        'matplotlib',
        fenced_blocks.matplotlib_formatter(la.params),
        check_exec = True)

    la.fenced_block(
        'r-plot',
        fenced_blocks.r_plot_formatter(la.params),
        check_exec = True)

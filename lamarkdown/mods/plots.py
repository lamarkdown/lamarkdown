import lamarkdown as la
from ..lib import fenced_blocks

def apply(scale = 1.0):
    for cmd in ['dot', 'neato', 'circo', 'fdp', 'osage', 'patchwork', 'sfdp', 'twopi']:
        la.fenced_command([cmd, '-Tsvg'], f'Graphviz ({cmd})')

    la.fenced_command(['plantuml', '-tsvg', '-p'], 'PlantUML')
    la.fenced_block('matplotlib', fenced_blocks.matplotlib_formatter(la.get_params()))

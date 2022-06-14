import lamarkdown as la

# Based on https://github.com/richleland/pygments-css/blob/master/default.css

def apply():
    for category, colour, font, classes in [
        ('operator', 'red',     '',       ['o', 'ow', 'p']),
        ('comment',  '#c06000', 'italic', ['c', 'ch', 'cm', 'cpf', 'c1', 'cs', 'cp']),
        ('keyword',  'blue',    'bold',   ['k', 'kc', 'kd', 'kn', 'kp', 'kr', 'kt']),
        ('number',   '#008080', '',       ['m', 'mb', 'mf', 'mh', 'mi', 'mo', 'il']),
        ('string',   'green',   '',       ['s', 'sa', 'sb', 'sc', 'dl', 'sd', 's2', 'se', 'sh', 'si', 'sx', 'sr', 's1', 'ss']),
        ('name',     'black',   '',       ['na', 'nb', 'nc', 'no', 'nd', 'ni', 'ne', 'nf', 'nl', 'nn', 'nt', 'nv', 'bp', 'fm', 'vc', 'vg', 'vi', 'vm']),
        ('space',    '#bbbbbb', '',       ['w'])
    ]:
        colour_var = f'la-code-{category}-color'
        font_var = f'la-code-{category}-font'

        la.css_vars[colour_var] = colour
        la.css_vars[font_var] = font or 'inherit'
        # Blank values are not strictly allowed, and 'inherit' is the default behaviour.

        la.css_rule(
            [f'code .{cls}' for cls in classes],
            f'color: var(--{colour_var}); font: var(--{font_var});'
        )

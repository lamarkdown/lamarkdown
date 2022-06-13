import lamarkdown as la

COUNTER_PREFIX = '_lamd_sec_'

def apply(from_level: int = 2, to_level: int = 6, sep = '\u2003', method = 'static'):

    if not (1 <= from_level <= to_level <= 6):
        raise ValueError(f'from_level {from_level} must be <= to_level {to_level}, and both must be between 1 and 6 inclusive.')

    if method == 'static':
        la.extension('lamarkdown.ext.heading_numbers',
                     from_level = from_level,
                     to_level = to_level,
                     sep = sep)

    elif method == 'css':
        la.css(f'body {{ counter-reset: {COUNTER_PREFIX}0; }}')

        def marker(counter_n):
            return ' "." '.join(f'counter({COUNTER_PREFIX}{i})' for i in range(counter_n + 1))

        for level in range(from_level, to_level + 1):
            counter_n = level - from_level
            la.css(
                f'''
                h{level}:not(.notnumbered) {{
                    counter-reset: {COUNTER_PREFIX}{counter_n + 1};
                    counter-increment: {COUNTER_PREFIX}{counter_n};
                }}

                h{level}:not(.notnumbered)::before {{
                    content: {marker(counter_n)};
                    margin-right: 1em;
                }}
                ''',
                if_selectors = f'h{level}:not(.notnumbered)'
            )

    else:
        raise ValueError(f'Unrecognised numbering method: "{method}"')

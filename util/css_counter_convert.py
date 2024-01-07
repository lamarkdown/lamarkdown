#!/usr/bin/python

import argparse
import collections
import re
from textwrap import dedent

HEX_ESCAPE = r'\\[0-9a-fA-F]+'
HEX_ESCAPE_REGEX = re.compile(fr'(?x){HEX_ESCAPE}')

STRING = fr'''
    " ( [^\\"] | \\. )* "
    |
    ' ( [^\\'] | \\. )* '
    |
    ( [A-Za-z0-9_-] | {HEX_ESCAPE} | \\. )+
'''
STRING_REGEX = re.compile(fr'(?x){STRING}')

INTEGER = r'-?[0-9]+'

ADDITIVE_TUPLE_REGEX = re.compile(fr'(?x) (?P<value> {INTEGER} ) \s+ (?P<symbol> {STRING} )')

CSS_COUNTER_REGEX = re.compile(
    fr'''(?x)
    @counter-style \s+ (?P<name> [a-z-]+) \s* \{{ \s*
        system: \s* (?P<system> cyclic | numeric | alphabetic | symbolic | additive |
                     fixed (\s+ (?P<fixed_n> [0-9]+))? |
                     extends\s+(?P<base> [a-z-]+ ) ) \s* ; \s*
        (
            symbols: \s* (?P<symbols> [^;]+) \s* ; \s*
            |
            additive-symbols: \s* (?P<additive_symbols> [^;]+) \s* ; \s*
            |
            negative: \s* (?P<neg_before> {STRING}) (\s+ (?P<neg_after> {STRING}))? \s* ; \s*
            |
            prefix: \s* (?P<prefix> {STRING}) \s* ; \s*
            |
            suffix: \s* (?P<suffix> {STRING}) \s* ; \s*
            |
            range: \s* (?P<range_min> infinite | {INTEGER}) \s+
                       (?P<range_max> infinite | {INTEGER}) \s* ; \s*
            |
            pad: \s* (?P<pad_width> {INTEGER}) \s+ (?P<pad_symbol> {STRING}) \s* ; \s*
            |
            fallback: \s* (?P<fallback> [a-z-]+) \s* ; \s*
        )*
    \}}
    ''')


def oops(msg):
    print(f'\x1b[31;1m[!!]\x1b[m{msg}')

def unescape_hex(match):
    s = match.group()
    assert s[0] == '\\'
    return chr(int(s[1:], base=16))

def unstring(s):
    if len(s) == 0:
        return ''
    if s[0] in '"\'':
        assert s[-1] == s[0]
        s = s[1:-1]
    s = HEX_ESCAPE_REGEX.sub(unescape_hex, s)
    s = re.sub(r'\\(.)', r'\1', s)
    return s

COUNTER_FIELDS = ['symbols', 'additive_symbols', 'negative', 'prefix', 'suffix', 'range', 'pad']

CounterDefn = collections.namedtuple(
    'CounterDefn',
    ['system', 'fallback', *COUNTER_FIELDS])


def main():
    parser = argparse.ArgumentParser(
        prog        = 'css_counter_convert',
        description = 'Supports development on the la.labels extension, by parsing the "normative definitions" of CSS counter types, and generating corresponding code snippets to be embedded within lamarkdown.ext.label_support.counter_types.py.',
    )

    parser.add_argument('input', metavar='FILE', help='Text file containing CSS "@counter-style" definitions.')
    args = parser.parse_args()

    with open(args.input) as r:
        input_css = r.read()

    # Delete comments
    input_css = re.sub('(?s)/\*.*?\*/', '', input_css)

    # Count definitions (for sanity checking)
    n_defns = sum(1 for _ in re.finditer('@counter-style', input_css))

    converted = {}
    init_entries = []
    for match in CSS_COUNTER_REGEX.finditer(input_css):

        name = match.group('name')
        system = match.group('system')

        if system.startswith('extends'):
            base = converted[match.group('base')]
            system = base.system
        else:
            base = CounterDefn(
                system = None,
                fallback = f'self[\'decimal\']',
                symbols = None,
                additive_symbols = None,
                negative = None,
                prefix = None,
                suffix = None,
                range = None,
                pad = None)

        symbols = [unstring(m.group())
                   for m in STRING_REGEX.finditer(match.group('symbols') or '')] or base.symbols

        additive_symbols = [(int(m.group('value')), unstring(m.group('symbol')))
                            for m in ADDITIVE_TUPLE_REGEX.finditer(
                                match.group('additive_symbols') or '')] or base.additive_symbols

        if (neg_before_str := match.group('neg_before')) is not None:
            negative = (unstring(neg_before_str), unstring(match.group('neg_after') or ''))
        else:
            negative = base.negative

        prefix = unstring(match.group('prefix') or '') or base.prefix
        suffix = unstring(match.group('suffix') or '') or base.suffix

        if (range_min_str := match.group('range_min')) is not None:
            range_max_str = match.group('range_max')
            range = (
                None if range_min_str == 'infinite' else int(range_min_str),
                None if range_max_str == 'infinite' else int(range_max_str)
            )
        else:
            range = base.range

        if (pad_width_str := match.group('pad_width')) is not None:
            pad = (int(pad_width_str), unstring(match.group('pad_symbol')))
        else:
            pad = base.pad

        if (fallback_str := match.group('fallback')) is not None:
            fallback = f'self[{repr(fallback_str)}]'
        elif range == (None, None) or (range is None and system in ['cyclic', 'numeric', 'fixed']):
            fallback = None # No fallback needed if the range is infinite
        else:
            fallback = base.fallback

        constructor = {
            'cyclic': 'CyclicCounter',
            'numeric': 'NumericCounter',
            'alphabetic': 'AlphabeticCounter',
            'symbolic': 'SymbolicCounter',
            'additive': 'AdditiveCounter',
            'fixed': 'FixedCounter'
        }[system]

        defn = CounterDefn(
            system = system,
            fallback = fallback,
            symbols = symbols,
            additive_symbols = additive_symbols,
            negative = negative,
            prefix = prefix,
            suffix = suffix,
            range = range,
            pad = pad)
        converted[name] = defn

        parameters = ', '.join(
            f'{field} = {repr(getattr(defn, field))}'
            for field in COUNTER_FIELDS
            if getattr(defn, field) is not None
        )

        if fallback is not None:
            parameters = f'fallback = {fallback}, {parameters}'

        init_entries.append(f'{repr(name)}: lambda: {constructor}({repr(name)}, {parameters})')

    initialisers = (',\n' + ' ' * 20).join(init_entries)
    print(dedent(fr'''
        class StandardCounterTypes:
            'This class is auto-generated by css_counter_convert.py.'
            def __init__(self):
                self._instances = {{}}
                self._initialisers = {{
                    {initialisers}
                }}

            def __getitem__(self, name):
                if ct := self._instances.get(name):
                    return ct

                if init := self._initialisers.get(name):
                    ct = init()
                    self._instances[name] = ct
                    return ct

                raise KeyError(name)
        '''
    ))

    print(f'\nSummary: {n_defns} total, {len(converted)} converted')


if __name__ == '__main__':
    main()

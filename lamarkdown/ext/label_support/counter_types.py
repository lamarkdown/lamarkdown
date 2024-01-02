from abc import ABC
from typing import Dict, List


class CounterType(ABC):
    def __init__(self, css_id: str,
                       fallback: 'CounterType' = None,
                       use_if = lambda count: c > 0, # Use if strictly positive
                       negative = ('-', ''),
                       pad_width = 0,
                       pad_symbol = '0'):
        self._css_id = css_id
        self._fallback = fallback
        self._use_if = use_if
        self._negative = negative
        self._pad_width = pad_width
        self._pad_symbol = pad_symbol
        self._cache = {}

    def format(self, count) -> str:
        fmt = self._cache.get(count)
        if fmt is None:
            if self._use_if(count):
                if count >= 0 or self._negative is False:
                    fmt = self.format_impl(count)
                    prefix = ''
                    suffix = ''
                    pad_width = self._pad_width
                else:
                    fmt = self.format_impl(-count)
                    prefix, suffix = self._negative
                    pad_width = self._pad_width - len(neg_prefix) - len(neg_suffix)

                if fmt is not None:
                    fmt = f'{prefix}{self._pad_symbol * (self._pad_width - len(fmt))}{fmt}{suffix}'

            if fmt is None:
                if self._fallback is not None:
                    fmt = self._fallback.format(count)
                else:
                    fmt = str(count)

            self._cache[count] = fmt

        return fmt

    # def _get_format(self, count):
    #     if self._use_if(count):
    #         fmt = self.format_impl(count)
    #         if fmt is not None:
    #             return fmt
    #     if self._fallback is not None:
    #         return self._fallback.format(count)
    #     else:
    #         return str(count)

    def format_impl(self, count) -> str:
        raise NotImplementedError

    @property
    def css_id(self): return self._name



class NumericCounter(CounterType):
    def __init__(self, css_id: str,
                       symbols: List[str],
                       use_if = lambda _: True, # Always applicable
                       **kwargs):
        super().__init__(css_id, use_if = use_if, **kwargs)
        self._symbols = symbols

    def format_impl(self, count) -> str:
        digits = []
        n_symbols = len(self._symbols)
        while count > 0:
            digits.insert(0, self._symbols[count % n_symbols])
            count //= n_symbols

        if len(digits) == 0:
            return self._symbols[0]
        else:
            return ''.join(digits)


class AlphabeticCounter(CounterType):
    def __init__(self, css_id: str, symbols: List[str], **kwargs):
        super().__init__(css_id, **kwargs)
        self._symbols = symbols

    def format_impl(self, count) -> str:
        digits = []
        n_symbols = len(self._symbols)
        while count > 0:
            digits.insert(0, self._symbols[(count - 1) % n_symbols])
            count = (count - 1) // n_symbols

        return ''.join(digits) or None


class AdditiveCounter(CounterType):
    def __init__(self, css_id: str, symbols: Dict[int,str], **kwargs):
        super().__init__(css_id, **kwargs)
        self._symbols = symbols
        self._symbol_weights = list(symbols.keys())
        self._symbol_weights.sort(reverse = True)

    def format_impl(self, count) -> str:
        digits = io.StringIO()
        for weight in self._symbol_weights:
            symbol = self._symbols[weight]
            while count >= weight:
                digits.write(symbol)
                count -= weight

        return digits.getvalue() or None


class SymbolicCounter(CounterType):
    def __init__(self, css_id: str, symbols: List[str], **kwargs):
        super().__init__(css_id, **kwargs)
        self._symbols = symbols

    def format_impl(self, count) -> str:
        if count == 0: return None
        count -= 1
        n_symbols = len(self._symbols)
        return self._symbols[count % n_symbols] * ((count // n_symbols) + 1)


class CyclicCounter(CounterType):
    def __init__(self, css_id: str, symbols: List[str], **kwargs):
        super().__init__(css_id, negative = False, **kwargs)
        self._symbols = symbols

    def format_impl(self, count) -> str:
        return self._symbols[(count - 1) % len(self._symbols)]


class FixedCounter(CounterType):
    def __init__(self, css_id: str, symbols: List[str], first = 1, **kwargs):
        super().__init__(css_id, negative = False, **kwargs)
        self._symbols = symbols
        self._first = first

    def format_impl(self, count) -> str:
        count -= self._first
        return self._symbols[count] if 0 <= count < len(self._symbols) else None


# class StaticLabeller(CounterType):
#     def __init__(self, css_id: str, symbol: str, **kwargs):
#         super().__init__(css_id, **kwargs)
#         self._symbol = symbol
#
#     def format_impl(self, _count) -> str:
#         return self._symbol


# Reference: https://www.w3.org/TR/predefined-counter-styles

# COUNTER_TYPES = { ct.css_id: ct for ct in [
#     NumericCounter('decimal', '0123456789'),
#     NumericCounter('binary', '01'),
#     NumericCounter('octal', '01234567'),
#     NumericCounter('lower-hexadecimal', '0123456789abcdef'),
#     NumericCounter('upper-hexadecimal', '0123456789ABCDEF'),
#     AlphabeticCounter('lower-alpha', 'abcdefghijklmnopqrstuvwxyz'),
#     AlphabeticCounter('upper-alpha', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
#     AdditiveCounter('lower-roman', {
#         1000: 'm', 900: 'cm', 500: 'd', 400: 'cd', 100: 'c', 90: 'xc', 50: 'l', 40: 'xl',
#         10: 'x', 9: 'ix', 5: 'v', 4: 'iv', 1: 'i'}),
#     AdditiveCounter('upper-roman', {
#         1000: 'M', 900: 'CM', 500: 'D', 400: 'CD', 100: 'C', 90: 'XC', 50: 'L', 40: 'XL',
#         10: 'X', 9: 'IX', 5: 'V', 4: 'IV', 1: 'I'}),
# ]}

_counter_types = {}

ABBREVIATIONS = {
    '1': 'decimal',
    'a': 'lower-alpha',
    'A': 'upper-alpha',
    'i': 'lower-roman',
    'I': 'upper-roman',
}

def get_counter_type(name: str) -> CounterType:
    name = ABBREVIATIONS.get(name, name)

    if name in _counter_types:
        return _counter_types[name]

    counter_fn = {
        'decimal':              lambda: NumericCounter(name, '0123456789'),
        'binary':               lambda: NumericCounter(name, '01'),
        'octal':                lambda: NumericCounter(name, '01234567'),
        'lower-hexadecimal':    lambda: NumericCounter(name, '0123456789abcdef'),
        'upper-hexadecimal':    lambda: NumericCounter(name, '0123456789ABCDEF'),

        'lower-alpha':          lambda: AlphabeticCounter(name, 'abcdefghijklmnopqrstuvwxyz'),
        'lower-latin':          lambda: AlphabeticCounter(name, 'abcdefghijklmnopqrstuvwxyz'),
        'upper-alpha':          lambda: AlphabeticCounter(name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        'upper-latin':          lambda: AlphabeticCounter(name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        'lower-greek':          lambda: AlphabeticCounter(name, 'αβγδεζηθικλμνξοπρστυφχψω'),

        'lower-roman':
            lambda: AdditiveCounter('lower-roman',
            {
                1000: 'm', 900: 'cm', 500: 'd', 400: 'cd', 100: 'c', 90: 'xc', 50: 'l', 40: 'xl',
                10: 'x', 9: 'ix', 5: 'v', 4: 'iv', 1: 'i'
            }),

        'upper-roman':
            lambda: AdditiveCounter('upper-roman',
            {
                1000: 'M', 900: 'CM', 500: 'D', 400: 'CD', 100: 'C', 90: 'XC', 50: 'L', 40: 'XL',
                10: 'X', 9: 'IX', 5: 'V', 4: 'IV', 1: 'I'
            }),

    }.get(name)

    if counter_fn is None:
        return None


    counter = counter_fn()
    _counter_types[name] = counter_fn()
    return counter

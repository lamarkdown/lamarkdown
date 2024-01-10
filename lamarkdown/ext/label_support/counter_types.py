import abc
import io
from typing import Callable, Dict, List, Optional, Tuple

Negative = Tuple[str, str]
Range = Tuple[Optional[int], Optional[int]]
Pad = Tuple[int, str]


class CounterType(abc.ABC):
    def __init__(self,
                 css_id: str,
                 fallback: Optional['CounterType'] = None,
                 negative: Negative = ('-', ''),
                 prefix: str = '',
                 suffix: str = '',
                 range: Range = (1, None),  # By default, use only if strictly positive
                 pad: Pad = (0, '0'),
                 eq_extra: Tuple = (),
                 abs_negative: bool = True):

        self._css_id = css_id
        self._fallback = fallback
        self._negative = negative
        self._prefix = prefix
        self._suffix = suffix
        self._range = range
        self._pad = pad
        self._eq_extra = eq_extra
        self._abs_negative = abs_negative

        self._cache: Dict[int, str] = {}
        self._hash = hash((type(self), css_id, fallback, negative,
                          prefix, suffix, range, pad, eq_extra))

    def format(self, count: int) -> str:
        fmt = self._cache.get(count)
        if fmt is None:

            min, max = self._range
            if (min is None or min <= count) and (max is None or count <= max):

                pad_width, pad_symbol = self._pad
                if count >= 0:
                    fmt = self.format_impl(count)
                    neg_prefix = ''
                    neg_suffix = ''
                else:
                    fmt = self.format_impl((-count) if self._abs_negative else count)
                    neg_prefix, neg_suffix = self._negative
                    pad_width -= len(neg_prefix) + len(neg_suffix)

                if fmt is not None:
                    pad = pad_symbol * (pad_width - len(fmt))
                    fmt = f'{self._prefix}{neg_prefix}{pad}{fmt}{neg_suffix}{self._suffix}'

            if fmt is None:
                if self._fallback is not None:
                    fmt = self._fallback.format(count)
                else:
                    fmt = str(count)

            self._cache[count] = fmt

        return fmt

    @abc.abstractmethod
    def format_impl(self, count) -> Optional[str]:
        ...

    @property
    def css_id(self):
        return self._css_id

    def __eq__(self, other):
        '''
        We avoid needing each subclass to define its own __eq__() logic by:
        1. Checking for type(...)==type(...); and
        2. Having the '_eq_extra' field, which contains arbitrary subclass-specific data.
        '''
        return (
            type(self)              is type(other)
            and self._css_id        == other._css_id
            and self._fallback      == other._fallback
            and self._negative      == other._negative
            and self._prefix        == other._prefix
            and self._suffix        == other._suffix
            and self._range         == other._range
            and self._pad           == other._pad
            and self._eq_extra      == other._eq_extra
        )

    def __hash__(self):
        return self._hash


class NumericCounter(CounterType):
    def __init__(self,
                 css_id: str,
                 symbols: List[str],
                 range: Range = (None, None),  # No min or max; always applicable
                 **kwargs):

        super().__init__(css_id,
                         range = range,
                         eq_extra = tuple(symbols),
                         abs_negative = True,
                         **kwargs)
        self._symbols = symbols

    def format_impl(self, count: int) -> str:
        digits: List[str] = []
        n_symbols = len(self._symbols)
        while count > 0:
            digits.insert(0, self._symbols[count % n_symbols])
            count //= n_symbols

        if len(digits) == 0:
            return self._symbols[0]
        else:
            return ''.join(digits)


class AlphabeticCounter(CounterType):
    def __init__(self,
                 css_id: str,
                 symbols: List[str],
                 range: Range = (1, None),
                 **kwargs):

        super().__init__(css_id, range = range, eq_extra = tuple(symbols), **kwargs)
        self._symbols = symbols

    def format_impl(self, count: int) -> Optional[str]:
        digits: List[str] = []
        n_symbols = len(self._symbols)
        while count > 0:
            digits.insert(0, self._symbols[(count - 1) % n_symbols])
            count = (count - 1) // n_symbols

        return ''.join(digits) or None


class AdditiveCounter(CounterType):
    def __init__(self,
                 css_id: str,
                 additive_symbols: List[Tuple[int, str]],
                 range: Range = (0, None),
                 **kwargs):

        super().__init__(css_id, range = range, eq_extra = tuple(additive_symbols), **kwargs)
        self._symbols = additive_symbols
        self._symbols.sort(reverse = True)

    def format_impl(self, count: int) -> Optional[str]:
        digits = io.StringIO()
        for weight, symbol in self._symbols:
            while count >= weight:
                digits.write(symbol)
                count -= weight
                if weight == 0:
                    break

        if count != 0:
            return None

        return digits.getvalue() or None


class SymbolicCounter(CounterType):
    def __init__(self,
                 css_id: str,
                 symbols: List[str],
                 range: Range = (1, None),
                 **kwargs):

        super().__init__(css_id, range = range, eq_extra = tuple(symbols), **kwargs)
        self._symbols = symbols

    def format_impl(self, count: int) -> Optional[str]:
        if count <= 0:
            return None
        count -= 1
        n_symbols = len(self._symbols)
        return self._symbols[count % n_symbols] * ((count // n_symbols) + 1)


class CyclicCounter(CounterType):
    def __init__(self,
                 css_id: str,
                 symbols: List[str],
                 range: Range = (None, None),
                 negative: Negative = ('', ''),
                 **kwargs):

        super().__init__(css_id,
                         range = range,
                         negative = negative,
                         eq_extra = tuple(symbols),
                         abs_negative = False,
                         **kwargs)
        self._symbols = symbols

    def format_impl(self, count: int) -> str:
        return self._symbols[(count - 1) % len(self._symbols)]


class FixedCounter(CounterType):
    def __init__(self,
                 css_id: str,
                 symbols: List[str],
                 first: int = 1,
                 **kwargs):

        super().__init__(css_id,
                         range = (1, len(symbols)),
                         negative = ('', ''),
                         eq_extra = (*symbols, first),
                         **kwargs)
        self._symbols = symbols
        self._first = first

    def format_impl(self, count: int) -> Optional[str]:
        count -= self._first
        return self._symbols[count] if 0 <= count < len(self._symbols) else None


class ChineseCounter(CounterType):
    '''
    CSS's @counter-style cannot specify Chinese-style counting systems, but the W3C gives an
    algorithm here: https://www.w3.org/TR/css-counter-styles-3/#limited-chinese

    _As I understand it:_

    The systems assign symbols to both digits 0-9 and to 'markers' indicating powers of 10.
    Numbers are constructed from most-significant digits on the left, to least significant on the
    right, with each digit followed by its power marker (10s, 100s, 1000s).

    There are other rules too:

    * There is no marker for power 0, so 0-10 are written with 1 symbol each.
    * There are no trailing zero digits (or markers for zero digits); e.g., 100 is two symbols:
        the '1' digit followed by the 100s marker.
    * Internal zero digits don't need markers, and multiple zeros are collapsed into a one.

    The W3C-provided symbols cover only the range up to 9999, but it is vanishingly unlikely we'd
    need more than that for labelling purposes.
    '''

    def __init__(self,
                 css_id: str,
                 digit_symbols: List[str],
                 power_symbols: List[str],
                 **kwargs):

        # Note: the first element of power_symbols should generally be the empty string.
        # Conceptually it refers to the 1s (power 0) marker.

        assert len(digit_symbols) == 10
        range = 10 ** (len(power_symbols) + 1) - 1
        super().__init__(css_id,
                         range = (-range, range),
                         eq_extra = (*digit_symbols, *power_symbols),
                         abs_negative = True,
                         **kwargs)
        self._digit_symbols = digit_symbols
        self._power_symbols = power_symbols

    def format_impl(self, count: int) -> Optional[str]:
        if count == 0:
            return self._digit_symbols[0]

        digits: List[str] = []
        power = 0
        prev_zero = True
        while count > 0:
            digit_n = count % 10
            if digit_n > 0:
                digits.append(self._power_symbols[power])
                if not (digit_n == 1 and power == 1 and count < 10):
                    # The leading '1' digit (but not the power marker) is ommitted for 10-19.
                    digits.append(self._digit_symbols[digit_n])
                prev_zero = False

            elif not prev_zero:
                # Zero only appears if the previous (next lowest) digit was non-zero.
                digits.append(self._digit_symbols[0])
                prev_zero = True

            count //= 10
            power += 1

        digits.reverse()  # Since we built the list from right-to-left.
        return ''.join(digits)


class EthiopicCounter(CounterType):

    def __init__(self,
                 css_id: str,
                 minor_symbols: List[str],
                 major_symbols: List[str],
                 odd_symbol: str,
                 even_symbol: str,
                 **kwargs):

        super().__init__(css_id,
                         range = (1, None),
                         eq_extra = (*minor_symbols, *major_symbols, odd_symbol, even_symbol),
                         **kwargs)
        self._minor_symbols = minor_symbols
        self._major_symbols = major_symbols
        self._odd_symbol = odd_symbol
        self._even_symbol = even_symbol

        self._n_minors = len(minor_symbols) + 1                 # Generally 10
        self._base = self._n_minors * (len(major_symbols) + 1)  # Generally 100

    def format_impl(self, count: int) -> Optional[str]:
        if count < 1:
            return None

        if count == 1:
            return self._minor_symbols[0]

        digits: List[str] = []
        first = True
        odd = False
        while count > 0:

            group = count % self._base
            if odd and group > 0:
                digits.append(self._odd_symbol)
            elif not odd and not first:
                digits.append(self._even_symbol)

            if not (group == 0
                    or (group == 1 == count)  # count == group at the most-significant group
                    or (group == 1 and odd)):

                minor = group % self._n_minors
                if minor > 0:
                    digits.append(self._minor_symbols[minor - 1])

                major = group // self._n_minors
                if major > 0:
                    digits.append(self._major_symbols[major - 1])

            odd = not odd
            first = False
            count //= self._base

        digits.reverse()  # Since we built the list from right-to-left.
        return ''.join(digits)


class CounterTypeFactory:
    def __init__(self, initialisers: Dict[str, Callable[[], CounterType]]):
        self._instances: Dict[str, CounterType] = {}
        self._initialisers = initialisers

    def __getitem__(self, name):
        if ct := self._instances.get(name):
            return ct

        if init := self._initialisers.get(name):
            ct = init()
            self._instances[name] = ct
            return ct

        return None

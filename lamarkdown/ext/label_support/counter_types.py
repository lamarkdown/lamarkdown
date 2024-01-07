import abc
import io
from typing import Dict, List, Tuple


class CounterType(abc.ABC):
    def __init__(self, css_id: str,
                       fallback: 'CounterType' = None,
                       negative = ('-', ''),
                       prefix = '',
                       suffix = '',
                       range = (1, None), # By default, use only if strictly positive
                       pad = (0, '0'),
                       eq_extra = ()):

        self._css_id = css_id
        self._fallback = fallback
        self._negative = negative
        self._prefix = prefix
        self._suffix = suffix
        self._range = range
        self._pad = pad
        self._eq_extra = eq_extra

        self._cache = {}
        self._hash = hash((type(self), css_id, fallback, negative,
                          prefix, suffix, range, pad, eq_extra))

    def format(self, count: int) -> str:
        fmt = self._cache.get(count)
        if fmt is None:

            min, max = self._range
            if (min is None or min <= count) and (max is None or count <= max):

                pad_width, pad_symbol = self._pad
                # if count >= 0 or self._negative is False:
                if count >= 0:
                    fmt = self.format_impl(count)
                    neg_prefix = ''
                    neg_suffix = ''
                else:
                    fmt = self.format_impl(-count)
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
    def format_impl(self, count) -> str: ...

    @property
    def css_id(self): return self._css_id

    def __eq__(self, other):
        '''
        We avoid needing each subclass to define its own __eq__() logic by:
        1. Checking for type(...)==type(...); and
        2. Having the '_eq_extra' field, which contains arbitrary subclass-specific data.
        '''
        return (
            type(self)              == type(other)
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
    def __init__(self, css_id: str,
                       symbols: List[str],
                       range = (None, None), # No min or max; always applicable
                       **kwargs):
        super().__init__(css_id, range = range, eq_extra = tuple(symbols), **kwargs)
        self._symbols = symbols

    def format_impl(self, count: int) -> str:
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
        super().__init__(css_id, eq_extra = tuple(symbols), **kwargs)
        self._symbols = symbols

    def format_impl(self, count: int) -> str:
        digits = []
        n_symbols = len(self._symbols)
        while count > 0:
            digits.insert(0, self._symbols[(count - 1) % n_symbols])
            count = (count - 1) // n_symbols

        return ''.join(digits) or None


class AdditiveCounter(CounterType):
    def __init__(self, css_id: str, additive_symbols: List[Tuple[int,str]], **kwargs):
        super().__init__(css_id, eq_extra = tuple(additive_symbols), **kwargs)
        self._symbols = additive_symbols
        self._symbols.sort(reverse = True)

    def format_impl(self, count: int) -> str:
        digits = io.StringIO()
        for weight, symbol in self._symbols:
            while count >= weight:
                digits.write(symbol)
                count -= weight

        return digits.getvalue() or None


class SymbolicCounter(CounterType):
    def __init__(self, css_id: str, symbols: List[str], **kwargs):
        super().__init__(css_id, eq_extra = tuple(symbols), **kwargs)
        self._symbols = symbols

    def format_impl(self, count: int) -> str:
        if count == 0: return None
        count -= 1
        n_symbols = len(self._symbols)
        return self._symbols[count % n_symbols] * ((count // n_symbols) + 1)


class CyclicCounter(CounterType):
    def __init__(self, css_id: str, symbols: List[str], **kwargs):
        super().__init__(css_id, eq_extra = tuple(symbols), **kwargs)
        self._symbols = symbols

    def format_impl(self, count: int) -> str:
        return self._symbols[(count - 1) % len(self._symbols)]


class FixedCounter(CounterType):
    def __init__(self, css_id: str, symbols: List[str], first = 1, **kwargs):
        super().__init__(css_id, eq_extra = (*symbols, first), **kwargs)
        self._symbols = symbols
        self._first = first

    def format_impl(self, count: int) -> str:
        count -= self._first
        return self._symbols[count] if 0 <= count < len(self._symbols) else None


ABBREVIATIONS = {
    '1': 'decimal',
    'a': 'lower-alpha',
    'A': 'upper-alpha',
    'i': 'lower-roman',
    'I': 'upper-roman',
}

class StandardCounterTypes:
    'This class is auto-generated by css_counter_convert.py.'
    def __init__(self):
        self._instances = {}
        self._initialisers = {
            'decimal': lambda: NumericCounter('decimal', symbols = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']),
            'decimal-leading-zero': lambda: NumericCounter('decimal-leading-zero', symbols = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], pad = (2, '0')),
            'arabic-indic': lambda: NumericCounter('arabic-indic', symbols = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']),
            'armenian': lambda: AdditiveCounter('armenian', fallback = self['decimal'], additive_symbols = [(9000, 'Ք'), (8000, 'Փ'), (7000, 'Ւ'), (6000, 'Ց'), (5000, 'Ր'), (4000, 'Տ'), (3000, 'Վ'), (2000, 'Ս'), (1000, 'Ռ'), (900, 'Ջ'), (800, 'Պ'), (700, 'Չ'), (600, 'Ո'), (500, 'Շ'), (400, 'Ն'), (300, 'Յ'), (200, 'Մ'), (100, 'Ճ'), (90, 'Ղ'), (80, 'Ձ'), (70, 'Հ'), (60, 'Կ'), (50, 'Ծ'), (40, 'Խ'), (30, 'Լ'), (20, 'Ի'), (10, 'Ժ'), (9, 'Թ'), (8, 'Ը'), (7, 'Է'), (6, 'Զ'), (5, 'Ե'), (4, 'Դ'), (3, 'Գ'), (2, 'Բ'), (1, 'Ա')], range = (1, 9999)),
            'upper-armenian': lambda: AdditiveCounter('upper-armenian', fallback = self['decimal'], additive_symbols = [(9000, 'Ք'), (8000, 'Փ'), (7000, 'Ւ'), (6000, 'Ց'), (5000, 'Ր'), (4000, 'Տ'), (3000, 'Վ'), (2000, 'Ս'), (1000, 'Ռ'), (900, 'Ջ'), (800, 'Պ'), (700, 'Չ'), (600, 'Ո'), (500, 'Շ'), (400, 'Ն'), (300, 'Յ'), (200, 'Մ'), (100, 'Ճ'), (90, 'Ղ'), (80, 'Ձ'), (70, 'Հ'), (60, 'Կ'), (50, 'Ծ'), (40, 'Խ'), (30, 'Լ'), (20, 'Ի'), (10, 'Ժ'), (9, 'Թ'), (8, 'Ը'), (7, 'Է'), (6, 'Զ'), (5, 'Ե'), (4, 'Դ'), (3, 'Գ'), (2, 'Բ'), (1, 'Ա')], range = (1, 9999)),
            'lower-armenian': lambda: AdditiveCounter('lower-armenian', fallback = self['decimal'], additive_symbols = [(9000, 'ք'), (8000, 'փ'), (7000, 'ւ'), (6000, 'ց'), (5000, 'ր'), (4000, 'տ'), (3000, 'վ'), (2000, 'ս'), (1000, 'ռ'), (900, 'ջ'), (800, 'պ'), (700, 'չ'), (600, 'ո'), (500, 'շ'), (400, 'ն'), (300, 'յ'), (200, 'մ'), (100, 'ճ'), (90, 'ղ'), (80, 'ձ'), (70, 'հ'), (60, 'կ'), (50, 'ծ'), (40, 'խ'), (30, 'լ'), (20, 'ի'), (10, 'ժ'), (9, 'թ'), (8, 'ը'), (7, 'է'), (6, 'զ'), (5, 'ե'), (4, 'դ'), (3, 'գ'), (2, 'բ'), (1, 'ա')], range = (1, 9999)),
            'bengali': lambda: NumericCounter('bengali', symbols = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯']),
            'cambodian': lambda: NumericCounter('cambodian', symbols = ['០', '១', '២', '៣', '៤', '៥', '៦', '៧', '៨', '៩']),
            'khmer': lambda: NumericCounter('khmer', symbols = ['០', '១', '២', '៣', '៤', '៥', '៦', '៧', '៨', '៩']),
            'cjk-decimal': lambda: NumericCounter('cjk-decimal', fallback = self['decimal'], symbols = ['〇', '一', '二', '三', '四', '五', '六', '七', '八', '九'], suffix = '、', range = (0, None)),
            'devanagari': lambda: NumericCounter('devanagari', symbols = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९']),
            'georgian': lambda: AdditiveCounter('georgian', fallback = self['decimal'], additive_symbols = [(10000, 'ჵ'), (9000, 'ჰ'), (8000, 'ჯ'), (7000, 'ჴ'), (6000, 'ხ'), (5000, 'ჭ'), (4000, 'წ'), (3000, 'ძ'), (2000, 'ც'), (1000, 'ჩ'), (900, 'შ'), (800, 'ყ'), (700, 'ღ'), (600, 'ქ'), (500, 'ფ'), (400, 'ჳ'), (300, 'ტ'), (200, 'ს'), (100, 'რ'), (90, 'ჟ'), (80, 'პ'), (70, 'ო'), (60, 'ჲ'), (50, 'ნ'), (40, 'მ'), (30, 'ლ'), (20, 'კ'), (10, 'ი'), (9, 'თ'), (8, 'ჱ'), (7, 'ზ'), (6, 'ვ'), (5, 'ე'), (4, 'დ'), (3, 'გ'), (2, 'ბ'), (1, 'ა')], range = (1, 19999)),
            'gujarati': lambda: NumericCounter('gujarati', symbols = ['૦', '૧', '૨', '૩', '૪', '૫', '૬', '૭', '૮', '૯']),
            'gurmukhi': lambda: NumericCounter('gurmukhi', symbols = ['੦', '੧', '੨', '੩', '੪', '੫', '੬', '੭', '੮', '੯']),
            'hebrew': lambda: AdditiveCounter('hebrew', fallback = self['decimal'], additive_symbols = [(10000, 'י׳'), (9000, 'ט׳'), (8000, 'ח׳'), (7000, 'ז׳'), (6000, 'ו׳'), (5000, 'ה׳'), (4000, 'ד׳'), (3000, 'ג׳'), (2000, 'ב׳'), (1000, 'א׳'), (400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'), (60, 'ס'), (50, 'נ'), (40, 'מ'), (30, 'ל'), (20, 'כ'), (19, 'יט'), (18, 'יח'), (17, 'יז'), (16, 'טז'), (15, 'טו'), (10, 'י'), (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'), (3, 'ג'), (2, 'ב'), (1, 'א')], range = (1, 10999)),
            'kannada': lambda: NumericCounter('kannada', symbols = ['೦', '೧', '೨', '೩', '೪', '೫', '೬', '೭', '೮', '೯']),
            'lao': lambda: NumericCounter('lao', symbols = ['໐', '໑', '໒', '໓', '໔', '໕', '໖', '໗', '໘', '໙']),
            'malayalam': lambda: NumericCounter('malayalam', symbols = ['൦', '൧', '൨', '൩', '൪', '൫', '൬', '൭', '൮', '൯']),
            'mongolian': lambda: NumericCounter('mongolian', symbols = ['᠐', '᠑', '᠒', '᠓', '᠔', '᠕', '᠖', '᠗', '᠘', '᠙']),
            'myanmar': lambda: NumericCounter('myanmar', symbols = ['၀', '၁', '၂', '၃', '၄', '၅', '၆', '၇', '၈', '၉']),
            'oriya': lambda: NumericCounter('oriya', symbols = ['୦', '୧', '୨', '୩', '୪', '୫', '୬', '୭', '୮', '୯']),
            'persian': lambda: NumericCounter('persian', symbols = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']),
            'lower-roman': lambda: AdditiveCounter('lower-roman', fallback = self['decimal'], additive_symbols = [(1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'), (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')], range = (1, 3999)),
            'upper-roman': lambda: AdditiveCounter('upper-roman', fallback = self['decimal'], additive_symbols = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')], range = (1, 3999)),
            'tamil': lambda: NumericCounter('tamil', symbols = ['௦', '௧', '௨', '௩', '௪', '௫', '௬', '௭', '௮', '௯']),
            'telugu': lambda: NumericCounter('telugu', symbols = ['౦', '౧', '౨', '౩', '౪', '౫', '౬', '౭', '౮', '౯']),
            'thai': lambda: NumericCounter('thai', symbols = ['๐', '๑', '๒', '๓', '๔', '๕', '๖', '๗', '๘', '๙']),
            'tibetan': lambda: NumericCounter('tibetan', symbols = ['༠', '༡', '༢', '༣', '༤', '༥', '༦', '༧', '༨', '༩']),
            'lower-alpha': lambda: AlphabeticCounter('lower-alpha', fallback = self['decimal'], symbols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']),
            'lower-latin': lambda: AlphabeticCounter('lower-latin', fallback = self['decimal'], symbols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']),
            'upper-alpha': lambda: AlphabeticCounter('upper-alpha', fallback = self['decimal'], symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']),
            'upper-latin': lambda: AlphabeticCounter('upper-latin', fallback = self['decimal'], symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']),
            'lower-greek': lambda: AlphabeticCounter('lower-greek', fallback = self['decimal'], symbols = ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω']),
            'hiragana': lambda: AlphabeticCounter('hiragana', fallback = self['decimal'], symbols = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ', 'さ', 'し', 'す', 'せ', 'そ', 'た', 'ち', 'つ', 'て', 'と', 'な', 'に', 'ぬ', 'ね', 'の', 'は', 'ひ', 'ふ', 'へ', 'ほ', 'ま', 'み', 'む', 'め', 'も', 'や', 'ゆ', 'よ', 'ら', 'り', 'る', 'れ', 'ろ', 'わ', 'ゐ', 'ゑ', 'を', 'ん'], suffix = '、'),
            'hiragana-iroha': lambda: AlphabeticCounter('hiragana-iroha', fallback = self['decimal'], symbols = ['い', 'ろ', 'は', 'に', 'ほ', 'へ', 'と', 'ち', 'り', 'ぬ', 'る', 'を', 'わ', 'か', 'よ', 'た', 'れ', 'そ', 'つ', 'ね', 'な', 'ら', 'む', 'う', 'ゐ', 'の', 'お', 'く', 'や', 'ま', 'け', 'ふ', 'こ', 'え', 'て', 'あ', 'さ', 'き', 'ゆ', 'め', 'み', 'し', 'ゑ', 'ひ', 'も', 'せ', 'す'], suffix = '、'),
            'katakana': lambda: AlphabeticCounter('katakana', fallback = self['decimal'], symbols = ['ア', 'イ', 'ウ', 'エ', 'オ', 'カ', 'キ', 'ク', 'ケ', 'コ', 'サ', 'シ', 'ス', 'セ', 'ソ', 'タ', 'チ', 'ツ', 'テ', 'ト', 'ナ', 'ニ', 'ヌ', 'ネ', 'ノ', 'ハ', 'ヒ', 'フ', 'ヘ', 'ホ', 'マ', 'ミ', 'ム', 'メ', 'モ', 'ヤ', 'ユ', 'ヨ', 'ラ', 'リ', 'ル', 'レ', 'ロ', 'ワ', 'ヰ', 'ヱ', 'ヲ', 'ン'], suffix = '、'),
            'katakana-iroha': lambda: AlphabeticCounter('katakana-iroha', fallback = self['decimal'], symbols = ['イ', 'ロ', 'ハ', 'ニ', 'ホ', 'ヘ', 'ト', 'チ', 'リ', 'ヌ', 'ル', 'ヲ', 'ワ', 'カ', 'ヨ', 'タ', 'レ', 'ソ', 'ツ', 'ネ', 'ナ', 'ラ', 'ム', 'ウ', 'ヰ', 'ノ', 'オ', 'ク', 'ヤ', 'マ', 'ケ', 'フ', 'コ', 'エ', 'テ', 'ア', 'サ', 'キ', 'ユ', 'メ', 'ミ', 'シ', 'ヱ', 'ヒ', 'モ', 'セ', 'ス'], suffix = '、'),
            'cjk-earthly-branch': lambda: FixedCounter('cjk-earthly-branch', fallback = self['cjk-decimal'], symbols = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'], suffix = '、'),
            'cjk-heavenly-stem': lambda: FixedCounter('cjk-heavenly-stem', fallback = self['cjk-decimal'], symbols = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'], suffix = '、'),
            'japanese-informal': lambda: AdditiveCounter('japanese-informal', fallback = self['cjk-decimal'], additive_symbols = [(9000, '九千'), (8000, '八千'), (7000, '七千'), (6000, '六千'), (5000, '五千'), (4000, '四千'), (3000, '三千'), (2000, '二千'), (1000, '千'), (900, '九百'), (800, '八百'), (700, '七百'), (600, '六百'), (500, '五百'), (400, '四百'), (300, '三百'), (200, '二百'), (100, '百'), (90, '九十'), (80, '八十'), (70, '七十'), (60, '六十'), (50, '五十'), (40, '四十'), (30, '三十'), (20, '二十'), (10, '十'), (9, '九'), (8, '八'), (7, '七'), (6, '六'), (5, '五'), (4, '四'), (3, '三'), (2, '二'), (1, '一'), (0, '〇')], negative = ('マイナス', ''), suffix = '、', range = (-9999, 9999)),
            'japanese-formal': lambda: AdditiveCounter('japanese-formal', fallback = self['cjk-decimal'], additive_symbols = [(9000, '九阡'), (8000, '八阡'), (7000, '七阡'), (6000, '六阡'), (5000, '伍阡'), (4000, '四阡'), (3000, '参阡'), (2000, '弐阡'), (1000, '壱阡'), (900, '九百'), (800, '八百'), (700, '七百'), (600, '六百'), (500, '伍百'), (400, '四百'), (300, '参百'), (200, '弐百'), (100, '壱百'), (90, '九拾'), (80, '八拾'), (70, '七拾'), (60, '六拾'), (50, '伍拾'), (40, '四拾'), (30, '参拾'), (20, '弐拾'), (10, '壱拾'), (9, '九'), (8, '八'), (7, '七'), (6, '六'), (5, '伍'), (4, '四'), (3, '参'), (2, '弐'), (1, '壱'), (0, '零')], negative = ('マイナス', ''), suffix = '、', range = (-9999, 9999)),
            'korean-hangul-formal': lambda: AdditiveCounter('korean-hangul-formal', fallback = self['cjk-decimal'], additive_symbols = [(9000, '구천'), (8000, '팔천'), (7000, '칠천'), (6000, '육천'), (5000, '오천'), (4000, '사천'), (3000, '삼천'), (2000, '이천'), (1000, '일천'), (900, '구백'), (800, '팔백'), (700, '칠백'), (600, '육백'), (500, '오백'), (400, '사백'), (300, '삼백'), (200, '이백'), (100, '일백'), (90, '구십'), (80, '팔십'), (70, '칠십'), (60, '육십'), (50, '오십'), (40, '사십'), (30, '삼십'), (20, '이십'), (10, '일십'), (9, '구'), (8, '팔'), (7, '칠'), (6, '육'), (5, '오'), (4, '사'), (3, '삼'), (2, '이'), (1, '일'), (0, '영')], negative = ('마이너스  ', ''), suffix = ', ', range = (-9999, 9999)),
            'korean-hanja-informal': lambda: AdditiveCounter('korean-hanja-informal', fallback = self['cjk-decimal'], additive_symbols = [(9000, '九千'), (8000, '八千'), (7000, '七千'), (6000, '六千'), (5000, '五千'), (4000, '四千'), (3000, '三千'), (2000, '二千'), (1000, '千'), (900, '九百'), (800, '八百'), (700, '七百'), (600, '六百'), (500, '五百'), (400, '四百'), (300, '三百'), (200, '二百'), (100, '百'), (90, '九十'), (80, '八十'), (70, '七十'), (60, '六十'), (50, '五十'), (40, '四十'), (30, '三十'), (20, '二十'), (10, '十'), (9, '九'), (8, '八'), (7, '七'), (6, '六'), (5, '五'), (4, '四'), (3, '三'), (2, '二'), (1, '一'), (0, '零')], negative = ('마이너스  ', ''), suffix = ', ', range = (-9999, 9999)),
            'korean-hanja-formal': lambda: AdditiveCounter('korean-hanja-formal', fallback = self['cjk-decimal'], additive_symbols = [(9000, '九仟'), (8000, '八仟'), (7000, '七仟'), (6000, '六仟'), (5000, '五仟'), (4000, '四仟'), (3000, '參仟'), (2000, '貳仟'), (1000, '壹仟'), (900, '九百'), (800, '八百'), (700, '七百'), (600, '六百'), (500, '五百'), (400, '四百'), (300, '參百'), (200, '貳百'), (100, '壹百'), (90, '九拾'), (80, '八拾'), (70, '七拾'), (60, '六拾'), (50, '五拾'), (40, '四拾'), (30, '參拾'), (20, '貳拾'), (10, '壹拾'), (9, '九'), (8, '八'), (7, '七'), (6, '六'), (5, '五'), (4, '四'), (3, '參'), (2, '貳'), (1, '壹'), (0, '零')], negative = ('마이너스  ', ''), suffix = ', ', range = (-9999, 9999)),
            'binary': lambda: NumericCounter('binary', symbols = ['0', '1']),
            'lower-hexadecimal': lambda: NumericCounter('lower-hexadecimal', symbols = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']),
            'octal': lambda: NumericCounter('octal', symbols = ['0', '1', '2', '3', '4', '5', '6', '7']),
            'upper-hexadecimal': lambda: NumericCounter('upper-hexadecimal', symbols = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']),
            'afar': lambda: AlphabeticCounter('afar', fallback = self['decimal'], symbols = ['ሀ', 'ለ', 'ሐ', 'መ', 'ረ', 'ሰ', 'በ', 'ተ', 'ነ', 'አ', 'ከ', 'ወ', 'ዐ', 'የ', 'ደ', 'ዸ', 'ገ', 'ጸ', 'ፈ'], suffix = '፦ '),
            'ethiopic-halehame': lambda: AlphabeticCounter('ethiopic-halehame', fallback = self['decimal'], symbols = ['ሀ', 'ለ', 'ሐ', 'መ', 'ሠ', 'ረ', 'ሰ', 'ቀ', 'በ', 'ተ', 'ኀ', 'ነ', 'አ', 'ከ', 'ወ', 'ዐ', 'ዘ', 'የ', 'ደ', 'ገ', 'ጠ', 'ጰ', 'ጸ', 'ፀ', 'ፈ', 'ፐ'], suffix = '፦ '),
            'ethiopic-halehame-am': lambda: AlphabeticCounter('ethiopic-halehame-am', fallback = self['decimal'], symbols = ['ሀ', 'ለ', 'ሐ', 'መ', 'ሠ', 'ረ', 'ሰ', 'ሸ', 'ቀ', 'በ', 'ተ', 'ቸ', 'ኀ', 'ነ', 'ኘ', 'አ', 'ከ', 'ኸ', 'ወ', 'ዐ', 'ዘ', 'ዠ', 'የ', 'ደ', 'ጀ', 'ገ', 'ጠ', 'ጨ', 'ጰ', 'ጸ', 'ፀ', 'ፈ', 'ፐ'], suffix = '፦ '),
            'ethiopic-halehame-ti-er': lambda: AlphabeticCounter('ethiopic-halehame-ti-er', fallback = self['decimal'], symbols = ['ሀ', 'ለ', 'ሐ', 'መ', 'ረ', 'ሰ', 'ሸ', 'ቀ', 'ቐ', 'በ', 'ተ', 'ቸ', 'ነ', 'ኘ', 'አ', 'ከ', 'ኸ', 'ወ', 'ዐ', 'ዘ', 'ዠ', 'የ', 'ደ', 'ጀ', 'ገ', 'ጠ', 'ጨ', 'ጰ', 'ጸ', 'ፈ', 'ፐ'], suffix = '፦ '),
            'ethiopic-halehame-ti-et': lambda: AlphabeticCounter('ethiopic-halehame-ti-et', fallback = self['decimal'], symbols = ['ሀ', 'ለ', 'ሐ', 'መ', 'ሠ', 'ረ', 'ሰ', 'ሸ', 'ቀ', 'ቐ', 'በ', 'ተ', 'ቸ', 'ኀ', 'ነ', 'ኘ', 'አ', 'ከ', 'ኸ', 'ወ', 'ዐ', 'ዘ', 'ዠ', 'የ', 'ደ', 'ጀ', 'ገ', 'ጠ', 'ጨ', 'ጰ', 'ጸ', 'ፀ', 'ፈ', 'ፐ'], suffix = '፦ '),
            'oromo': lambda: AlphabeticCounter('oromo', fallback = self['decimal'], symbols = ['ሀ', 'ለ', 'መ', 'ረ', 'ሰ', 'ሸ', 'ቀ', 'በ', 'ተ', 'ቸ', 'ነ', 'ኘ', 'አ', 'ከ', 'ወ', 'የ', 'ደ', 'ዸ', 'ጀ', 'ገ', 'ጠ', 'ጨ', 'ጰ', 'ጸ', 'ፈ'], suffix = '፦ '),
            'sidama': lambda: AlphabeticCounter('sidama', fallback = self['decimal'], symbols = ['ሀ', 'ለ', 'መ', 'ረ', 'ሰ', 'ሸ', 'ቀ', 'በ', 'ተ', 'ቸ', 'ነ', 'ኘ', 'አ', 'ከ', 'ወ', 'የ', 'ደ', 'ዸ', 'ጀ', 'ገ', 'ጠ', 'ጨ', 'ጰ', 'ጸ', 'ፈ'], suffix = '፦ '),
            'tigre': lambda: AlphabeticCounter('tigre', fallback = self['decimal'], symbols = ['ሀ', 'ለ', 'ሐ', 'መ', 'ረ', 'ሰ', 'ሸ', 'ቀ', 'በ', 'ተ', 'ቸ', 'ነ', 'አ', 'ከ', 'ወ', 'ዐ', 'ዘ', 'የ', 'ደ', 'ጀ', 'ገ', 'ጠ', 'ጨ', 'ጰ', 'ጸ', 'ፈ', 'ፐ'], suffix = '፦ '),
            'urdu': lambda: NumericCounter('urdu', symbols = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'])
        }

    def __getitem__(self, name):
        if ct := self._instances.get(name):
            return ct

        if init := self._initialisers.get(name):
            ct = init()
            self._instances[name] = ct
            return ct

        raise KeyError(name)


_counter_types = StandardCounterTypes()

def get_counter_type(name: str) -> CounterType:
    return _counter_types[ABBREVIATIONS.get(name, name)]

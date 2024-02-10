from lamarkdown.ext.label_support.counter_types import (
    AdditiveCounter, AlphabeticCounter, CounterType, CyclicCounter, FixedCounter, NumericCounter,
    SymbolicCounter)
from lamarkdown.ext.label_support.standard_counter_types import get_counter_type
import unittest
from hamcrest import assert_that, equal_to


class CounterTypesTestCase(unittest.TestCase):

    def test_get_counter_type_basic(self):
        for (names,                 value, string) in [
            (['1', 'decimal'],      1,     '1'),
            (['1', 'decimal'],      9,     '9'),
            (['1', 'decimal'],      91,    '91'),
            (['1', 'decimal'],      999,   '999'),
            (['binary'],            1,     '1'),
            (['binary'],            9,     '1001'),
            (['binary'],            91,    '1011011'),
            (['binary'],            999,   '1111100111'),
            (['octal'],             1,     '1'),
            (['octal'],             9,     '11'),
            (['octal'],             91,    '133'),
            (['octal'],             999,   '1747'),
            (['lower-hexadecimal'], 1,     '1'),
            (['lower-hexadecimal'], 9,     '9'),
            (['lower-hexadecimal'], 91,    '5b'),
            (['lower-hexadecimal'], 999,   '3e7'),
            (['upper-hexadecimal'], 1,     '1'),
            (['upper-hexadecimal'], 9,     '9'),
            (['upper-hexadecimal'], 91,    '5B'),
            (['upper-hexadecimal'], 999,   '3E7'),

            (['decimal-leading-zero'], 1,   '01'),
            (['decimal-leading-zero'], 9,   '09'),
            (['decimal-leading-zero'], 91,  '91'),
            (['decimal-leading-zero'], 999, '999'),

            (['a', 'lower-alpha', 'lower-latin'],   1,     'a'),
            (['a', 'lower-alpha', 'lower-latin'],   9,     'i'),
            (['a', 'lower-alpha', 'lower-latin'],   91,    'cm'),
            (['a', 'lower-alpha', 'lower-latin'],   999,   'alk'),
            (['A', 'upper-alpha', 'upper-latin'],   1,     'A'),
            (['A', 'upper-alpha', 'upper-latin'],   9,     'I'),
            (['A', 'upper-alpha', 'upper-latin'],   91,    'CM'),
            (['A', 'upper-alpha', 'upper-latin'],   999,   'ALK'),

            (['i', 'lower-roman'],                  1,     'i'),
            (['i', 'lower-roman'],                  9,     'ix'),
            (['i', 'lower-roman'],                  91,    'xci'),
            (['i', 'lower-roman'],                  999,   'cmxcix'),
            (['I', 'upper-roman'],                  1,     'I'),
            (['I', 'upper-roman'],                  9,     'IX'),
            (['I', 'upper-roman'],                  91,    'XCI'),
            (['I', 'upper-roman'],                  999,   'CMXCIX'),
        ]:
            for name in names:
                assert_that(
                    get_counter_type(name).format(value),
                    equal_to(string),
                    f'counter "{name}" for value {value} expected to give "{string}"')


    def test_get_counter_type_i18n(self):
        for (name, all_symbols, other_samples) in [
            (
                'lower-greek',
                ['0', 'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο',
                 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω'],
                [(25, 'αα'), (51, 'βγ')]
            ),
            (
                'ethiopic-numeric',
                ['0', '፩', '፪', '፫', '፬', '፭', '፮', '፯', '፰', '፱',  # 0-9
                 '፲', '፲፩', '፲፪', '፲፫', '፲፬', '፲፭', '፲፮', '፲፯', '፲፰', '፲፱',  # 10-19
                 '፳'],  # 20
                [
                    (30, '፴'), (40, '፵'), (50, '፶'), (60, '፷'), (70, '፸'), (80, '፹'), (90, '፺'),

                    # https://www.w3.org/TR/css-counter-styles-3/#ethiopic-numeric-counter-style
                    (100, '፻'), (78010092, '፸፰፻፩፼፺፪'), (780100000092, '፸፰፻፩፼፼፺፪'),

                    # https://www.w3.org/TR/predefined-counter-styles/#ethiopic-numeric
                    (111, '፻፲፩'), (222, '፪፻፳፪'), (333, '፫፻፴፫'), (444, '፬፻፵፬'),

                    # https://en.wikipedia.org/wiki/Ge%CA%BDez_script#Numerals
                    (475, '፬፻፸፭'), (83692, '፰፼፴፮፻፺፪')
                ]
            ),
            (
                'simp-chinese-informal',
                ['零、', '一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、',
                 '十、', '十一、', '十二、', '十三、', '十四、', '十五、', '十六、', '十七、', '十八、', '十九、',
                 '二十、', '二十一、'],
                [
                    (-1, '负一、'), (-9, '负九、'), (-120, '负一百二十、'),

                    # https://www.w3.org/TR/css-counter-styles-3/#limited-chinese
                    (30, '三十、'), (40, '四十、'), (50, '五十、'), (60, '六十、'), (70, '七十、'), (80, '八十、'),
                    (90, '九十、'), (100, '一百、'), (105, '一百零五、'), (110, '一百一十、'), (120, '一百二十、'),

                    # https://www.w3.org/TR/predefined-counter-styles/#simp-chinese-informal
                    (111, '一百一十一、'), (222, '二百二十二、'), (333, '三百三十三、'), (444, '四百四十四、'),
                ]
            ),
            (
                'simp-chinese-formal',
                ['零、', '壹、', '贰、', '叁、', '肆、', '伍、', '陆、', '柒、', '捌、', '玖、',
                 '拾、', '拾壹、', '拾贰、', '拾叁、', '拾肆、', '拾伍、', '拾陆、', '拾柒、', '拾捌、', '拾玖、',
                 '贰拾、', '贰拾壹、'],
                [
                    (-1, '负壹、'), (-9, '负玖、'), (-120, '负壹佰贰拾、'),
                    (30, '叁拾、'), (40, '肆拾、'), (50, '伍拾、'), (60, '陆拾、'), (70, '柒拾、'), (80, '捌拾、'),
                    (90, '玖拾、'), (100, '壹佰、'), (105, '壹佰零伍、'), (110, '壹佰壹拾、'), (120, '壹佰贰拾、'),

                    # https://www.w3.org/TR/predefined-counter-styles/#simp-chinese-formal
                    (111, '壹佰壹拾壹、'), (222, '贰佰贰拾贰、'), (333, '叁佰叁拾叁、'), (444, '肆佰肆拾肆、'),
                ]
            ),
            (
                'trad-chinese-informal',
                ['零、', '一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、',
                 '十、', '十一、', '十二、', '十三、', '十四、', '十五、', '十六、', '十七、', '十八、', '十九、',
                 '二十、', '二十一、'],
                [
                    (-1, '負一、'), (-9, '負九、'), (-120, '負一百二十、'),
                    (30, '三十、'), (40, '四十、'), (50, '五十、'), (60, '六十、'), (70, '七十、'), (80, '八十、'),
                    (90, '九十、'), (100, '一百、'), (105, '一百零五、'), (110, '一百一十、'), (120, '一百二十、'),

                    # https://www.w3.org/TR/predefined-counter-styles/#trad-chinese-informal
                    (111, '一百一十一、'), (222, '二百二十二、'), (333, '三百三十三、'), (444, '四百四十四、'),
                ]

            ),
            (
                'trad-chinese-formal',
                ['零、', '壹、', '貳、', '參、', '肆、', '伍、', '陸、', '柒、', '捌、', '玖、',
                 '拾、', '拾壹、', '拾貳、', '拾參、', '拾肆、', '拾伍、', '拾陸、', '拾柒、', '拾捌、', '拾玖、',
                 '貳拾、', '貳拾壹、'],
                [
                    (-1, '負壹、'), (-9, '負玖、'), (-120, '負壹佰貳拾、'),
                    (30, '參拾、'), (40, '肆拾、'), (50, '伍拾、'), (60, '陸拾、'), (70, '柒拾、'), (80, '捌拾、'),
                    (90, '玖拾、'), (100, '壹佰、'), (105, '壹佰零伍、'), (110, '壹佰壹拾、'), (120, '壹佰貳拾、'),

                    # https://www.w3.org/TR/predefined-counter-styles/#trad-chinese-formal
                    (111, '壹佰壹拾壹、'), (222, '貳佰貳拾貳、'), (333, '參佰參拾參、'), (444, '肆佰肆拾肆、'),
                ]

            ),
        ]:
            counter = get_counter_type(name)
            for (value, string) in enumerate(all_symbols, start = 0):
                assert_that(
                    counter.format(value),
                    equal_to(string),
                    f'counter "{name}" for value {value} expected to give "{string}"')

            for (value, string) in other_samples:
                assert_that(
                    counter.format(value),
                    equal_to(string),
                    f'counter "{name}" for value {value} expected to give "{string}"')


    def test_numeric_counter(self):
        counter = NumericCounter('mock_css_id', '01234')
        for (value, string) in [
            (0,     '0'),
            (1,     '1'),
            (4,     '4'),
            (5,     '10'),
            (24,    '44'),
            (25,    '100'),
            (-1,    '-1'),
            (-24,   '-44'),
        ]:
            assert_that(counter.format(value), equal_to(string))


    def test_alphabetic_counter(self):
        counter = AlphabeticCounter('mock_css_id', 'abcde')
        for (value, string) in [
            (-1,    '-1'),  # Fallback
            (0,     '0'),   # Fallback
            (1,     'a'),
            (2,     'b'),
            (5,     'e'),
            (6,     'aa'),
            (30,    'ee'),
            (31,    'aaa'),
        ]:
            assert_that(counter.format(value), equal_to(string))


    def test_additive_counter(self):
        counter = AdditiveCounter('mock_css_id',
                                  [(10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')])
        for (value, string) in [
            (-1,    '-1'),  # Fallback
            (0,     '0'),   # Fallback
            (1,     'i'),
            (2,     'ii'),
            (3,     'iii'),
            (4,     'iv'),
            (5,     'v'),
            (6,     'vi'),
            (7,     'vii'),
            (8,     'viii'),
            (9,     'ix'),
            (10,    'x'),
            (11,    'xi'),
            (14,    'xiv'),
            (39,    'xxxix'),
        ]:
            assert_that(counter.format(value), equal_to(string))


    def test_symbolic_counter(self):
        counter = SymbolicCounter('mock_css_id', 'abcde')
        for (value, string) in [
            (-1,    '-1'),  # Fallback
            (0,     '0'),   # Fallback
            (1,     'a'),
            (2,     'b'),
            (5,     'e'),
            (6,     'aa'),
            (10,    'ee'),
            (11,    'aaa'),
            (15,    'eee'),
        ]:
            assert_that(counter.format(value), equal_to(string))


    def test_cyclic_counter(self):
        counter = CyclicCounter('mock_css_id', 'abcde')
        for (value, string) in [
            # (-2,    'c'),
            (-1,    'd'),
            (0,     'e'),
            (1,     'a'),
            (2,     'b'),
            (5,     'e'),
            (6,     'a'),
            (10,    'e'),
            (11,    'a'),
            (15,    'e'),
        ]:
            assert_that(counter.format(value), equal_to(string))


    def test_fixed_counter(self):
        counter = FixedCounter('mock_css_id', 'abcde')
        for (value, string) in [
            (-1,    '-1'),  # Fallback
            (0,     '0'),   # Fallback
            (1,     'a'),
            (2,     'b'),
            (3,     'c'),
            (4,     'd'),
            (5,     'e'),
            (6,     '6'),   # Fallback
            (7,     '7'),   # Fallback
            (10,    '10'),  # Fallback
            (11,    '11'),  # Fallback
        ]:
            assert_that(counter.format(value), equal_to(string))


    def test_range_fallback(self):

        '''
        We construct different pairs of counter types, where the 'main' counter type has a certain
        range, and should fall back to the 'fallback' counter type outside that range. It _also_
        falls back for the special value '1'.
        '''

        for range_min, range_max, expected_seq in [
            (None, None, ['main0', 'main1', 'fbk2', 'main3', 'main4', 'main5']),
            (1,    None, ['fbk0',  'main1', 'fbk2', 'main3', 'main4', 'main5']),
            (None, 4,    ['main0', 'main1', 'fbk2', 'main3', 'main4', 'fbk5']),
            (1,    4,    ['fbk0',  'main1', 'fbk2', 'main3', 'main4', 'fbk5'])
        ]:
            class FallbackCounter(CounterType):
                def __init__(self):
                    super().__init__('fallback_mock_css_id',
                                     range = (None, None))

                def format_impl(self, count: int) -> str:
                    return f'fbk{count}'

            class MainCounter(CounterType):
                def __init__(self):
                    super().__init__('main_mock_css_id',
                                    range = (range_min, range_max),
                                    fallback = FallbackCounter())

                def format_impl(self, count: int) -> str:
                    return None if count == 2 else f'main{count}'

            counter_type = MainCounter()
            for count, expected_label in zip(range(0, 6), expected_seq):
                assert_that(counter_type.format(count),
                            equal_to(expected_label))


    def test_negative(self):

        for negative, abs_negative, expected_seq in [
            (('[', ']'), False, ['[x]', 'y', 'z']),
            (('[', ']'), True,  ['[z]', 'y', 'z'])
        ]:
            class TestCounter(CounterType):
                def __init__(self):
                    super().__init__('mock_css_id',
                                     range = (None, None),
                                     negative = negative,
                                     abs_negative = abs_negative)

                def format_impl(self, count: int) -> str:
                    return {-1: 'x', 0: 'y', 1: 'z'}[count]

            counter_type = TestCounter()
            for count, expected_label in zip(range(-1, 2), expected_seq):
                assert_that(counter_type.format(count),
                            equal_to(expected_label))


    def test_prefix_suffix(self):

        class TestCounter(CounterType):
            def __init__(self):
                super().__init__('mock_css_id',
                                 prefix = 'prefix-',
                                 suffix = '-suffix')

            def format_impl(self, count: int) -> str:
                return 'label'

        assert_that(
            TestCounter().format(1),
            equal_to('prefix-label-suffix'))


    def test_pad(self):

        for pad,       core_label, expected_label in [
            ((0, '#'), 'a',        'a'),
            ((0, '#'), 'aa',       'aa'),
            ((0, '#'), 'aaa',      'aaa'),
            ((1, '#'), 'a',        'a'),
            ((1, '#'), 'aa',       'aa'),
            ((1, '#'), 'aaa',      'aaa'),
            ((2, '#'), 'a',        '#a'),
            ((2, '#'), 'aa',       'aa'),
            ((2, '#'), 'aaa',      'aaa'),
            ((3, '#'), 'a',        '##a'),
            ((3, '#'), 'aa',       '#aa'),
            ((3, '#'), 'aaa',      'aaa'),
            ((4, '#'), 'a',        '###a'),
            ((4, '#'), 'aa',       '##aa'),
            ((4, '#'), 'aaa',      '#aaa')
        ]:
            class TestCounter(CounterType):
                def __init__(self):
                    super().__init__('mock_css_id',
                                     pad = pad)

                def format_impl(self, count: int) -> str:
                    return core_label

            assert_that(
                TestCounter().format(1),
                equal_to(expected_label))

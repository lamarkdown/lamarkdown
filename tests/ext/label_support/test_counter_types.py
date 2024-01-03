from lamarkdown.ext.label_support.counter_types import *
import unittest


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
                self.assertEqual(
                    string,
                    get_counter_type(name).format(value),
                    msg = f'counter "{name}" for value {value} expected to give "{string}"')


    def test_get_counter_type_i18n(self):
        for (name, all_symbols, other_samples) in [
            (
                'lower-greek',
                ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω'],
                [(25, 'αα'), (51, 'βγ')]
            )
        ]:
            counter = get_counter_type(name)
            for (value, string) in enumerate(all_symbols, start = 1):
                self.assertEqual(
                    string,
                    counter.format(value),
                    msg = f'counter "{name}" for value {value} expected to give "{string}"')

            for (value, string) in other_samples:
                self.assertEqual(
                    string,
                    counter.format(value),
                    msg = f'counter "{name}" for value {value} expected to give "{string}"')


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
            self.assertEqual(string, counter.format(value))


    def test_alphabetic_counter(self):
        counter = AlphabeticCounter('mock_css_id', 'abcde')
        for (value, string) in [
            (-1,    '-1'), # Fallback
            (0,     '0'),  # Fallback
            (1,     'a'),
            (2,     'b'),
            (5,     'e'),
            (6,     'aa'),
            (30,    'ee'),
            (31,    'aaa'),
        ]:
            self.assertEqual(string, counter.format(value))


    def test_additive_counter(self):
        counter = AdditiveCounter('mock_css_id',
                                  {10: 'x', 9: 'ix', 5: 'v', 4: 'iv', 1: 'i'})
        for (value, string) in [
            (-1,    '-1'), # Fallback
            (0,     '0'),  # Fallback
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
            self.assertEqual(string, counter.format(value))


    def test_symbolic_counter(self):
        counter = SymbolicCounter('mock_css_id', 'abcde')
        for (value, string) in [
            (-1,    '-1'), # Fallback
            (0,     '0'),  # Fallback
            (1,     'a'),
            (2,     'b'),
            (5,     'e'),
            (6,     'aa'),
            (10,    'ee'),
            (11,    'aaa'),
            (15,    'eee'),
        ]:
            self.assertEqual(string, counter.format(value))


    def test_cyclic_counter(self):
        counter = CyclicCounter('mock_css_id', 'abcde')
        for (value, string) in [
            (-1,    '-1'), # Fallback
            (0,     '0'),  # Fallback
            (1,     'a'),
            (2,     'b'),
            (5,     'e'),
            (6,     'a'),
            (10,    'e'),
            (11,    'a'),
            (15,    'e'),
        ]:
            self.assertEqual(string, counter.format(value))


    def test_fixed_counter(self):
        counter = FixedCounter('mock_css_id', 'abcde')
        for (value, string) in [
            (-1,    '-1'), # Fallback
            (0,     '0'),  # Fallback
            (1,     'a'),
            (2,     'b'),
            (3,     'c'),
            (4,     'd'),
            (5,     'e'),
            (6,     '6'), # Fallback
            (7,     '7'), # Fallback
            (10,    '10'), # Fallback
            (11,    '11'), # Fallback
        ]:
            self.assertEqual(string, counter.format(value))

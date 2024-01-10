from .counter_types import CounterType, CounterTypeFactory, ChineseCounter, EthiopicCounter
from .derived_counter_types import COUNTER_TYPES

ABBREVIATIONS = {
    '1': 'decimal',
    'a': 'lower-alpha',
    'A': 'upper-alpha',
    'i': 'lower-roman',
    'I': 'upper-roman',
}

SPECIAL_COUNTER_TYPES: CounterTypeFactory = CounterTypeFactory({
    'simp-chinese-informal': lambda: ChineseCounter(
        'simp-chinese-informal',
        digit_symbols = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'],
        power_symbols = ['', '十', '百', '千'],
        negative = ('负', ''),
        suffix = '、',
        fallback = COUNTER_TYPES['cjk-decimal']),

    'simp-chinese-formal': lambda: ChineseCounter(
        'sisimp-chinese-formal',
        digit_symbols = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'],
        power_symbols = ['', '拾', '佰', '仟'],
        negative = ('负', ''),
        suffix = '、',
        fallback = COUNTER_TYPES['cjk-decimal']),

    'trad-chinese-informal': lambda: ChineseCounter(
        'trad-chinese-informal',
        digit_symbols = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'],
        power_symbols = ['', '十', '百', '千'],
        negative = ('負', ''),
        suffix = '、'),

    'trad-chinese-formal': lambda: ChineseCounter(
        'trad-chinese-formal',
        digit_symbols = ['零', '壹', '貳', '參', '肆', '伍', '陸', '柒', '捌', '玖'],
        power_symbols = ['', '拾', '佰', '仟'],
        negative = ('負', ''),
        suffix = '、',
        fallback = COUNTER_TYPES['cjk-decimal']),

    'cjk-ideographic': lambda: SPECIAL_COUNTER_TYPES['trad-chinese-informal'],

    'ethiopic-numeric': lambda: EthiopicCounter(
        'ethiopic-numeric',
        minor_symbols = ['፩', '፪', '፫', '፬', '፭', '፮', '፯', '፰', '፱'],
        major_symbols = ['፲', '፳', '፴', '፵', '፶', '፷', '፸', '፹', '፺'],
        odd_symbol = '፻',
        even_symbol = '፼'),
})


def get_counter_type(name: str) -> CounterType:
    name = ABBREVIATIONS.get(name, name)
    return SPECIAL_COUNTER_TYPES[name] or COUNTER_TYPES[name]

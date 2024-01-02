from . import counter_types
from dataclasses import dataclass
import re
from typing import Optional


@dataclass
class LabelTemplate:
    prefix: str
    separator: str
    suffix: str
    parent_type: str
    # heading_parent: bool
    # list_parent: bool
    counter_type: Optional[counter_types.CounterType]
    child_template: Optional['LabelTemplate']


class LabelTemplateException(Exception): pass


QUOTED_LITERAL = r'''
    ' ( [^'] | '' )*+ '
    |
    " ( [^"] | "" )*+ "
'''

LITERAL = fr'''
    (
        [^a-zA-Z0-9,] | {QUOTED_LITERAL}
    )*+
'''

TEMPLATE_REGEX = re.compile(fr'''(?x)
    \s*
    (?P<prefix> {LITERAL} )
    (
        (
            (?P<parent> X | L | H[1-6]? )
            (?P<separator> {LITERAL} )
        )?+
        (?P<format> [a-zA-Z0-9-]+ )
        (?P<suffix> {LITERAL} )
    )?
    \s*
''')

# STATIC_LABELS = {'disc': '•', 'circle': '◦', 'square': '▪'}


QUOTED_LITERAL_REGEX = re.compile(QUOTED_LITERAL)
ESCAPED_QUOTES = {'"': re.compile('""'),
                  "'": re.compile("''")}

def _repl_literal(match) -> str:
    # quote = match.group('quote')
    quote = match.group()[0]
    text  = match.group()[1:-1]
    return ESCAPED_QUOTES[quote].sub(quote, text)


class LabelTemplateParser:

    # DEFAULT = LabelTemplate(prefix = '', separator = '', suffix = '.',
    #                         heading_parent = False, list_parent = False,
    #                         counter_type = counter_types.get_counter_type('decimal'))
    DEFAULT = LabelTemplate(prefix = '', separator = '', suffix = '.', parent_type = '',
                            counter_type = counter_types.get_counter_type('decimal'),
                            child_template = None)

    def __init__(self):
        self._cache = {}




    def parse(self, template_str: str, start_index: int = 0) -> Optional[LabelTemplate]:
        if template_str is None:
            raise ValueError

        template_substr = template_str[start_index:];
        template = self._cache.get(template_substr)
        if template is not None:
            return template

        match = TEMPLATE_REGEX.match(template_substr)
        if match is None:
            raise LabelTemplateException(f'Parse error in label template "{template_str}"')


        # prefix = QUOTED_LITERAL_REGEX.sub(_repl_literal, match.group('prefix'))
        # parent_spec = match.group('parent')
        #
        # counter_type = None
        # if (counter_name := match.group('format')) is not None:
        #     if counter_name in STATIC_LABELS:
        #         prefix = f'prefix{STATIC_LABELS[counter_name]}'
        #
        #     else:
        #         counter_type = counter_types.get_counter_type(counter_name)
        #         if counter_type is None:
        #             raise LabelTemplateException(
        #                 f'Invalid counter type "{counter_name}" in label template "{template_str}"')
        #
        # template = LabelTemplate(
        #     prefix         = prefix,
        #     separator      = QUOTED_LITERAL_REGEX.sub(_repl_literal, match.group('separator') or ''),
        #     suffix         = QUOTED_LITERAL_REGEX.sub(_repl_literal, match.group('suffix') or ''),
        #     parent_type    = '' if parent_spec == 'X' else parent_spec,
        #     # heading_parent = parent in ['P', 'H'],
        #     # list_parent    = parent in ['P', 'L'],
        #     counter_type   = counter_type,
        #     child_template = None
        # )


        parent_type = None
        if (parent_spec := match.group('parent')) is not None:
            parent_type = '' if parent_spec == 'X' else parent_spec.lower()

        counter_type = None
        if (counter_name := match.group('format')) is not None:
            counter_type = counter_types.get_counter_type(counter_name)
            if counter_type is None:
                raise LabelTemplateException(
                    f'Invalid counter type "{counter_name}" in label template "{template_str}"')

        template = LabelTemplate(
            prefix         = QUOTED_LITERAL_REGEX.sub(_repl_literal, match.group('prefix')),
            separator      = QUOTED_LITERAL_REGEX.sub(_repl_literal, match.group('separator') or ''),
            suffix         = QUOTED_LITERAL_REGEX.sub(_repl_literal, match.group('suffix') or ''),
            parent_type    = parent_type,
            # heading_parent = parent in ['P', 'H'],
            # list_parent    = parent in ['P', 'L'],
            counter_type   = counter_type,
            child_template = None
        )

        match_len = match.end()
        if match_len < len(template_substr):
            if template_str[match_len] != ',':
                raise LabelTemplateException(f'Expected "," at index {match_len}')

            template.child_template = (
                template if template_substr[match_len + 1].strip() == '*'
                else self.parse(template_str, start_index + match_len + 1)
            )

        self._cache[template_substr] = template
        return template


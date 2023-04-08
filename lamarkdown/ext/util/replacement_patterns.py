'''
Replacement patterns are a mechanism we add to Python Markdown, similar to inline patterns, but
parsed differently (and parsed before inline patterns).

Inline patterns are applied one at a time, in order of priority, to the whole a given piece of text.
Replacement patterns are applied one at a time, in order of priority, to _each character position_
of a given piece of text. Thus, patterns that appear _first_ take precedence over patterns appearing
later.

This help us create new 'replacement' elements, where the original text between start and end
delimiters is converted and replaced by something else. More precisely, whether or not we actually
replace the text, we want to _suppress_ further processing between the start and end delimiters.

The $`...` syntax from la.eval, and $...$ and $$...$$ from la.latex work like this. Inline patterns
cannot easily resolve the case where one syntax appears inside the other, as in '$`...$...$...`'
and '$$...$`...`...$$'. What we want is for the _outermost_ syntax to take precedence, and for the
inner syntax to be treated as literal text.

We cannot achieve this if we parse one syntax strictly before the other, using inline patterns.

The `...` markdown syntax falls conceptually into this category too. It is handled using an inline
processor, and that works only because it's the only syntax of its kind, by default. To avoid
clashes between this inline processor and any replacement processors, we register a
`BacktickPassthrough` replacement processor, which recognises `...`, ``...``, etc., and so prevents
other replacement processors replacing anything inside them, but which then permits inline patterns
-- i.e., the backtick inline processor -- to handle the content.
'''

from . import opaque_tree
import markdown
from markdown.treeprocessors import Treeprocessor

import re
from xml.etree import ElementTree


class ReplacementPattern:
    def __init__(self, regex, allow_inline_patterns = False):
        self.compiled_re = re.compile(regex)
        self.allow_inline_patterns = allow_inline_patterns

    def handle_match(self, match):
        raise NotImplementedError


class BacktickPassthrough(ReplacementPattern):
    def __init__(self):
        super().__init__(
            '(?P<tic>`+)(?P<code>.+?)(?P=tic)',
            allow_inline_patterns = True)

    def handle_match(self, match):
        return match.group(0)



class ReplacementProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md):
        super().__init__(md)


    def run(self, root):
        all_patterns = list(self.md.replacement_patterns)
        self._process_element(root, all_patterns)


    def _process_element(self, element, all_patterns):
        i = self._process_text(element, all_patterns)
        while i < len(element):
            self._process_element(element[i], all_patterns)
            i = self._process_tail(element, i, all_patterns)


    def _process_text(self, element, all_patterns):
        ch_index = 0
        while element.text:
            new_element, match = self._find_first_pattern(element.text, ch_index, all_patterns)
            if new_element is None: break

            ch_index = match.end(0)
            prefix = element.text[:match.start(0)]
            suffix = element.text[ch_index:]

            if isinstance(new_element, str):
                element.text = f'{prefix}{new_element}{suffix}'

            else: # isinstance(new_element, Element):
                element.insert(0, new_element)
                element.text = prefix or None
                new_element.tail = suffix or None
                return self._process_tail(element, 0, all_patterns)

        return 0


    def _process_tail(self, element, elem_index, all_patterns):
        ch_index = 0
        prev_subelement = element[elem_index]
        while prev_subelement.tail:
            new_element, match = self._find_first_pattern(prev_subelement.tail, ch_index, all_patterns)
            if new_element is None: break

            ch_index = match.end(0)
            prefix = prev_subelement.tail[:match.start(0)]
            suffix = prev_subelement.tail[match.end(0):]

            if isinstance(new_element, str):
                prev_subelement.tail = f'{prefix}{new_element}{suffix}'

            else: # isinstance(new_element, Element):
                elem_index += 1
                element.insert(elem_index, new_element)

                prev_subelement.tail = prefix or None
                new_element.tail = suffix or None
                prev_subelement = new_element
                ch_index = 0

        return elem_index + 1


    def _find_first_pattern(self, text, start_index, all_patterns):
        if isinstance(text, markdown.util.AtomicString):
            return None, None

        escaped = False
        for ch_index in range(start_index, len(text) - start_index):
            if text[ch_index] == '\\':
                escaped = not escaped
            else:
                if not escaped:
                    for pattern in all_patterns:
                        match = pattern.compiled_re.match(text, ch_index)
                        if match:
                            new_element = pattern.handle_match(match)
                            if isinstance(new_element, ElementTree.Element) and not pattern.allow_inline_patterns:
                                opaque_tree(new_element)
                            return new_element, match
                escaped = False

        return None, None


def init(md):
    if not hasattr(md, 'replacement_patterns'):
        md.replacement_patterns = markdown.util.Registry()
        md.replacement_patterns.register(BacktickPassthrough(), 'backtick-passthrough', 10)

        md.treeprocessors.register(ReplacementProcessor(md), 'replacement', 30)

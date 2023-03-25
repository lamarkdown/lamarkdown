'''
'''


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


# class BacktickPassthrough(ReplacementPattern):
#     def __init__(self):
#         super().__init__(
#             '(?P<tic>`+)(?P<code>.+?)(?P=1)',
#             allow_inline_patterns = True)
#
#     def handle_match(self, match):




class ReplacementProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md):
        super().__init__(md)


    def run(self, root):
        all_patterns = list(self.md.replacement_patterns)
        self._process_element(root, all_patterns)


    def _process_element(self, element, all_patterns):
        i = 0
        prev_element = None

        if element.text:
            new_element, match = self._find_first_pattern(element.text, all_patterns)
            if new_element is not None:
                element.insert(0, new_element)
                prefix = element.text[:match.start(0)]
                suffix = element.text[match.end(0):]
                element.text = prefix or None
                new_element.tail = suffix or None
                i = self._process_tail(element, 0, all_patterns)

        while i < len(element):
            self._process_element(element[i], all_patterns)
            i = self._process_tail(element, i, all_patterns)


    def _process_tail(self, element, index, all_patterns):
        prev_subelement = element[index]
        while prev_subelement.tail:
            new_element, match = self._find_first_pattern(prev_subelement.tail, all_patterns)
            if new_element is None: break

            index += 1
            element.insert(index, new_element)

            prefix = prev_subelement.tail[:match.start(0)]
            suffix = prev_subelement.tail[match.end(0):]
            prev_subelement.tail = prefix or None
            new_element.tail = suffix or None
            prev_subelement = new_element

        return index + 1


    def _find_first_pattern(self, text, all_patterns):
        if isinstance(text, markdown.util.AtomicString):
            return None, None

        escaped = False
        for ch_index in range(len(text)):
            if text[ch_index] == '\\':
                escaped = not escaped

            elif not escaped:
                for pattern in all_patterns:
                    match = pattern.compiled_re.match(text, ch_index)
                    if match:
                        new_element = pattern.handle_match(match)
                        if not pattern.allow_inline_patterns:
                            self._opaque_tree(new_element)
                        return new_element, match

        return None, None


    def _opaque_tree(self, element):
        element.text = markdown.util.AtomicString(element.text)
        for subelement in element:
            self._opaque_tree(subelement)
            subelement.tail = markdown.util.AtomicString(subelement.tail)





def init(md):
    if not hasattr(md, 'replacement_patterns'):
        md.replacement_patterns = markdown.util.Registry()
        md.treeprocessors.register(ReplacementProcessor(md), 'replacement', 30)

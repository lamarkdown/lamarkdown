from __future__ import annotations
from .labellers import Labeller
from .label_templates import parse_element_type

from collections import defaultdict
import re
from typing import Callable, Iterator
from xml.etree.ElementTree import Element


LABEL_REF_CLASS = 'la-ref'
LINK_REF_REGEX = re.compile(r'(?<!\\)##((?P<brace>\{)?(?P<type>[a-zA-Z0-9_-]+)(?(brace)\}|))?')


class RefResolver:
    def __init__(self):
        pass

    def find_refs(self, root: Element):
        self._refs: dict[str, dict[str, list[Element]]] = defaultdict(lambda: defaultdict(list))

        for anchor in root.iter('a'):
            href = anchor.get('href') or ''
            if href.startswith('#') and len(href) > 1:
                id = href[1:]
                for element_type, ref_element in self._find(anchor):
                    self._refs[id][element_type].append(ref_element)


    def _find(self, element: Element) -> Iterator[tuple[str, Element]]:
        text = element.text or ''
        if match := LINK_REF_REGEX.search(text):
            ref_element = Element('span')
            ref_element.set('class', LABEL_REF_CLASS)
            ref_element.text = match.group()  # Will be overwritten later
            ref_element.tail = text[match.end():]
            yield (parse_element_type(match.group('type') or 'x'), ref_element)

            element.text = text[0:match.start()]
            element.insert(0, ref_element)

        i = 0
        while i < len(element):
            # Not a for loop because we're modifying the list as we go.
            child = element[i]
            if child.get('class') != LABEL_REF_CLASS:
                yield from self._find(child)

            i += 1
            text = child.tail or ''
            if match := LINK_REF_REGEX.search(text):

                ref_element = Element('span')
                ref_element.set('class', LABEL_REF_CLASS)
                ref_element.text = match.group()  # Will be overwritten later
                ref_element.tail = text[match.end():]
                yield (parse_element_type(match.group('type') or 'x'), ref_element)

                child.tail = text[0:match.start()]
                element.insert(i, ref_element)


    def resolve_refs(self,
                     target_element: Element,
                     find_labeller: Callable[[str], Labeller | None]):

        if (id := target_element.get('id')) and (id_label_refs := self._refs.get(id)):
            for element_type, ref_elements in id_label_refs.items():
                if labeller := find_labeller(element_type):
                    label = labeller.as_string_core()
                    for ref_element in ref_elements:
                        ref_element.text = label

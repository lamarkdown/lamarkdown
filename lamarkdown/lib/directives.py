from __future__ import annotations
from .progress import Progress
import markdown
from xml.etree.ElementTree import Element


class Directives:
    def __init__(self, progress: Progress):
        self._progress = progress


    def format(self, name: str, value: str | None = None) -> str:
        if value is None:
            return f'-{name}'
        else:
            value = value.replace('\\', '\\\\').replace('"', '\\"')
            return f'-{name}="{value}"'


    def _pop(self, name: str, element: Element, context: str) -> tuple[str | None, str | None]:

        a1 = f'-{name}'
        a2 = f'md-{name}'
        v1 = element.attrib.pop(a1, None)
        v2 = element.attrib.pop(a2, None)

        if v1 is not None and v2 is not None:
            self._progress.warning(
                context,
                msg = (f'Avoid writing both "{a1}" and "{a2}" for the same element.'))

        if v1 is not None:
            return a1, v1

        if v2 is not None:
            return a2, v2

        return None, None


    def pop(self,
            name: str,
            element: Element,
            context: str,
            default: str | None = None) -> str | None:

        _, value = self._pop(name, element, context)
        return value or default


    def pop_bool(self, name: str, element: Element, context: str) -> bool:
        attr, value = self._pop(name, element, context)
        if value is not None and value not in [f'-{name}', f'md-{name}']:
            self._progress.warning(
                context,
                msg = (f'Do not write {{{attr}="{value}"}}; {attr} expects no value.'))

        return value is not None


    def peek(self, name: str, element: Element, context: str) -> bool:
        return f'-{name}' in element.attrib or f'md-{name}' in element.attrib


class DirectiveTreeProcessor(markdown.treeprocessors.Treeprocessor):
    '''
    Translates directive attributes from their condensed form ('-directive') to a form compatible
    with HTML/XML parsing ('md-directive'). This ensures we can continue to
    '''

    def __init__(self, md):
        super().__init__(md)

    def run(self, root):
        for element in root.iter():
            dir_attributes = [a for a in element.attrib.keys() if a.startswith('-')]
            for attr in dir_attributes:
                new_attr = f'md{attr}'
                if new_attr not in element.attrib:
                    element.attrib[new_attr] = element.attrib[attr]
                    del element.attrib[attr]


def init(md):
    NAME = 'la-directives'
    if NAME not in md.treeprocessors:
        md.treeprocessors.register(DirectiveTreeProcessor(md), NAME, 0)

        # This can generally be very low priority; it simply needs to happen _at some point_ after
        # attr_list is done, and while the tree structure still exists.

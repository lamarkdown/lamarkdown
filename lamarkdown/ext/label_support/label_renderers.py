from .labellers import Labeller
from abc import ABC, abstractmethod
from textwrap import dedent
from typing import Callable, Dict, Optional, Set
from xml.etree import ElementTree


LABELLED_CSS_CLASS = 'la-labelled'
EXPLICIT_LABEL_CSS_CLASS = 'la-label'
NO_LABEL_CSS_CLASS = 'la-no-label'


def add_css_class(element: ElementTree.Element, *new_classes: str):
    if classes_str := element.get('class'):
        existing_classes = set(classes_str.split())
        element.set('class', classes_str + ' ' + (' '.join(c for c in new_classes
                                                           if c not in existing_classes)))
    else:
        element.set('class', ' '.join(new_classes))


def add_element_style(element: ElementTree.Element, new_style: str):
    if (existing_style := element.get('style')) is not None:
        new_style = f'{existing_style};{new_style}'
    element.set('style', new_style)


class LabelsRenderer(ABC):

    @abstractmethod
    def render_labelled_element(self,
                                labeller: Labeller,
                                container: Optional[ElementTree.Element],
                                element: ElementTree.Element):
        ...

    def render_no_labelled_element(self,
                                   container: Optional[ElementTree.Element],
                                   element: ElementTree.Element):

        if container is not None:
            add_css_class(element, NO_LABEL_CSS_CLASS)


class CssLabelsRenderer(LabelsRenderer):
    def __init__(self, css_fn: Callable[[str], None]):
        self._css_fn = css_fn
        self._css_done: Set[str] = set()
        self._labellers: Dict[ElementTree.Element, Labeller] = {}
        self._labellers_changed: Set[ElementTree.Element] = set()


    def _css(self, css):
        if css in self._css_done:
            return
        self._css_done.add(css)
        self._css_fn(dedent(css))


    def render_labelled_element(self,
                                labeller: Labeller,
                                container: Optional[ElementTree.Element],
                                element: ElementTree.Element):

        self._css(f'.{LABELLED_CSS_CLASS}>li{{list-style-type:none;}}\n')

        css_class = labeller.get_css_class()

        if container is None:
            raise NotImplementedError
            # TODO: this would implement CSS-based counters for headings (standalone elements).
            # We don't need this quite yet, but it's a future possibility.

        else:
            prev_labeller = self._labellers.get(container)
            new = prev_labeller != labeller
            if new:
                self._labellers[container] = labeller

            first = prev_labeller is None
            if first:
                add_css_class(container, f'{LABELLED_CSS_CLASS} {css_class}')
                if labeller.template.counter_type is not None:
                    self._css(f'.{css_class}{{counter-reset:{css_class};}}\n')
                    self._css(f'.{css_class}>li:not(.{NO_LABEL_CSS_CLASS}){{'
                              f'counter-increment:{css_class};}}\n')

                self._css(f'.{css_class}>li:not(.{NO_LABEL_CSS_CLASS})::before{{'
                          f'content:{labeller.as_css_expr()};}}')

            if new and not first:
                if labeller.template.counter_type is not None:
                    self._css(f'{element.tag}.{css_class}{{counter-increment:{css_class};}}\n')

                self._css(f'{element.tag}.{css_class}::before{{'
                          f'content:{labeller.as_css_expr()};}}\n')
                add_element_style(element, f'counter-reset:{css_class}')
                self._labellers_changed.add(container)

            if container in self._labellers_changed:
                add_css_class(element, css_class)


class HtmlLabelsRenderer(LabelsRenderer):

    def __init__(self):
        self._containers: Set[ElementTree.Element] = set()

    def render_labelled_element(self,
                                labeller: Labeller,
                                container: Optional[ElementTree.Element],
                                element: ElementTree.Element):

        if container is not None and container not in self._containers:
            self._containers.add(container)
            add_css_class(container, LABELLED_CSS_CLASS)

        label_elem = ElementTree.Element('span', {'class': EXPLICIT_LABEL_CSS_CLASS})
        label_elem.text = labeller.as_string()
        label_elem.tail = element.text
        element.text = ''
        element.insert(0, label_elem)

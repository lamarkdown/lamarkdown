from .label_templates import LabelTemplate
from typing import List, Optional


class Labeller:
    '''
    Tracks and produces text/css representation of labels (particularly counter-based labels,
    though fixed labels too) for headings, lists and potentially other elements.
    '''
    def __init__(self,
                 element_type: str,
                 template: LabelTemplate,
                 parent: Optional['Labeller'] = None,
                 count: int = 0,
                 css_id: Optional[int] = None):

        self._element_type = element_type.lower()
        self._template = template
        self._parent = parent
        self._count = count
        self._css_id = css_id
        self._dependents: List[Labeller] = []


    def add_dependent(self, dependent: 'Labeller'):
        assert dependent is not self
        self._dependents.append(dependent)


    def reset_dependents(self):
        self._dependents.clear()


    def as_string_core(self):
        if self._template.counter_type is None:
            return ''

        s = self._template.counter_type.format(self._count)
        if self._parent is None:
            return s

        return f'{self._parent.as_string_core()}{self._template.separator}{s}'


    def as_css_expr_core(self):
        if self._template.counter_type is None:
            return ''

        if self._css_id is None:
            return _as_css_str(self.as_string_core())

        expr = f'counter({self.get_css_class()},{self._template.counter_type.css_id})'
        if self._parent is not None:
            sep = _as_css_str(self._template.separator)
            expr = f'{self._parent.as_css_expr_core()} {sep} {expr}'.strip()
        return expr


    def as_string(self):
        return f'{self._template.prefix}{self.as_string_core()}{self._template.suffix}'


    def as_css_expr(self):
        prefix = _as_css_str(self._template.prefix)
        suffix = _as_css_str(self._template.suffix)
        return f'{prefix} {self.as_css_expr_core()} {suffix}'.strip()


    def get_css_class(self):
        '''
        Name to be used to _both_:
        (a) identify a container for CSS styling purposes, and
        (b) identify the CSS counter to keep track of the numbering.
        '''
        return None if self._css_id is None else f'la-label{self._css_id}'

    @property
    def element_type(self):
        return self._element_type

    @property
    def template(self):
        return self._template

    @property
    def parent(self):
        return self._parent

    @property
    def dependents(self):
        return self._dependents

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, n):
        self._count = n

    def __repr__(self):
        return f'Labeller({self._element_type}, {self._template}, {self._count}, {self._css_id})'


def _as_css_str(string):
    return ('"' + string.replace('\\', '\\\\').replace('"', '\\"') + '"') if string else ''

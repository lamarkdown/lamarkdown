from .label_templates import LabelTemplate, LabelTemplateParser
from typing import List, Optional, Union


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
        self._children: List[Labeller] = []


    def add_child(self, child: 'Labeller'):
        self._children.append(child)


    def reset_children(self):
        self._children.clear()


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
    def children(self):
        return self._children

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


# class LabellerFactory:
#     def __init__(self, parser = LabelTemplateParser()):
#         self._parser = parser
#         self._next_id = 0
#         self._labellers = {}
#
#     def get(self,
#             element_type: str,
#             template: Union[str, LabelTemplate],
#             parent: Optional[Labeller] = None,
#             count: int = 0,
#             css: bool = True):
#
#         _template = self._parser.parse(template) if isinstance(template, str) else template
#
#         key_list = [_template.counter_type, css, _template.prefix, _template.suffix]
#         cur_parent = parent
#         while cur_parent is not None:
#             key_list.append(cur_parent._template.counter_type)
#             key_list.append(_template.separator)
#             cur_parent = cur_parent.parent
#
#         key = tuple(key_list)
#
#         labeller = self._labellers.get(key)
#         if labeller is None:
#             if css is False:
#                 css_id = None
#             else:
#                 css_id = self._next_id
#                 self._next_id += 1
#                 self._labellers[key] = labeller
#
#             labeller = Labeller(element_type, _template, parent, count, css_id)
#             self._labellers[key] = labeller
#
#         labeller.count = count
#
#         if parent is not None:
#             parent.add_child(labeller)
#
#         return labeller


# class LabellerStack:
#     def __init__(self):
#         self._stack: List[Labeller] = []
#
#     def append(self, labeller: Labeller):
#         self._stack.append(labeller)
#
#     def clear_children(self, labeller: Labeller):
#         for child_labeller in labeller.children:
#             try:
#                 stack.remove(child_labeller)
#             except ValueError:
#                 pass  # Doesn't matter if not in stack
#         labeller.children.clear()
#
#     def remove(self, labeller: Labeller):
#         self.clear_children(labeller)
#         try:
#             self._stack.remove(labeller)
#         except ValueError:
#             pass
#
#     def replace(self, old_labeller: Labeller, new_labeller: Labeller):
#         self.clear_children(old_labeller)
#         self._stack[self._stack.index(old_labeller)] = new_labeller
#
#     def find(self, element_type: str) -> Optional[Labeller]:
#         if element_type is None:
#             return None
#         for labeller in reversed(self._labeller_stack):
#             if labeller.element_type.startswith(element_type):
#                 return labeller
#         return None

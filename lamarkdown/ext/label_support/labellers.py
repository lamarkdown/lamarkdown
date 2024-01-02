from .label_templates import LabelTemplate
from typing import Optional


class Labeller:
    # TODO: ListCounter needs to have a unique ID, because it needs to create CSS counters and refer back to them.
    # Also, if we get it to create an entire set of CSS rules (not just a content expression), then it needs IDs
    # to match those rules to elements.

    # Ideally I want to reuse CSS where possible, rather than duplicating it. Which means:
    # 1. I need a dict somewhere to store CSS class names (as these are the only(?) things required to be embedded in the HTML.
    # 2. The dict keys should be... templates, plus some representation of the parent template? i.e., lists containing all ancestor templates plus the current one. (Not necessary to include child templates.)

    def __init__(self, element_type: str,
                       template: LabelTemplate,
                       parent: Optional['Labeller'] = None,
                       count: int = 0,
                       css_id: Optional[int] = None):

        self._element_type = element_type.lower()
        self._template = template
        self._parent = parent
        self._count = count
        self._css_id = css_id


    def _as_string_core(self):
        s = self._template.counter_type.format(self._count)
        return (
            s if self._parent is None
            else f'{self._parent._as_string_core()}{self._template.separator}{s}'
        )


    def _as_css_expr_core(self):
        if self._css_id is None:
            return _as_css_str(self._as_string_core())

        elif self._template.counter_type is None:
            return ''

        else:
            expr = f'counter({self.get_css_counter()}, {self._template.counter_type.css_id})'
            if self._parent is not None:
                expr = f'{self._parent._as_css_expr_core()} {self._template.separator} {expr}'
            return expr


    def as_string(self):
        return f'{self._template.prefix}{self._as_string_core()}{self._template.suffix}'


    def as_css_expr(self):
        prefix = _as_css_str(self._template.prefix)
        suffix = _as_css_str(self._template.suffix)
        return f'{prefix} {self._as_css_expr_core()} {suffix}'


    def get_css_counter(self):
        return self._css_id and f'la-label{self._css_id}'

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
    def count(self):
        return self._count

    @count.setter
    def count(self, n):
        # self._str = None
        # self._internal_str = None
        self._count = n


def _as_css_str(string):
    return ('"' + string.replace('\\', '\\\\').replace('"', '\\"') + '"') if string else ''


class LabellerFactory:
    def __init__(self):
        self._next_id = 0
        self._labellers = {}

    def get(self,
            element_type: str,
            template: LabelTemplate,
            parent: Labeller = None,
            count: int = 0,
            css: bool = True):

        key_list = [template.counter_type, template.prefix, template.suffix]
        cur_parent = parent
        while cur_parent is not None:
            key_list.append(cur_parent.template.counter_type)
            key_list.append(template.separator)
            cur_parent = cur_parent.parent

        key = tuple(key_list)

        labeller = self._labellers.get(key)
        if labeller is None:
            if css is None:
                css_id = None
            else:
                css_id = self._next_id
                self._next_id += 1
                self._labellers[key] = labeller

            labeller = Labeller(element_type, template, parent, count, css_id)
            self._labellers[key] = labeller

        labeller.count = count
        return labeller


# class ListCounter:
#     def __init__(self, #type: str,
#                        template: LabelTemplate,
#                        str_impl_only: bool = False,
#                        parent: ListCounter = None,
#                        count: int = 1):
#         #self._type = type
#         self._template = template
#         self._str_impl_only = str_impl_only
#         self._parent = parent
#         self._count = count
#
#         self._str = None
#         self._expr = None
#         self._internal_str = None
#         self._internal_expr = None
#
#         # We should pre-evaluate the whole 'parent' boolean expression somehow, both so that it
#         # doesn't get duplicated below, and for slight efficiency.
#         #
#         # Basically, 'parent' can just be None if the expression would be false.
#
#
#     def _as_internal_str(self):
#         if not self._internal_str:
#             # self._internal_str = (
#             #     parent._as_internal_str()
#             #     if parent and ((parent._type == 'h' and template.heading_parent) or
#             #                    (parent._type in ['ol', 'ul'] and template.list_parent))
#             #     else ''
#             #     +
#             #     ...
#             # )
#             self._internal_str = (
#                 self._parent._as_internal_str() if self.p_parent else ''
#                 +
#                 self._template.counter_type.format(self._count)
#             )
#         return self._internal_str
#
#
#     def _as_internal_expr(self):
#         if self._str_impl_only:
#             return self._as_internal_str()
#
#         if not self._internal_expr:
#             if self._str_impl_only:
#                 self._internal_expr = _as_css_str(self._as_internal_str())
#             else:
#                 # # TODO: not sure where to get the counter ID from yet
#                 # self._internal_expr = f'counter({counter_id...}, {self._template.format})'
#                 #
#                 # if self._parent and (
#                 #     (self._parent._type == 'h' and self._template.heading_parent) or
#                 #     (self._parent._type in ['ol', 'ul'] and self._template.list_parent)):
#                 #
#                 #     self._internal_expr = f'{self.parent._as_internal_expr} {_as_css_str(self._template.separator)} {self._internal_expr}'
#
#                 # TODO: not sure where to get the counter ID from yet
#                 self._internal_expr = f'counter({counter_id...}, {self._template.counter_type.css_id})'
#
#                 if self._parent:
#                     self._internal_expr = f'{self._parent._as_internal_expr()} {_as_css_str(self._template.separator)} {self._internal_expr}'
#
#         return self._internal_expr
#
#     def as_str(self):
#         if not self._str:
#             self._str = f'{template.prefix}{self._as_internal_str()}{template.suffix}'
#         return self._str
#
#     def as_expr(self):
#         if not self._expr:
#
#     @property
#     def count(self):
#         return self._count
#
#     @count.setter
#     def count(self, n):
#         self._str = None
#         self._internal_str = None
#         self._count = n

'''
# List Label Extension

Assigns counter-based (or fixed) labels to headings and/or list items, either by embedding label
text directly in the HTML (for headings), or by employing CSS properties to render labels,
particularly for <ol> and <ul>.

'Label templates' specify what labelling system to use. They can be provided in two ways:

1. By adding the ':label' directive; e.g.:

    ## The Next Section {::label="[1] "}

    {::label="(a) "}
    1. Item A
    2. Item B
    3. Item C

2. By specifying the configuration options 'h_labels', 'ol_labels' and 'ul_labels', which then
   apply to the top-most heading, <ol> or <ul> elements, respectively. (By specifying 'h_level',
   the 'h_labels' template can instead apply to a specific heading level from 1 to 6.)


## Template syntax

Label templates can create complex labelling schemes, with minimal specification. The syntax is
defined as follows:

template := template_part ( ',' template_part )* [ ',' '*' ]
template_part := literal* [ [ ('X' | 'L' | 'H' [level] ) literal+ ] format_spec literal* ]

format_spec := any alphanumeric sequence (including '-', but not at the start or end position)

level := an integer from 1 to 6, inclusive
literal := ( unquoted_literal | quoted_literal )*
unquoted_literal := any single character _other than_ ',', quotation marks, alphanumeric
    characters, or '-' if surrounded by alphanumeric characters
quoted_literal := any sequence of characters surrounded by double or single quotes, and possibly
    including doubled-up quotes to represent literal quotation marks.

Thus, a template consists of one or more comma-separated parts, optionally ending in a '*'. The
first (mandatory) part applies directly to the current list or list element. Subsequent parts apply
to successive levels of child lists, _of the same fundamental type_ (nested lists for lists, and
sub-headings for headings). If present, the '*' causes the final template to apply indefinitely to
any more deeply-nested lists/headings. (If '*' is omitted, then any lists nested more deeply are
outside the scope of this template list.)

The `format_spec` refers to the core numbering system for a given list or list element. It can be:

* `1`, for arabic numerals;
* `a`/`A`, for lower/uppercase English alphabetic numbering;
* `i`/`I`, for lower/uppercase Roman numerals; or
* one of various terms accepted by the list-style-type CSS property; e.g., `lower-greek`,
    `armenian`, etc.

(This extension seeks to support _most_ numbering schemes available in CSS.)

For <ul> elements, there's generally no numbering system required, and `format_spec` can be
omitted, so that the entire template consists just of a literal `prefix`.

(This extension _does not_ directly support the CSS terms 'disc', 'circle', 'square', as these can
be directly represented with literal characters; e.g., '•', '◦', '▪'.)

If `X`, `L` or `H` is given, it refers to the label of the nearest _numbered_ ancestor element.
Specifically, `X` means _any_ such element (though, again, only those with numbering systems, so
generally not <ul> elements), `L` means a list element (almost certainly <ol>), `H` means any
heading element, and `H1`-`H6` mean the corresponding heading level. If such an ancestor element
exists, its core label (minus any prefix/suffix literals) will be inserted prior to the element's
own number, along with an delimiting literal.

If X, L or H is given, but no such element exists, then no ancestor label will be inserted, _and_
the delimiting literal will be omitted too.

Examples:

* :label="(X.1),*"
* :label="1.,(a),(i)"


# Also...

:no-label -- suppresses any label for the current element, and avoids updating the counter.

'''


# TODO :
# - number <table><caption>... and <figure><figcaption>...
# - <figure> could be used to represent several different kinds of numbered constructs: images, equations, code listings, maybe even tables (though <table><caption> already exists for that).
#
# - For each <figure> or <table>, we first figure out what sub-type it is:
#   - initially, check whether there's a CSS class equal to any of several keywords, case-insensitive. By default, these are 'figure', 'table', 'equation' and 'listing' (irrespective of whether <figure> or <table> has been used).
#   - if not, check whether there's a CSS class _containing_ any of those keywords, or any abbreviations ('fig', 'tab', 'eq' or 'lst')
#   - if not, then:
#     - a <table> is just a table
#     - for a <figure>, guess from the contents; by default:
#       - <code>/<pre> -> listing;
#       - <math> -> equation;
#       - <table> -> table;
#       - anything else -> figure.
#   - Each of these shall be called a 'figure/table type', and has its own independent label series.
#
# - The user shall be able to define additional types, via la.labels configuration option; e.g., (for equations)
#   - figure_types: [{'names': ['example', 'ex'],
#                       'auto_detect': ['./div[@class="example"]'],
#                       'default_labels': 'Example H2.1. '}]
#   - The names become valid class names, as well as valid element types. They must not overlap.
#
# - Consolidate the config option for specifying global labelling, into a single dict, indexed by element type
#
# - Create another (simple) markdown extension called 'figures' (or maybe 'captions') that will
#   find any elements with the ':caption' directive and wrap them in a <figure>, with the value of
#   ':caption' becoming the content (passed through markdown's inline (tree?) processors) of <figcaption>.



# TODO:
#
# <f
#
#
# :label-resume -- continue the numbering from the previous list _at the same level_. (The
#   previous list may be a sibling element, or it may be an 'nth-cousin', sharing any common
#   ancestor element.)
#
#
# :label-skip -- skips 1 counter value if the attribute value is non-numeric. If the attr value is
#   an integer, advances the counter by that amount (_on top of_ the one increment that the counter
#   would normally advance anyway). If the attr value is '=' followed by an integer (or an
#   alphabetic count or roman numeral), then the counter value is set to that number.


# NOTE: There are other types of lists as well: <menu>/<li> and <dd>/<dt>/<dl>, but
# numbering these is likely a rarefied use case.


import lamarkdown
from lamarkdown.ext.label_support.labellers import Labeller
from lamarkdown.ext.label_support.label_templates import LabelTemplate, LabelTemplateParser
from lamarkdown.ext.label_support.label_renderers import CssLabelsRenderer, HtmlLabelsRenderer
from lamarkdown.ext.label_support.ref_resolver import RefResolver
from lamarkdown.lib.progress import Progress

import markdown

import abc
from typing import Callable, Dict, Iterable, List, Optional, Protocol, Set, Union
from xml.etree.ElementTree import Element

NAME = 'la.labels'

LABEL_DIRECTIVE = ':label'
NO_LABEL_DIRECTIVE = ':no-label'


class LabelControl:
    def __init__(self,
                 default_templates: Dict[str, str],
                 use_css_rendering: Set[str],
                 recursor: Callable[[Element,Iterable[Element]], None],
                 parser: LabelTemplateParser,
                 html_renderer: HtmlLabelsRenderer,
                 css_renderer: Optional[CssLabelsRenderer],
                 ref_resolver: RefResolver,
                 progress: Progress):

        self._default_template_str = default_templates
        self._use_css_rendering = use_css_rendering
        self._recursor = recursor
        self._parser = parser
        self._html_renderer = html_renderer
        self._css_renderer = css_renderer
        self._renderers: Dict[str, LabelRenderer] = {}
        self._ref_resolver = ref_resolver
        self._progress = progress

        self._stack: List[Labeller] = []
        self._labellers = {}
        self._next_id = 0

    def clear_children(self, labeller: Labeller):
        for child_labeller in labeller.children:
            try:
                self._stack.remove(child_labeller)
            except ValueError:
                pass  # Doesn't matter if not in stack
        labeller.children.clear()

    def remove_labeller(self, labeller: Labeller):
        self.clear_children(labeller)
        try:
            self._stack.remove(labeller)
        except ValueError:
            pass

    def find(self, element_type: str) -> Optional[Labeller]:
        if element_type is None:
            return None
        for labeller in reversed(self._stack):
            if labeller.element_type.startswith(element_type):
                return labeller
        return None

    def get_default_template(self, *element_types: str) -> str:
        for t in element_types:
            if template := self._default_template_str.get(t):
                return template
        return None

    def _get_renderer(self, element_type: str):

        if self._css_renderer is None:
             return self._html_renderer

        renderer = self._renderers.get(element_type)
        if renderer is None:
            renderer = (
                self._css_renderer if any(element_type.startswith(t)
                                          for t in self._use_css_rendering)
                else self._html_renderer
            )
            self._renderers[element_type] = renderer

        return renderer

    def _make_labeller(self,
            element_type: str,
            template: Union[str, LabelTemplate],
            parent: Optional[Labeller] = None,
            count: int = 0):

        _template = self._parser.parse(template) if isinstance(template, str) else template
        _parent = self.find(_template.parent_type) if parent is None else parent
        use_css = isinstance(self._get_renderer(element_type), CssLabelsRenderer)

        # We cache labellers, reusing ones that share the same visual info and same parents. This
        # is done to optimise the output (fewer CSS declarations), _not_ processing time or memory
        # usage.

        key_list = [_template.counter_type, use_css, _template.prefix, _template.suffix]
        cur_parent = _parent
        while cur_parent is not None:
            key_list.append(cur_parent._template.counter_type)
            key_list.append(_template.separator)
            cur_parent = cur_parent.parent
        key = tuple(key_list)

        labeller = self._labellers.get(key)
        if labeller is None:
            if use_css:
                css_id = self._next_id
                self._next_id += 1
                self._labellers[key] = labeller
            else:
                css_id = None

            labeller = Labeller(element_type, _template, _parent, count, css_id)
            self._labellers[key] = labeller

        labeller.count = count

        if _parent is not None:
            _parent.add_child(labeller)

        return labeller


    def new_labeller(self, element_type: str, template: Union[str, LabelTemplate]) -> Labeller:
        labeller = self._make_labeller(element_type, template)
        self._stack.append(labeller)
        return labeller

    def replace_labeller(self,
                         old_labeller: Labeller,
                         element_type: str,
                         new_template: Union[str, LabelTemplate]):
        labeller = self._make_labeller(element_type, new_template, old_labeller.parent)
        self.clear_children(old_labeller)
        self._stack[self._stack.index(old_labeller)] = labeller
        return labeller

    def render(self, labeller: Labeller, container: Element, item: Element):
        self._get_renderer(labeller.element_type).render_labelled_element(labeller,
                                                                          container, item)

    def render_none(self, element_type: str, container: Element, item: Element):
        self._get_renderer(element_type).render_no_labelled_element(container, item)

    def resolve_refs(self, element: Element):
        self._ref_resolver.resolve_refs(element, self.find)

    def recurse(self, element: Element, exclude: Iterable[Element] = []):
        self._recursor(element, exclude)

    @property
    def progress(self):
        return self._progress



class LabelProcessor(abc.ABC):
    def reset(self):
        pass

    @abc.abstractmethod
    def run(self, element: Element, control: LabelControl):
        ...


class HeadingLabelProcessor(LabelProcessor):
    def reset(self):
        self._previous_h_level = -1

    def test(self, element: Element) -> bool:
        return element.tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def run(self, element: Element, control: LabelControl):

        if element.attrib.pop(NO_LABEL_DIRECTIVE, None):
            control.render_none(element.tag, None, element)
            control.resolve_refs(element)
            return

        cur_h_level = int(element.tag[1])

        # Maybe a labeller already exists (from a previous sibling heading)
        labeller = control.find(element.tag)

        if labeller is None:
            # If no labeller exists, first see if there's a ':label' directive
            template = element.attrib.pop(LABEL_DIRECTIVE, None)

            # Failing that, see if a parent heading labeller specifies an inner template
            if template is None and (
                    outer_labeller := control.find(f'h{cur_h_level - 1}')) is not None:

                template = outer_labeller.template.inner_template

            # Failing that, maybe a configuration option is applicable
            if template is None: # and cur_h_level == self._h_level:
                template = control.get_default_template('h', element.tag)

            if template is not None:
                labeller = control.new_labeller(element.tag, template)

        elif new_template := element.attrib.pop(LABEL_DIRECTIVE, None):
            # A labeller does already exist, but a new template has been given
            labeller = control.replace_labeller(labeller, element.tag, new_template)

        if self._previous_h_level > cur_h_level:
            # Finishing (at least) one heading level, and continuing with a higher- level
            # heading.

            for i in range(self._previous_h_level, cur_h_level, -1):
                if (inner_labeller := control.find(f'h{i}')) is not None:
                    control.remove_labeller(inner_labeller)

        self._previous_h_level = cur_h_level

        if labeller is not None:
            labeller.count += 1
            control.render(labeller, None, element)

        control.resolve_refs(element)


class ListLabelProcesor(LabelProcessor):
    def test(self, element: Element) -> bool:
        return element.tag in {'ol', 'ul'}

    def run(self, element: Element, control: LabelControl):
        template: Union[None, str, LabelTemplate] = element.attrib.pop(LABEL_DIRECTIVE, None)

        outer_labeller = control.find(element.tag)
        if template is None and outer_labeller is not None:
            template = outer_labeller.template.inner_template

        if template is None and outer_labeller is None:
            template = control.get_default_template(element.tag)

        if template is None:
            control.resolve_refs(element)
            control.recurse(element)
            return

        labeller = control.new_labeller(element.tag, template)
        control.resolve_refs(element)

        for li in element:
            # Lists generally contain just <li> elements, but it doesn't hurt to check.
            if li.tag == 'li':
                if li.attrib.pop(NO_LABEL_DIRECTIVE, None):
                    control.render_none(element.tag, element, li)

                else:
                    if new_template := li.attrib.pop(LABEL_DIRECTIVE, None):
                        labeller = control.replace_labeller(labeller, element.tag, new_template)

                    labeller.count += 1
                    control.render(labeller, element, li)

                control.resolve_refs(li)
                control.recurse(li)
                control.clear_children(labeller)

        control.remove_labeller(labeller)


class FigureLabelProcessor(LabelProcessor):
    def reset(self):
        self.first_child = True
        self.level = 0

    def test(self, element: Element) -> bool:
        return element.tag in {'figure', 'table'}

    def run(self, element: Element, control: LabelControl):
        caption_tag = 'figcaption' if element.tag == 'figure' else 'caption'
        fig_caption = (
            element[0]       if element[0].tag == caption_tag
            else element[-1] if element[-1].tag == caption_tag
            else None
        )

        if element.tag == 'table':
            element_type = 'table'

        else:
            css_classes = [c.lower() for c in element.get('class').split()]
            css_type_guess = {
                t
                for t, words in [('figure',  ('figure', 'picture', 'image', 'diagram')),
                                 ('table',   ('table', 'tabular')),
                                 ('math',    ('math', 'equation', 'formula')),
                                 ('listing', ('listing', 'code'))]
                if any(cls.startswith(word) or cls.endswith(word)
                        for cls in css_classes
                        for word in words)
            }

            children = [e for e in element if e is not fig_caption]
            element_type = (
                css_type_guess.pop() if len(css_type_guess) == 1
                else 'table'         if all(c.tag == 'table' for c in children)
                else 'math'          if all(c.tag == 'math'  for c in children)
                else 'listing'       if all(c.tag in ['code', 'pre'] for c in children)
                else 'figure'
            )

        if (element.attrib.pop(NO_LABEL_DIRECTIVE)
                or (fig_caption is not None and figcaption.attrib.pop(NO_LABEL_DIRECTIVE))):

            control.resolve_refs(element)
            if fig_caption is None:
                pass
            else:
                control.resolve_refs(fig_caption)
                control.render_none(element_type, None, fig_caption)

            control.recurse(element)
            return


        if fig_caption is None:
            fig_caption = Element(caption_tag)
            fig_caption.tail = element.text
            element.text = None
            element.insert(0, fig_caption)


        template1 = element.attrib.pop(LABEL_DIRECTIVE, None)
        template2 = fig_caption.attrib.pop(LABEL_DIRECTIVE, None)
        if template1 and template2:
            if template1 == template2:
                control.progress.warning(
                    NAME,
                    msg = (f':label="{template1}" given twice for the same {element_type}'))
            else:
                control.progress.warning(
                    NAME,
                    msg = (f'Conflicting label templates, :label="{template1}" and '
                           f':label="{template2}", given for the same {element_type}'))

        template: Union[None, str, LabelTemplate] = template1 or template2

        labeller = control.find(element_type)
        if self._first_child or labeller is None:
            # outer_labeller = control.find(element_type)
            if labeller is not None:
                template = labeller.template.inner_template

            if template is None and self._level == 0:
                template = control.get_default_template(element_type)

            if template is None:
                control.resolve_refs(element)
                control.recurse(element)
                return

            labeller = control.new_labeller(element.tag, template)

        elif template is not None:
            labeller = control.replace_labeller(labeller, element_type, template)

        control.resolve_refs(element)
        control.resolve_refs(fig_caption)

        self._first_child = True
        self._level += 1
        control.recurse(element, exclude = [fig_caption])
        self._first_child = False
        self._level -= 1
        control.remove_labeller(labeller)


class LabelsTreeProcessor(markdown.treeprocessors.Treeprocessor):

    def __init__(self,
                 md,
                 label_processors: List[LabelProcessor],
                 default_templates: Dict[str, str],
                 use_css_rendering: Set[str],
                 parser: LabelTemplateParser,
                 ref_resolver: RefResolver,
                 html_renderer: HtmlLabelsRenderer,
                 css_renderer: Optional[CssLabelsRenderer],
                 progress: Progress):

        super().__init__(md)
        self._label_processors = label_processors
        self._default_templates = default_templates
        self._use_css_rendering = use_css_rendering
        self._parser = parser
        self._ref_resolver = ref_resolver
        self._html_renderer = html_renderer
        self._css_renderer = css_renderer
        self._progress = progress

    def run(self, root: Element):
        self._ref_resolver.find_refs(root)
        self._control = LabelControl(default_templates = self._default_templates,
                                     use_css_rendering = self._use_css_rendering,
                                     recursor = self._recurse,
                                     parser = self._parser,
                                     ref_resolver = self._ref_resolver,
                                     html_renderer = self._html_renderer,
                                     css_renderer = self._css_renderer,
                                     progress = self._progress)

        for label_proc in self._label_processors:
            label_proc.reset()

        self._apply_labellers(root)
        return root

    def _apply_labellers(self, element: Element):
        for label_proc in self._label_processors:
            if label_proc.test(element):
                label_proc.run(element, self._control)
                break
        else:
            self._control.resolve_refs(element)
            self._recurse(element, [])

    def _recurse(self, element: Element, exclude: Iterable[Element]):
        for child in element:
            if element not in exclude:
                self._apply_labellers(child)


_FN_DEFAULT = lambda: 0  # noqa: E731


class LabelsExtension(markdown.Extension):
    def __init__(self, **kwargs):
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass  # Use default defaults

        self.config = {
            'progress': [
                p.progress if p else Progress(),
                'An object accepting progress messages.'
            ],

            'css_fn': [
                lamarkdown.css if p else _FN_DEFAULT,
                'Callback function accepting CSS code via a string parameter. This enables CSS-'
                'based numbering (for <ol> elements). This may be "None", in which case list '
                'labels will be computed at compile-time and embedded in the HTML as plain text.'
            ],

            'label_processors': [
                [HeadingLabelProcessor(), ListLabelProcesor(), FigureLabelProcessor()],
                'The processors to be invoked to coordinate the labelling of elements.'
            ],

            'css_rendering': [
                {'ol', 'ul'}
            ],

            'labels': [
                {},
                'Default label template for each element type, to be applied at the outer-most '
                'level.'
            ],
        }
        super().__init__(**kwargs)


    def extendMarkdown(self, md):
        # Note: it may be wise to load the la.attr_prefix extension alongside this one, because it
        # provides a convenient way to apply directives. However, attr_prefix isn't loaded
        # automatically here, because this extension might still be useful without it.

        css_fn = self.getConfig('css_fn')

        tree_proc = LabelsTreeProcessor(
            md,
            label_processors = self.getConfig('label_processors'),
            default_templates = self.getConfig('labels'),
            use_css_rendering = self.getConfig('css_rendering'),
            parser = LabelTemplateParser(),
            ref_resolver = RefResolver(),
            html_renderer = HtmlLabelsRenderer(),
            css_renderer = None if css_fn is _FN_DEFAULT else CssLabelsRenderer(css_fn),
            progress = self.getConfig('progress')
        )

        md.treeprocessors.register(tree_proc, 'la-labels-tree', 6)

        # Priority must be:
        # * Lower than the TreeProcessors of 'attr_list' (priority 8) and 'la.attr_prefix' (15),
        #   because they will supply the directives (as element attributes) that we consume here.
        #
        # * Higher than the TreeProcessor of 'toc' (priority 5), because heading elements must be
        #   labelled before the table-of-contents is built, or the labels will be omitted from the
        #   ToC.



def makeExtension(**kwargs):
    return LabelsExtension(**kwargs)




# ---


#
# class LabelProcessor:
#     def __init__(self,
#                  tags: Set[str],
#                  labeller_factory: LabellerFactory
#                  renderer: LabelRenderer):
#
#         self._tags = tags
#         self.labeller_factory = labeller_factory
#         self.renderer = renderer
#
#     # def render(self, element):
#     #     self._renderer.render_labelled_element(labeller, element, li)
#
#     def reset(self):
#         pass
#
#     @property
#     def tags(self):
#         return self._tags
#
#     def apply(self,
#               element: Element,
#               stack: LabellerStack,
#               resolve_refs: Callable[[Element], None],
#               recurse: Callable[[Element], None]):
#         ...
#
#
#
# class HeadingLabelProcessor:
#     def __init__(self,
#                  labeller_factory: LabellerFactory
#                  renderer: LabelRenderer,
#                  default_template: LabelTemplate):
#         super().__init__({'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}, labeller_factory, renderer)
#         self._default_template = default_template
#
#
#     def reset(self):
#         self._previous_h_level = -1
#
#
#     def apply(self,
#               element: Element,
#               stack: LabellerStack,
#               resolve_refs: Callable[[Element], None],
#               recurse: Callable[[Element], None]):
#
#         if element.attrib.pop(NO_LABEL_DIRECTIVE, None):
#             self.renderer.render_no_labelled_element(None, element)
#
#         elif (labeller := self._get_heading_labeller(element, stack)) is not None:
#             labeller.count += 1
#             self.renderer.render_labelled_element(labeller, None, element)
#
#         resolve_refs(element)
#
#
#     def _get_heading_labeller(self, element, stack: LabellerStack) -> Optional[Labeller]:
#
#         cur_h_level = int(element.tag[1])
#
#         # Maybe a labeller already exists (from a previous sibling heading)
#         labeller = stack.find(element.tag)
#
#         if labeller is None:
#             # If no labeller exists, first see if there's a ':label' directive
#             template = None
#             if (template_str := element.attrib.pop(LABEL_DIRECTIVE, None)) is not None:
#                 template = self._parser.parse(template_str)
#
#             # Failing that, see if a parent heading labeller specifies an inner template
#             if template is None and (
#                     outer_labeller := stack.find(f'h{cur_h_level - 1}')) is not None:
#
#                 template = outer_labeller.template.inner_template
#
#             # Failing that, maybe the configuration option is applicable
#             if template is None and cur_h_level == self._h_level:
#                 template = self._default_template
#
#             # TODO: catch LabelTemplateException from self._parser.parse()
#
#             if template is not None:
#                 labeller = self._labeller_factory.get(
#                     element.tag,
#                     template,
#                     parent = stack.find(template.parent_type),
#                     css = False
#                 )
#                 stack.append(labeller)
#
#         elif (new_template_str := element.attrib.pop(LABEL_DIRECTIVE, None)) is not None:
#
#             # A labeller does already exist, but a new template has been given
#             stack.remove(labeller)
#             new_labeller = self._labeller_factory.get(
#                 element_type = element.tag,
#                 template = self._parser.parse(new_template_str),
#                 parent = labeller.parent,
#                 css = False
#             )
#             stack.append(new_labeller)
#             labeller = new_labeller
#
#         if self._previous_h_level > cur_h_level:
#             # Finishing (at least) one heading level, and continuing with a higher- level
#             # heading.
#
#             for i in range(self._previous_h_level, cur_h_level, -1):
#                 if (inner_labeller := self._find_labeller(f'h{i}')) is not None:
#                     stack.remove(inner_labeller)
#
#         self._previous_h_level = cur_h_level
#
#         return labeller
#
#
# class ListLabelProcessor(LabelProcessor):
#     def __init__(self,
#                  labeller_factory: LabellerFactory
#                  renderer: LabelRenderer,
#                  ol_default_template: LabelTemplate,
#                  ul_default_template: LabelTemplate):
#         super().__init__({'ol', 'ul'}, labeller_factory, renderer)
#         self._ol_default_template = ol_default_template
#         self._ul_default_template = ul_default_template
#
#
#     def apply(self,
#               element: Element,
#               stack: LabellerStack,
#               resolve_refs: Callable[[Element], None],
#               recurse: Callable[[Element], None]):
#
#         template: Union[None, str, LabelTemplate] = element.attrib.pop(LABEL_DIRECTIVE, None)
#
#         outer_labeller = self._find_labeller(element_type)
#         if template is None and outer_labeller is not None:
#             template = outer_labeller.template.inner_template
#
#         if template is None and outer_labeller is None:
#             template = (
#                 self._ol_default_template if element.tag == 'ol' else self._ul_default_template)
#
#         if template is None:
#             resolve_refs(element)
#             recurse(element)
#             return
#
#         labeller = self.labeller_factory.get(
#             element_type = element.tag,
#             template = template,
#             parent = stack.find(template.parent_type)
#         )
#
#         stack.append(labeller)
#         resolve_refs(element)
#
#         for li in element:
#             # Lists generally contain just <li> elements, but it doesn't hurt to check.
#             if li.tag == 'li':
#                 if li.attrib.pop(NO_LABEL_DIRECTIVE, None):
#                     self.renderer.render_no_labelled_element(element, li)
#
#                 else:
#                     if new_template_str := li.attrib.pop(LABEL_DIRECTIVE, None):
#                         new_labeller = self._labeller_factory.get(
#                             element_type = element.tag,
#                             template = self._parser.parse(new_template_str),
#                             parent = labeller.parent
#                         )
#                         stack.replace(labeller, new_labeller)
#                         labeller = new_labeller
#
#                     labeller.count += 1
#                     self.renderer.render_labelled_element(labeller, element, li)
#
#                 resolve_refs(li)
#                 recurse(li)
#                 stack.clear_children(labeller)
#
#         stack.remove(labeller)
#
#
# class FigureLabelProcessor(LabelProcessor):
#     def __init__(self,
#                  labeller_factory: LabellerFactory
#                  renderer: LabelRenderer,
#                  default_templates: Dict[str, LabelTemplate]):
#         super().__init__({'figure', 'table'}, labeller_factory, renderer)
#         self._default_templates = default_templates
#
#
#     def apply(self,
#               element: Element,
#               stack: LabellerStack,
#               resolve_refs: Callable[[Element], None],
#               recurse: Callable[[Element], None]):
#
#         caption_tag = 'figcaption' if element.tag == 'figure' else 'caption'
#         fig_caption = (
#             element[0]       if element[0].tag == caption_tag
#             else element[-1] if element[-1].tag == caption_tag
#             else None
#         )
#
#
#         # fig:no-label   cap (none, no-label, blank) | cap:create   render (none, no-label, label)
#         # ---------------------------------------------------------------------------------------
#         # False          None                        | True         label
#         # False          No-label                    | False        no-label
#         # False          Blank                       | False        label
#         # True           None                        | False        none
#         # True           No-label                    | False        no-label
#         # True           Blank                       | False        no-label
#
#         if (element.attrib.pop(NO_LABEL_DIRECTIVE)
#                 or (fig_caption is not None and figcaption.attrib.pop(NO_LABEL_DIRECTIVE))):
#
#             resolve_refs(element)
#             if fig_caption is None:
#                 pass
#             else:
#                 resolve_refs(fig_caption)
#                 self._fig_renderer.render_no_labelled_element(None, fig_caption)
#
#             recurse(element)
#             return
#
#
#         if fig_caption is None:
#             fig_caption = Element(caption_tag)
#             fig_caption.tail = element.text
#             element.text = None
#             element.insert(0, fig_caption)
#
#         if element.tag == 'table':
#             element_type = 'table'
#
#         else:
#             css_classes = [c.lower() for c in element.get('class').split()]
#             css_type_guess = {
#                 t
#                 for t, words in [('figure',  ('figure', 'picture', 'image', 'diagram')),
#                                  ('table',   ('table', 'tabular')),
#                                  ('math',    ('math', 'equation', 'formula')),
#                                  ('listing', ('listing', 'code'))]
#                 if any(cls.startswith(word) or cls.endswith(word)
#                         for cls in css_classes
#                         for word in words)
#             }
#
#             children = [e for e in element if e is not fig_caption]
#             element_type = (
#                 css_type_guess.pop() if len(css_type_guess) == 1
#                 else 'table'         if all(c.tag == 'table' for c in children)
#                 else 'math'          if all(c.tag == 'math'  for c in children)
#                 else 'listing'       if all(c.tag in ['code', 'pre'] for c in children)
#                 else 'figure'
#             )
#
#         template: Union[None, str, LabelTemplate] = (
#             element.attrib.pop(LABEL_DIRECTIVE, None)
#             or fig_caption.attrib.pop(LABEL_DIRECTIVE, None))
#
#         outer_labeller = stack.find(element_type)
#         if template is None and outer_labeller is not None:
#             template = outer_labeller.template.inner_template
#
#         if template is None and outer_labeller is None:
#             template = self._default_template.get(element_type)
#
#         if template is None:
#             resolve_refs(element)
#             recurse(element)
#             return
#
#         labeller = self.labeller_factory.get(
#             element_type = element_type,
#             template = template,
#             parent = stack.find(template.parent_type)
#         )
#         self.renderer.render_labelled_element(labeller, None, fig_caption)
#
#         stack.append(labeller)
#         resolve_refs(element)
#         resolve_refs(fig_caption)
#         recurse(element, lambda e: e is not fig_caption)
#         stack.remove(labeller)
#
#
#
#
# class LabelsTreeProcessor(markdown.treeprocessors.Treeprocessor):
#
#     def __init__(self,
#                  md,
#                  label_processors: List[LabelProcessor],
#                  # parser = LabelTemplateParser(),
#                  labeller_factory = LabellerFactory(),
#                  ref_resolver = RefResolver()):
#
#         super().__init__(md)
#         # self._parser = parser
#         self._label_processors = label_processors
#         self._labeller_factory = labeller_factory
#         self._ref_resolver = ref_resolver
#
#     def run(self, root: Element):
#         self._ref_resolver.find_refs(root)
#         self._labeller_stack = LabellerStack()
#
#         for label_proc in self._label_processors:
#             label_proc.reset()
#
#         self._apply_labellers(root)
#         return root
#
#     def _apply_labellers(self, element: Element):
#         for label_proc in self._label_processors:
#             if element.tags in label_proc.tags:
#                 label_proc.apply(element, self._labeller_stack, self._resolve_refs, self._recurse)
#                 break
#         else:
#             self._resolve_refs(element)
#             self._recurse(element)
#
#     def _recurse(self, element: Element, include: Callable[[Element],bool] = lambda: True):
#         for child in element:
#             if include(child):
#                 self._apply_labellers(child)
#
#     def _resolve_refs(self, element: Element):
#         self._ref_resolver.resolve_refs(element, self._labeller_stack.find)



# class LabelsExtension(markdown.Extension):
#     def __init__(self, **kwargs):
#         p = None
#         try:
#             from lamarkdown.lib.build_params import BuildParams
#             p = BuildParams.current
#         except ModuleNotFoundError:
#             pass  # Use default defaults
#
#         self.config = {
#             'css_fn': [
#                 lamarkdown.css if p else _FN_DEFAULT,
#                 'Callback function accepting CSS code via a string parameter. This enables CSS-'
#                 'based numbering (for <ol> elements). This may be "None", in which case list '
#                 'labels will be computed at compile-time and embedded in the HTML as plain text.'
#             ],
#
#             'h_labels': [
#                 _LABEL_DEFAULT,
#                 'Default heading template, to be applied at heading level "h_level".'
#             ],
#
#             'h_level': [
#                 1,
#                 'Heading level at which to apply the default heading labels ("h_labels").'
#             ],
#
#             'ol_labels': [
#                 _LABEL_DEFAULT,
#                 'Default ordered list template, to be applied starting at the top-most ordered '
#                 'list level.'
#             ],
#
#             'ul_labels': [
#                 _LABEL_DEFAULT,
#                 'Default unordered list template, to be applied starting at the top-most '
#                 'unordered list level.'
#             ],
#
#             'figure_labels': [
#                 _LABEL_DEFAULT,
#                 ''
#             ]
#         }
#         super().__init__(**kwargs)
#
#
#     def extendMarkdown(self, md):
#         # Note: it may be wise to load the la.attr_prefix extension alongside this one, because it
#         # provides a convenient way to apply directives. However, attr_prefix isn't loaded
#         # automatically here, because this extension might still be useful without it.
#
#         css_fn = self.getConfig('css_fn')
#         h_template = self.getConfig('h_labels')
#         ul_template = self.getConfig('ul_labels')
#         ol_template = self.getConfig('ol_labels')
#         figure_template = self.getConfig('figure_labels')
#
#         tree_proc = LabelsTreeProcessor(
#             md,
#             css_fn      = None if css_fn is _FN_DEFAULT else css_fn,
#             h_template  = None if h_template is _LABEL_DEFAULT else h_template,
#             h_level     = self.getConfig('h_level'),
#             ul_template = None if ul_template is _LABEL_DEFAULT else ul_template,
#             ol_template = None if ol_template is _LABEL_DEFAULT else ol_template,
#
#         )
#
#         md.treeprocessors.register(tree_proc, 'la-labels-tree', 6)
#
#         # Priority must be:
#         # * Lower than the TreeProcessors of 'attr_list' (priority 8) and 'la.attr_prefix' (15),
#         #   because they will supply the directives (as element attributes) that we consume here.
#         #
#         # * Higher than the TreeProcessor of 'toc' (priority 5), because heading elements must be
#         #   labelled before the table-of-contents is built, or the labels will be omitted from the
#         #   ToC.
#
#
#
# def makeExtension(**kwargs):
#     return LabelsExtension(**kwargs)
#


# -----





# class LabelsTreeProcessor(markdown.treeprocessors.Treeprocessor):
#
#     def __init__(self,
#                  md,
#                  css_fn,
#                  h_template,
#                  h_level,
#                  ol_template,
#                  ul_template,
#                  figure_template):
#         super().__init__(md)
#         self._parser = LabelTemplateParser()
#         self._labeller_factory = LabellerFactory()
#
#         self._h_template = h_template and self._parser.parse(h_template)
#         self._h_level = h_level
#         self._ol_template = ol_template and self._parser.parse(ol_template)
#         self._ul_template = ul_template and self._parser.parse(ul_template)
#         self._figure_template = figure_template and self._parser.parse(figure_template)
#
#         html_renderer = HtmlLabelsRenderer()
#         self._h_renderer = html_renderer
#         self._l_renderer = CssLabelsRenderer(css_fn) if css_fn else html_renderer
#         self._fig_renderer = html_renderer
#
#         self._ref_resolver = RefResolver()
#
#
#     def run(self, root: Element):
#         self._ref_resolver.find_refs(root)
#         self._labeller_stack: List[Labeller] = []
#         self._previous_h_level = -1
#         self._recurse(root)
#         return root
#
#
#     def _recurse(self, element):
#         if element.tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
#
#             if NO_LABEL_DIRECTIVE in element.attrib:
#                 del element.attrib[NO_LABEL_DIRECTIVE]
#                 self._h_renderer.render_no_labelled_element(None, element)
#
#             elif (labeller := self._get_heading_labeller(element)) is not None:
#                 labeller.count += 1
#                 self._h_renderer.render_labelled_element(labeller, None, element)
#
#             self._ref_resolver.resolve_refs(element, self._find_labeller)
#
#             # Note: we don't recurse into heading elements. If you have <h2><ul>...</ul></h2>,
#             # you get what you deserve.
#
#
#         elif (element.tag in {'ul', 'ol'}
#               and (labeller := self._get_internal_labeller(
#                   element,
#                   None,  # lists have no caption element
#                   element.tag,
#                   {'ul': self._ul_template, 'ol': self._ol_template}[element.tag]))):
#
#             self._labeller_stack.append(labeller)
#             self._ref_resolver.resolve_refs(element, self._find_labeller)
#
#             for li in element:
#                 # Lists generally contain just <li> elements, but it doesn't hurt to check.
#                 if li.tag == 'li':
#                     if NO_LABEL_DIRECTIVE in li.attrib:
#                         del li.attrib[NO_LABEL_DIRECTIVE]
#                         self._l_renderer.render_no_labelled_element(element, li)
#
#                     else:
#                         if (new_template_str := li.get(LABEL_DIRECTIVE)) is not None:
#                             del li.attrib[LABEL_DIRECTIVE]
#                             new_labeller = self._labeller_factory.get(
#                                 element_type = element.tag,
#                                 template = self._parser.parse(new_template_str),
#                                 parent = labeller.parent
#                             )
#                             self._labeller_stack[
#                                 self._labeller_stack.index(labeller)] = new_labeller
#                             labeller = new_labeller
#
#                         labeller.count += 1
#                         self._l_renderer.render_labelled_element(labeller, element, li)
#
#                     self._ref_resolver.resolve_refs(li, self._find_labeller)
#
#                     for child_elem in li:
#                         self._recurse(child_elem)
#
#                     # Clear all other labellers that have become dependent on this one.
#                     for child_labeller in labeller.children:
#                         try:
#                             self._labeller_stack.remove(child_labeller)
#                         except ValueError:
#                             pass  # Doesn't matter if not in stack
#                     labeller.children.clear()
#
#
#             self._labeller_stack.remove(labeller)
#
#
#         elif (element.tag in {'figure', 'table'}
#
#             caption_tag = 'figcaption' if element.tag == 'figure' else 'caption'
#             fig_caption = (
#                 element[0]       if element[0].tag == caption_tag
#                 else element[-1] if element[-1].tag == caption_tag
#                 else None
#             )
#
#
#             # fig:no-label   cap (none, no-label, blank) | cap:create   render (none, no-label, label)
#             # ---------------------------------------------------------------------------------------
#             # False          None                        | True         label
#             # False          No-label                    | False        no-label
#             # False          Blank                       | False        label
#             # True           None                        | False        none
#             # True           No-label                    | False        no-label
#             # True           Blank                       | False        no-label
#
#             if (element.attrib.pop(NO_LABEL_DIRECTIVE)
#                     or (fig_caption is not None and figcaption.attrib.pop(NO_LABEL_DIRECTIVE))):
#
#                 if fig_caption is None:
#                     pass
#                 else:
#                     self._fig_renderer.render_no_labelled_element(None, fig_caption)
#
#             else:
#                 if fig_caption is None:
#                     fig_caption = Element(caption_tag)
#                     fig_caption.tail = element.text
#                     element.text = None
#                     element.insert(0, fig_caption)
#
#                 children = [e for e in element if e is not fig_caption]
#
#                 if element.tag == 'table':
#                     element_type = 'table'
#
#                 else:
#                     css_classes = [c.lower() for c in element.get('class').split()]
#                     css_type_guess = {
#                         t
#                         for t, words in [('figure',  ('figure', 'picture', 'image', 'diagram')),
#                                          ('table',   ('table', 'tabular')),
#                                          ('math',    ('math', 'equation', 'formula')),
#                                          ('listing', ('listing', 'code'))]
#                         if any(cls.startswith(word) or cls.endswith(word)
#                                for cls in css_classes
#                                for word in words)
#                     }
#
#                     element_type = (
#                         css_type_guess.pop() if len(css_type_guess) == 1
#                         else 'table'         if all(c.tag == 'table' for c in children)
#                         else 'math'          if all(c.tag == 'math'  for c in children)
#                         else 'listing'       if all(c.tag in ['code', 'pre'] for c in children)
#                         else 'figure'
#                     )
#
#                 labeller := self._get_internal_labeller(element,
#                                                         fig_caption,
#                                                         element_type,
#                                                         self._figure_template.get(element_type))
#
#                 self._labeller_stack.append(labeller)
#                 self._fig_renderer.render_labelled_element(labeller, None, fig_caption)
#                 self._ref_resolver.resolve_refs(element, self._find_labeller)
#                 self._ref_resolver.resolve_refs(fig_caption, self._find_labeller)
#
#                 for child_elem in children:
#                     self._recurse(child_elem)
#
#                 self._labeller_stack.remove(labeller)
#
#         else:
#             # Non-labelled elements
#             self._ref_resolver.resolve_refs(element, self._find_labeller)
#             for child_elem in element:
#                 self._recurse(child_elem)
#
#
#
#
#     def _get_internal_labeller(self,
#                                element: Element,
#                                caption_element: Optional[Element],
#                                element_type: str,
#                                template_setting: LabelTemplate) -> Optional[Labeller]:
#         template = None
#         if ((template_str := element.attrib.pop(LABEL_DIRECTIVE, None))
#                 or (caption_element is not None
#                     and (template_str := caption_element.attrib.pop(LABEL_DIRECTIVE, None)))):
#             template = self._parser.parse(template_str)
#
#         # Otherwise, see if there's a inner template
#         outer_labeller = self._find_labeller(element_type)
#         if template is None and outer_labeller is not None:
#             template = outer_labeller.template.inner_template
#
#         # Otherwise, maybe the configuration option is applicable (if this is a top-level list)
#         if template is None and outer_labeller is None:
#             # template = self._ul_template if element.tag == 'ul' else self._ol_template
#             template = template_setting
#
#         if template is None:
#             return None
#         else:
#             return self._labeller_factory.get(
#                 element_type = element_type,
#                 template = template,
#                 parent = self._find_labeller(template.parent_type)
#             )
#
#
#     # def _find_labeller(self, parent_type: Optional[str]) -> Optional[Labeller]:
#     #     if parent_type is None:
#     #         return None
#     #     for labeller in reversed(self._labeller_stack):
#     #         if labeller.element_type.startswith(parent_type):
#     #             return labeller
#     #     return None
#
#
# _LABEL_DEFAULT = 'default'
# _FN_DEFAULT = lambda: 0  # noqa: E731
#
#
# class LabelsExtension(markdown.Extension):
#     def __init__(self, **kwargs):
#         p = None
#         try:
#             from lamarkdown.lib.build_params import BuildParams
#             p = BuildParams.current
#         except ModuleNotFoundError:
#             pass  # Use default defaults
#
#         self.config = {
#             'css_fn': [
#                 lamarkdown.css if p else _FN_DEFAULT,
#                 'Callback function accepting CSS code via a string parameter. This enables CSS-'
#                 'based numbering (for <ol> elements). This may be "None", in which case list '
#                 'labels will be computed at compile-time and embedded in the HTML as plain text.'
#             ],
#
#             'h_labels': [
#                 _LABEL_DEFAULT,
#                 'Default heading template, to be applied at heading level "h_level".'
#             ],
#
#             'h_level': [
#                 1,
#                 'Heading level at which to apply the default heading labels ("h_labels").'
#             ],
#
#             'ol_labels': [
#                 _LABEL_DEFAULT,
#                 'Default ordered list template, to be applied starting at the top-most ordered '
#                 'list level.'
#             ],
#
#             'ul_labels': [
#                 _LABEL_DEFAULT,
#                 'Default unordered list template, to be applied starting at the top-most '
#                 'unordered list level.'
#             ],
#
#             'figure_labels': [
#                 _LABEL_DEFAULT,
#                 ''
#             ]
#         }
#         super().__init__(**kwargs)
#
#
#     def extendMarkdown(self, md):
#         # Note: it may be wise to load the la.attr_prefix extension alongside this one, because it
#         # provides a convenient way to apply directives. However, attr_prefix isn't loaded
#         # automatically here, because this extension might still be useful without it.
#
#         css_fn = self.getConfig('css_fn')
#         h_template = self.getConfig('h_labels')
#         ul_template = self.getConfig('ul_labels')
#         ol_template = self.getConfig('ol_labels')
#         figure_template = self.getConfig('figure_labels')
#
#         tree_proc = LabelsTreeProcessor(
#             md,
#             css_fn      = None if css_fn is _FN_DEFAULT else css_fn,
#             h_template  = None if h_template is _LABEL_DEFAULT else h_template,
#             h_level     = self.getConfig('h_level'),
#             ul_template = None if ul_template is _LABEL_DEFAULT else ul_template,
#             ol_template = None if ol_template is _LABEL_DEFAULT else ol_template,
#
#         )
#
#         md.treeprocessors.register(tree_proc, 'la-labels-tree', 6)
#
#         # Priority must be:
#         # * Lower than the TreeProcessors of 'attr_list' (priority 8) and 'la.attr_prefix' (15),
#         #   because they will supply the directives (as element attributes) that we consume here.
#         #
#         # * Higher than the TreeProcessor of 'toc' (priority 5), because heading elements must be
#         #   labelled before the table-of-contents is built, or the labels will be omitted from the
#         #   ToC.
#
#
#
# def makeExtension(**kwargs):
#     return LabelsExtension(**kwargs)

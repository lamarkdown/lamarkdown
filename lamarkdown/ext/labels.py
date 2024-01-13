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


# TODO:
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

# TODO (future):
# - number <table><caption>... and <figure><figcaption>...
# - provide a way to define new numbering series (e.g., listings, equations, etc.)

# NOTE: There are other types of lists as well: <menu>/<li> and <dd>/<dt>/<dl>, but
# numbering these is likely a rarefied use case.


import lamarkdown
from lamarkdown.ext.label_support.labellers import Labeller, LabellerFactory
from lamarkdown.ext.label_support.label_templates import LabelTemplateParser
from lamarkdown.ext.label_support.label_renderers import CssLabelsRenderer, HtmlLabelsRenderer
from lamarkdown.ext.label_support.ref_resolver import RefResolver

import markdown

from typing import List, Optional
from xml.etree.ElementTree import Element

LABEL_DIRECTIVE = ':label'
NO_LABEL_DIRECTIVE = ':no-label'


class LabelsTreeProcessor(markdown.treeprocessors.Treeprocessor):

    def __init__(self, md, css_fn, h_template, h_level, ol_template, ul_template):
        super().__init__(md)
        self._parser = LabelTemplateParser()
        self._labeller_factory = LabellerFactory()

        self._h_template = h_template and self._parser.parse(h_template)
        self._h_level = h_level
        self._ol_template = ol_template and self._parser.parse(ol_template)
        self._ul_template = ul_template and self._parser.parse(ul_template)

        html_renderer = HtmlLabelsRenderer()
        self._h_renderer = html_renderer
        self._l_renderer = CssLabelsRenderer(css_fn) if css_fn else html_renderer

        self._ref_resolver = RefResolver()


    def run(self, root: Element):
        self._ref_resolver.find_refs(root)
        self._labeller_stack: List[Labeller] = []
        self._previous_h_level = -1
        self._recurse(root)
        return root


    def _recurse(self, element):
        if element.tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:

            if NO_LABEL_DIRECTIVE in element.attrib:
                del element.attrib[NO_LABEL_DIRECTIVE]
                self._h_renderer.render_no_labelled_element(None, element)

            elif (labeller := self._get_heading_labeller(element)) is not None:
                labeller.count += 1
                self._h_renderer.render_labelled_element(labeller, None, element)

            self._ref_resolver.resolve_refs(element, self._find_labeller)

            # Note: we don't recurse into heading elements. If you have <h2><ul>...</ul></h2>,
            # you get what you deserve.

        elif (element.tag in {'ul', 'ol'}
              and (labeller := self._get_list_labeller(element)) is not None):

            self._labeller_stack.append(labeller)
            self._ref_resolver.resolve_refs(element, self._find_labeller)

            for li in element:
                # Lists generally contain just <li> elements, but it doesn't hurt to check.
                if li.tag == 'li':
                    if NO_LABEL_DIRECTIVE in li.attrib:
                        del li.attrib[NO_LABEL_DIRECTIVE]
                        self._l_renderer.render_no_labelled_element(element, li)

                    else:
                        if (new_template_str := li.get(LABEL_DIRECTIVE)) is not None:
                            del li.attrib[LABEL_DIRECTIVE]
                            new_labeller = self._labeller_factory.get(
                                element_type = element.tag,
                                template = self._parser.parse(new_template_str),
                                parent = labeller.parent
                            )
                            self._labeller_stack[
                                self._labeller_stack.index(labeller)] = new_labeller
                            labeller = new_labeller

                        labeller.count += 1
                        self._l_renderer.render_labelled_element(labeller, element, li)

                    self._ref_resolver.resolve_refs(li, self._find_labeller)

                    for child_elem in li:
                        self._recurse(child_elem)

                    # Clear all other labellers that have become dependent on this one.
                    for child_labeller in labeller.children:
                        try:
                            self._labeller_stack.remove(child_labeller)
                        except ValueError:
                            pass  # Doesn't matter if not in stack
                    labeller.children.clear()


            self._labeller_stack.remove(labeller)

        else:
            # Non-labelled elements
            self._ref_resolver.resolve_refs(element, self._find_labeller)
            for child_elem in element:
                self._recurse(child_elem)


    def _get_heading_labeller(self, element) -> Optional[Labeller]:

        cur_h_level = int(element.tag[1])

        # Maybe a labeller already exists (from a previous sibling heading)
        labeller = self._find_labeller(element.tag)

        if labeller is None:
            # If no labeller exists, first see if there's a ':label' directive
            template = None
            if (template_str := element.get(LABEL_DIRECTIVE)) is not None:
                del element.attrib[LABEL_DIRECTIVE]
                template = self._parser.parse(template_str)

            # Failing that, see if a parent heading labeller specifies an inner template
            if template is None and (
                    outer_labeller := self._find_labeller(f'h{cur_h_level - 1}')) is not None:

                template = outer_labeller.template.inner_template

            # Failing that, maybe the configuration option is applicable
            if template is None and cur_h_level == self._h_level:
                template = self._h_template

            # TODO: catch LabelTemplateException from self._parser.parse()

            if template is not None:
                labeller = self._labeller_factory.get(
                    element.tag,
                    template,
                    parent = self._find_labeller(template.parent_type),
                    css = False
                )
                self._labeller_stack.append(labeller)

        elif (new_template_str := element.get(LABEL_DIRECTIVE)) is not None:

            # A labeller does already exist, but a new template has been given
            del element.attrib[LABEL_DIRECTIVE]
            self._labeller_stack.remove(labeller)
            new_labeller = self._labeller_factory.get(
                element_type = element.tag,
                template = self._parser.parse(new_template_str),
                parent = labeller.parent,
                css = False
            )
            self._labeller_stack.append(new_labeller)
            labeller = new_labeller

        if self._previous_h_level > cur_h_level:
            # Finishing (at least) one heading level, and continuing with a higher- level
            # heading.

            for i in range(self._previous_h_level, cur_h_level, -1):
                if (inner_labeller := self._find_labeller(f'h{i}')) is not None:
                    self._labeller_stack.remove(inner_labeller)

        self._previous_h_level = cur_h_level

        return labeller


    def _get_list_labeller(self, element) -> Optional[Labeller]:
        template = None
        if (template_str := element.get(LABEL_DIRECTIVE)) is not None:
            del element.attrib[LABEL_DIRECTIVE]
            template = self._parser.parse(template_str)

        # Otherwise, see if there's a inner template
        outer_labeller = self._find_labeller(element.tag)
        if template is None and outer_labeller is not None:
            template = outer_labeller.template.inner_template

        # Otherwise, maybe the configuration option is applicable (if this is a top-level list)
        if template is None and outer_labeller is None:
            template = self._ul_template if element.tag == 'ul' else self._ol_template

        if template is None:
            return None
        else:
            return self._labeller_factory.get(
                element_type = element.tag,
                template = template,
                parent = self._find_labeller(template.parent_type)
            )


    def _find_labeller(self, parent_type: Optional[str]) -> Optional[Labeller]:
        if parent_type is None:
            return None
        for labeller in reversed(self._labeller_stack):
            if labeller.element_type.startswith(parent_type):
                return labeller
        return None


_LABEL_DEFAULT = 'default'
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
            'css_fn': [
                lamarkdown.css if p else _FN_DEFAULT,
                'Callback function accepting CSS code via a string parameter. This enables CSS-'
                'based numbering (for <ol> elements). This may be "None", in which case list '
                'labels will be computed at compile-time and embedded in the HTML as plain text.'
            ],

            'h_labels': [
                _LABEL_DEFAULT,
                'Default heading template, to be applied at heading level "h_level".'
            ],

            'h_level': [
                1,
                'Heading level at which to apply the default heading labels ("h_labels").'
            ],

            'ol_labels': [
                _LABEL_DEFAULT,
                'Default ordered list template, to be applied starting at the top-most ordered '
                'list level.'
            ],

            'ul_labels': [
                _LABEL_DEFAULT,
                'Default unordered list template, to be applied starting at the top-most '
                'unordered list level.'
            ]
        }
        super().__init__(**kwargs)


    def extendMarkdown(self, md):
        # Note: it may be wise to load the la.attr_prefix extension alongside this one, because it
        # provides a convenient way to apply directives. However, attr_prefix isn't loaded
        # automatically here, because this extension might still be useful without it.

        css_fn = self.getConfig('css_fn')
        h_template = self.getConfig('h_labels')
        ul_template = self.getConfig('ul_labels')
        ol_template = self.getConfig('ol_labels')

        tree_proc = LabelsTreeProcessor(
            md,
            css_fn      = None if css_fn is _FN_DEFAULT else css_fn,
            h_template  = None if h_template is _LABEL_DEFAULT else h_template,
            h_level     = self.getConfig('h_level'),
            ul_template = None if ul_template is _LABEL_DEFAULT else ul_template,
            ol_template = None if ol_template is _LABEL_DEFAULT else ol_template,
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

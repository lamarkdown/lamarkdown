'''
# List Label Extension

---

## Configuration options

//Parameters:
//* h_level
//* ol_level
//* inner_h_level
//* inner_ol_level
//* counter
//* counter_list
//* element
//* element_list
//* style_list
//
//Applies to all <li> and <hx> elements.


h_labels=<template_list>
h_label_level=1..6 -- heading level at which to apply the h_label template list.
ul_labels=<template_list>
ol_labels=<template_list>

auto_label?? Can we devise a configuration option for applying labels automatically to arbitrary parts of the document tree? Potentially this could be generalised to some other extension, since :label is just an element attribute.





## Template syntax

template_list := template ( separator template )* [ separator '*' ]
template = literal* [ [ ('X' | 'L' | 'H' [level] ) literal+ ] format_spec literal* ]

separator := ',' followed by any amount of whitespace
literal := unquoted_literal | quoted_literal
unquoted_literal := any char except whitespace, a-z, A-Z and 0-9
quoted_literal := '"' ... '"' (FIXME)
level := any positive integer

A template lists consists of one or more comma (/whitespace)-separated templates, optionally ending in a '*'. The first (mandatory) template applies directly to the current list or list element. Subsequent templates apply to successive levels of child lists, _of the same fundamental type_ (sub-lists for lists, and sub-headings for headings). If present, the '*' causes the final template to apply indefinitely to any more deeply-nested lists/headings. (If '*' is omitted, then any lists nested more deeply are outside the scope of this template list.)

The `format_spec` refers to the numbering/labelling system for a given list or list element. It can be:
* `1`, for arabic numerals,
* `a`/`A`, for lower/uppercase English alphabetic numbering,
* `i`/`I`, for lower/uppercase Roman numerals,
* one of various terms accepted by the list-style-type CSS property; e.g., `lower-green`, `armenian`, etc. (Such labels are not necessarily _implemented_ by CSS. In some cases, Lamarkdown will need to calculate the actual numbering itself, and it won't necessarily support all CSS-supported numbering schemes.)

For <ul> elements, there's generally no numbering system required, and `format_spec` will generally be either:
1. Omitted altogether, leaving just the literal prefix; or
2. Given a value like 'square' or 'circle'.

Preceding this, if 'X', 'L' or 'H' is given, it refers to the label of the nearest _numbered_ ancestor element. Specifically, X means _any_ such element (though, again, only those with numbering systems, so generally not <ul> elements), L means a list element (almost certainly <ol>), H means any heading element, and H1-H6 mean the corresponding heading level. If such an ancestor element exists, its core label (minus any leading and trailing literals) will be inserted prior to the element's own number, along with an delimiting literal.

If X, L or H is given, but no such element exists, then no ancestor label will be inserted, _and_ the delimiting literal will be omitted too.

Examples:

* :label="(X.1),*"
* :label="1.,(a),(i)"



* X == parent label, minus prefix and suffix literal content.
* L == similar to X, but only if the immediate parent is a list (not a heading); otherwise, evaluates to the empty string.
* H == similar to X, but only if the immediate parent is a heading

For X, L and H, if the corresponding parent label is unavailable, then it is left out, AND the
joining literal is omitted as well.




## Corner cases and questions

What if list labelling 'skips' a level? Actually, we might decide that it fundamentally cannot; that
all levels must have labels.

Is it likely that someone would want to reverse the order of labels? If so, we could allow a reversed
form of the syntax, though it seems unlikely to be needed.


## Related directives

:label-resume -- continue the numbering from the previous list _at the same level_. (The previous list may be a sibling element, or it may be an 'nth-cousin', sharing any common ancestor element.)

:label-none -- suppresses any label for the current element, and avoids updating the counter.

:label-skip -- skips 1 counter value if the attribute value is non-numeric. If the attr value is an integer, advances the counter by that amount (_on top of_ the one increment that the counter would normally advance anyway). If the attr value is '=' followed by an integer (or an alphabetic count or roman numeral), then the counter value is set to that number.


## Implementation approaches

1. Hard-coded with <span class="la-list-label">. This means the evaluation of actual list labels at compile time.

2. Using CSS properties:
     2a. 'list-style-type' in combination with @counter rules;
     2b. 'list-style-type' with just basic built-in styles.
     2c. CSS classes representing list styles.

3. Using a CSS variable (--la-list-label), in the case that the style overrides the normal CSS list display mechanism. (It can, for instance, use something like 'li::before { content: var(--la-list-label); }'.

* The extension could also, technically do any combination of these at the same time, if there was some need for a fallback, though this is almost certainly unnecessary.

Headings would probably use approach 1 by default (though they could use the others instead, with additional CSS support). Lists would use approach 2 for basic styling, or approach 3 for advanced styling (particularly in combination with m.doc()).



---

Can we write <ol style="display: grid"><li style="display: list-style">...</ol>? And get the best of both worlds?



'''

from lamarkdown.ext.label_support.labellers import Labeller, LabellerFactory
from lamarkdown.ext.label_support.label_templates import LabelTemplateParser

from . import util
import markdown

from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree


LABEL_DIRECTIVE = ':label'

LABELLED_CSS_CLASS = 'la-labelled'
EXPLICIT_LABEL_CSS_CLASS = 'la-label'


class LabelsTreeProcessor(markdown.treeprocessors.Treeprocessor):

    def __init__(self, md, css_fn, h_template, h_level, ol_template, ul_template):
        super().__init__(md)
        self._css_fn = css_fn

        self._parser = LabelTemplateParser()
        self._labeller_factory = LabellerFactory()

        self._h_template = h_template and self._parser.parse(h_template)
        self._h_level = h_level
        self._ol_template = ol_template and self._parser.parse(ol_template)
        self._ul_template = ul_template and self._parser.parse(ul_template)

        self._previous_h_level = -1


    def _find_parent_labeller(self, stack, parent_type) -> Optional[Labeller]:
        for labeller in reversed(stack):
            if labeller.element_type.startswith(parent_type):
                return labeller
        return None


    def run(self, root):

        labeller_stack = []
        heading_indexes = {}
        css_class_n = 0

        disable_list_style_type = False

        def recurse(element):

            if element.tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
                cur_h_level = int(element.tag[1])

                labeller = None
                if cur_h_level in heading_indexes:
                    # A labeller already exists (from a previous sibling heading)
                    labeller = labeller_stack[heading_indexes[cur_h_level]]

                    # If a ':label' directive is provided _as well_, then we replace the current
                    # labeller with a new one.

                    if (new_template_str := element.get(LABEL_DIRECTIVE)) is not None:
                        labeller = self._labeller_factory.get(
                            element_type = element.tag,
                            template = self._parser.parse(new_template_str),
                            parent = labeller.parent
                        )
                        labeller_stack[heading_indexes[cur_h_level]] = labeller

                if labeller is None:
                    # If no labeller exists, first see if there's a ':label' directive
                    template = None
                    if LABEL_DIRECTIVE in element.attrib:
                        template = self._parser.parse(element.get(LABEL_DIRECTIVE))

                    # Failing that, see if a parent heading labeller specifies a child template
                    if template is None and (cur_h_level - 1) in heading_indexes:
                        template = labeller_stack[heading_indexes[cur_h_level - 1]].template.child_template

                    # Failing that, maybe the configuration option is applicable
                    if template is None and cur_h_level == self._h_level:
                        template = self._h_template

                    # TODO: catch LabelTemplateException from self._parser.parse()

                    if template is not None:
                        labeller = self._labeller_factory.get(
                            element.tag,
                            template,
                            parent = self._find_parent_labeller(labeller_stack, template.parent_type)
                        )


                if labeller is not None:
                    labeller.count += 1

                    if self._previous_h_level < cur_h_level:
                        # Starting a new heading level
                        heading_indexes[cur_h_level] = len(labeller_stack)
                        labeller_stack.append(labeller)

                    label_elem = ElementTree.Element('span', **{'class': EXPLICIT_LABEL_CSS_CLASS})
                    label_elem.text = labeller.as_string()
                    label_elem.tail = element.text
                    element.text = ''
                    element.insert(0, label_elem)

                # Note: we don't recurse into heading elements. If you have <h2><ul>...</ul></h2>,
                # you get what you deserve.

                if self._previous_h_level > cur_h_level:
                    # Finishing (at least) one heading level, and continuing with a higher- level
                    # heading.

                    for i in range(self._previous_h_level, cur_h_level, -1):
                        if i in heading_indexes:
                            del labeller_stack[heading_indexes[i]]
                            del heading_indexes[i]

                self._previous_h_level = cur_h_level



            # TODO (future):
            # - number <table><caption>... and <figure><figcaption>...
            # - provide a way to define new numbering series (e.g., listings, equations, etc.)

            # NOTE: There are other types of lists as well: <menu>/<li> and <dd>/<dt>/<dl>, but numbering these is likely a rarefied use case.

            elif element.tag in {'ul', 'ol'}:

                disable_list_style_type = True

                # TODO (future): check for a 'resume' directive, and if found, re-use an existing sibling list labeller.

                # Find the explicit label directive, if any
                # list_template_str = element.get(LABEL_DIRECTIVE)
                template = None
                if LABEL_DIRECTIVE in element.attrib:
                    template = self._parser.parse(element.get(LABEL_DIRECTIVE))

                # Otherwise, see if there's a child label
                # if list_template_str is None and len(labeller_stack) > 0:
                #     if labeller_stack[-1] **represents the same kind of list (h, ul or ol)**:
                #         list_template_str = labeller_stack[-1].child_template_str
                if (template is None and
                    (parent_labeller := self._find_parent_labeller(labeller_stack, element.tag)) is not None
                ):
                    template = parent_labeller.template.child_template

                # Otherwise, maybe the configuration option is applicable (if this is a top-level list)
                if template is None and len(labeller_stack) == 0:
                    template = self._ul_template if element.tag == 'ul' else self._ol_template

                if template is not None:

                    labeller = self._labeller_factory.get(
                        element_type = element.tag,
                        template = template, #self._parser.parse(template_str),
                        parent = self._find_parent_labeller(labeller_stack, template.parent_type)
                    )
                    # TODO: catch LabelTemplateException from self._parser.parse()
                    labeller_stack.append(labeller)

                    if self._css_fn is None:
                        element.set('class', LABELLED_CSS_CLASS)
                    else:
                        # Render CSS logic, if possible
                        li_css_counter = None
                        css_counter = labeller.get_css_counter()
                        element.set('class', f'{LABELLED_CSS_CLASS} {css_counter}')
                        self._css_fn(f'''
                            .{css_counter} {{
                                counter-reset: {css_counter};
                            }}
                            .{css_counter} > li {{
                                counter-increment: {css_counter};
                            }}
                            .{css_counter} > li::before {{
                                content: {labeller.as_css_expr()};
                            }}
                        ''')

                    for li in element:
                        # Lists generally contain just <li> elements, but it doesn't hurt to check.
                        if li.tag == 'li':

                            new_template_str = li.get(LABEL_DIRECTIVE)
                            if new_template_str is not None:
                                # labeller.reset(new_template = self._parse_template(new_template_str))
                                labeller = self._labeller_factory.get(
                                    element_type = element.tag,
                                    template = self._parser.parse(new_template_str),
                                    parent = labeller.parent
                                )
                                labeller_stack[-1] = labeller

                                if self._css_fn is not None:
                                    li_css_counter = labeller.get_css_counter()
                                    css._css_fn(f'''
                                        li.{li_css_counter} {{
                                            counter-increment: {li_css_counter};
                                        }}
                                        li.{li_css_counter}::before {{
                                            content: {labeller.as_css_expr()};
                                        }}
                                    ''')

                                    s = li.get('style')
                                    li.set('style',
                                           ((s + '; ') if s else '')
                                           + f'conter-reset: {li_css_counter}')

                            labeller.count += 1

                            # Render embedded HTML text, if necessary
                            if self._css_fn is None:
                                label_elem = ElementTree.Element('span', **{'class': EXPLICIT_LABEL_CSS_CLASS})
                                label_elem.text = labeller.as_string()
                                label_elem.tail = li.text
                                li.text = ''
                                li.insert(0, label_elem)

                            elif li_css_counter is not None:
                                li.set('class', li_css_counter)

                            for child in li:
                                recurse(child)



                    labeller_stack.pop()

                else:
                    # We're not styling this list, but we must recurse to find other elements.
                    for child in element:
                        recurse(child)

            else:
                for child in element:
                    recurse(child)
        # end-def

        recurse(root)

        if disable_list_style_type:
            self._css_fn(f'''
                .la-label > li {{
                    list-style-type: none;
                }}
            ''')

        return root


LABEL_DEFAULT = 'default'

class LabelsExtension(markdown.Extension):
    def __init__(self, **kwargs):
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass # Use default defaults

        self.config = {
            'css_fn': [
                lamarkdown.css if p else None,
                'Callback function accepting CSS code via a string parameter. This enables CSS-based numbering (for <ol> elements). This may be "None", in which case list labels will be computed at compile-time and embedded in the HTML as plain text.'
            ],

            'h_labels': [
                LABEL_DEFAULT, #'H.1 ,*',
                'Default heading template, to be applied at heading level "h_level".'
            ],

            'h_level': [
                1,
                'Heading level at which to apply the default heading labels ("h_labels").'
            ],

            'ol_labels': [
                LABEL_DEFAULT, #'1.,(a)',
                'Default ordered list template, to be applied starting at the top-most ordered list level.'
            ],

            'ul_labels': [
                LABEL_DEFAULT, #'▪,•,◦,*',
                'Default unordered list template, to be applied starting at the top-most unordered list level.'
            ]
        }
        super().__init__(**kwargs)


    def extendMarkdown(self, md):
        # Note: it may be wise to load the la.attr_prefix extension alongside this one, because it
        # provides a convenient way to apply ':label' directives to lists. However, attr_prefix
        # isn't loaded automatically here, because this extension might still be useful without it.

        h_template = self.getConfig('h_labels')
        ul_template = self.getConfig('ul_labels')
        ol_template = self.getConfig('ol_labels')

        proc = LabelsTreeProcessor(
            md,
            css_fn      = self.getConfig('css_fn'),
            h_template  = None if h_template == LABEL_DEFAULT else h_template,
            h_level     = self.getConfig('h_level'),
            ul_template = None if ul_template == LABEL_DEFAULT else ul_template,
            ol_template = None if ol_template == LABEL_DEFAULT else ol_template,
        )

        md.treeprocessors.register(proc, 'la-labels-tree', 15) # low priority?



def makeExtension(**kwargs):
    return LabelsExtension(**kwargs)

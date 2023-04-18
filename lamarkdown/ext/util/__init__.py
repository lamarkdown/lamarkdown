import markdown
import markdown.extensions.attr_list
import re
from xml.etree import ElementTree

# ATTR = r'''
#     \{\:?[ ]*               # Starts with '{' or '{:' (with optional spaces)
#     (?P<attr>
#         [^\}\n ][^\}\n]*    # No '}' or newlines, and at least one non-space char.
#     )?
#     [ ]*\}                  # Ends with '}' (with optional spaces)
# '''

ATTR = r'''
    \{\:?[ ]*               # Starts with '{' or '{:' (with optional spaces)
    (?P<attr>
        (?![\s\}])          # First character must not be a space or closing brace
        (
            \\[{}\\]        # Consists of {, } and \ escapes, and
            |
            [^\{\}\n]       # Non-brace, non-newline characters.
        )*
    )?
    [ ]*\}                  # Ends with '}' (with optional spaces)
'''


def set_attributes(element, attrs):
    if isinstance(attrs, re.Match):
        attrs = attrs.group('attr')

    if attrs is not None:
        attrs = attrs.replace(r'\{', '{').replace(r'\}', '}').replace('\\\\', '\\')
        # Hijack parts of the attr_list extension to handle the attribute list.
        #
        # (Warning: there is a risk here that a future version of Markdown will change
        # the design of attr_list, such that this call doesn't work anymore. For now, it
        # seems the easiest and most consistent way to go.)
        markdown.extensions.attr_list.AttrListTreeprocessor().assign_attrs(element, attrs)


def strip_namespaces(element: ElementTree.Element):
    '''Recursively removes {...}-style namespace info from both tags and attributes.'''
    if element.tag.startswith('{'):
        element.tag = element.tag.split('}', 1)[1]

    key_set = set(element.attrib.keys())
    for key in key_set:
        if key.startswith('{'):
            element.attrib[key.split('}', 1)[1]] = element.attrib[key]
            del element.attrib[key]

    for subelement in element:
        strip_namespaces(subelement)


def opaque_tree(element: ElementTree.Element):
    '''Recursively replaces all the text in a subtree with AtomicStrings.'''
    if element.text:
        element.text = markdown.util.AtomicString(element.text)
    for subelement in element:
        opaque_tree(subelement)
        if subelement.tail:
            subelement.tail = markdown.util.AtomicString(subelement.tail)

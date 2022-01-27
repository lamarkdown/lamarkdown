'''
Utility module that creates HTML elements representing error messages, to be embedded in the output
document.
'''
from markdown.util import AtomicString
import html
import traceback
from xml.etree import ElementTree


PANEL_STYLE = 'border: 2px dashed yellow; background: #800000; padding: 1ex;'
TITLE_STYLE = 'font-weight: bold; color: white;'
WHERE_STYLE = 'color: yellow;'
DETAILS_STYLE = ''

MAX_ROWS = 50
MAX_COLS = 110

def with_message(where: str, title: str, *details_list: list[str]) -> ElementTree.Element:
    panel_elem = ElementTree.Element('form', style = PANEL_STYLE)
    title_elem = ElementTree.SubElement(panel_elem, 'div', style = TITLE_STYLE)
    where_elem = ElementTree.SubElement(title_elem, 'span', style = WHERE_STYLE)

    where_elem.text = AtomicString(html.escape(f'[{where}]'))
    where_elem.tail = AtomicString(html.escape(f' {title}'))

    if details_list:
        cols = str(max(10, min(MAX_COLS,
            max(len(line) for details in details_list for line in details.splitlines())
        )))

        for details in details_list:
            details_elem = ElementTree.SubElement(panel_elem,
                'textarea',
                style = DETAILS_STYLE,
                rows = str(details.count('\n') + 1),
                cols = cols,
                readonly = ''
            )
            details_elem.text = AtomicString(html.escape(details))

    return panel_elem


def from_exception(where: str, e: Exception, *details_list: list[str]) -> ElementTree.Element:
    return with_message(where, str(e), ''.join(traceback.format_exc()), *details_list)

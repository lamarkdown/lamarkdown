'''
The Error class represents errors occurring during compilation. These are incorporated into the
HTML document (for visibility) and/or output to the console.
'''
from markdown.util import AtomicString
import html
import traceback
from xml.etree import ElementTree


PANEL_STYLE = 'border: 2px dashed yellow; background: #800000; padding: 1ex;'
TITLE_STYLE = 'font-weight: bold; color: white;'
WHERE_STYLE = 'color: yellow;'
DETAILS_STYLE = ''

MAX_ROWS = 30
MAX_COLS = 110

CONSOLE_WHERE = '\033[33;1m'
CONSOLE_TITLE = '\033[37;1m'
CONSOLE_RESET = '\033[0m'

class Error:
    def __init__(self, where: str, title: str, *details_list: str):
        self._where = where
        self._title = title
        self._details_list = details_list


    @staticmethod
    def from_exception(where: str, e: Exception, *details_list: str) -> 'Error':
        return Error(where, str(e), ''.join(traceback.format_exc()), *details_list)


    def to_element(self) -> ElementTree.Element:
        panel_elem = ElementTree.Element('form', style = PANEL_STYLE)
        title_elem = ElementTree.SubElement(panel_elem, 'div', style = TITLE_STYLE)
        where_elem = ElementTree.SubElement(title_elem, 'span', style = WHERE_STYLE)

        where_elem.text = AtomicString(f'[{self._where}]')
        where_elem.tail = AtomicString(f' {self._title}')

        if self._details_list:
            cols = str(max(10, min(MAX_COLS,
                max(len(line) for details in self._details_list for line in details.splitlines())
            )))

            for details in self._details_list:
                details_elem = ElementTree.SubElement(panel_elem,
                    'textarea',
                    style = DETAILS_STYLE,
                    rows = str(max(1, min(MAX_ROWS, details.count('\n') + 1))),
                    cols = cols,
                    readonly = ''
                )
                details_elem.text = AtomicString(details)

        return panel_elem


    def to_html(self) -> str:
        return ElementTree.tostring(self.to_element(), encoding = 'unicode')


    def print(self):
        print(f'{CONSOLE_WHERE}[{self._where}]{CONSOLE_RESET} {CONSOLE_TITLE}{self._title}{CONSOLE_RESET}')
        for details in self._details_list:
            print('--')
            print(details.strip())
        if self._details_list:
            print('--')

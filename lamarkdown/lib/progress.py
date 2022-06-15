'''
'''
from markdown.util import AtomicString
import html
import textwrap
import traceback
from xml.etree import ElementTree

RESET = '\033[0m'

class Message:
    def __init__(self, location: str, msg: str, *details_list: str):
        self._location = location
        self._msg = msg
        self._details_list = details_list

    def print(self):
        print(f'{self.LOCATION_COLOUR}{self.TAG}{self._location}:{RESET} {self.MSG_COLOUR}{self._msg}{RESET}')

        for details in self._details_list:
            if details[-1] == '\n':
                details = details[:-1]
            print(textwrap.indent(details, '  | ', lambda line: True))
            print('  ---')

class ProgressMsg(Message):
    LOCATION_COLOUR = '\033[35m'
    MSG_COLOUR = '\033[35m'
    TAG = ''

class WarningMsg(Message):
    LOCATION_COLOUR = '\033[33;1m'
    MSG_COLOUR = '\033[37;1m'
    TAG = '[!] '

class ErrorMsg(Message):
    LOCATION_COLOUR = '\033[31;1m'
    MSG_COLOUR = '\033[37;1m'
    TAG = '[!!] '

    PANEL_STYLE = 'border: 2px dashed yellow; background: #800000; padding: 1ex;'
    MSG_STYLE = 'font-weight: bold; color: white;'
    LOCATION_STYLE = 'color: yellow;'
    DETAILS_STYLE = 'max-width: calc(100% - 1ex);'

    MAX_ROWS = 30
    MAX_COLS = 110

    def __init__(self, *args):
        super().__init__(*args)
        self._consumed = False

    @property
    def consumed(self):
        return self._consumed


    def as_dom_element(self) -> ElementTree.Element:
        panel_elem = ElementTree.Element('form', style = self.PANEL_STYLE)
        msg_elem = ElementTree.SubElement(panel_elem, 'div', style = self.MSG_STYLE)
        location_elem = ElementTree.SubElement(msg_elem, 'span', style = self.LOCATION_STYLE)

        location_elem.text = AtomicString(f'[!!] {self._location}:')
        location_elem.tail = AtomicString(f' {self._msg}')

        if self._details_list:
            cols = str(max(10, min(self.MAX_COLS,
                max(len(line) for details in self._details_list for line in details.splitlines())
            )))

            for details in self._details_list:
                details_elem = ElementTree.SubElement(panel_elem,
                    'textarea',
                    style = self.DETAILS_STYLE,
                    rows = str(max(1, min(self.MAX_ROWS, details.count('\n') + 1))),
                    cols = cols,
                    readonly = ''
                )
                details_elem.text = AtomicString(details)

        self._consumed = True
        return panel_elem


    def as_html_str(self) -> str:
        self._consumed = True
        return ElementTree.tostring(self.as_dom_element(), encoding = 'unicode')



class Progress:
    def __init__(self):
        self._errors = []

    def show(self, msg: Message, skip = 0):
        for _ in range(skip):
            print()
        msg.print()
        if isinstance(msg, ErrorMsg):
            self._errors.append(msg)
        return msg

    def progress(self, *args, **kwargs):
        return self.show(ProgressMsg(*args), **kwargs)

    def warning(self, *args, **kwargs):
        return self.show(WarningMsg(*args), **kwargs)

    def error(self, *args, **kwargs):
        return self.show(ErrorMsg(*args), **kwargs)

    def error_from_exception(self, location: str, e: Exception, *details_list: str, **kwargs):
        return self.show(ErrorMsg(location, str(e), ''.join(traceback.format_exc()), *details_list), **kwargs)

    def get_errors(self):
        return list(self._errors)

    def clear_errors(self):
        self._errors.clear()


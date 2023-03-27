'''
'''
from markdown.util import AtomicString
import html
import shutil
import traceback
from xml.etree import ElementTree

RESET = '\033[0m'


def wrap(text, width):
    if text == '':
        yield ''
    while text:
        newline_index = text.find('\n')
        if newline_index != -1 and newline_index <= width:
            yield text[:newline_index]
            text = text[newline_index + 1:]
        else:
            yield text[:width]
            text = text[width:]


class Message:
    def __init__(self, location: str, msg: str, *details_list: str):
        self._location = location
        self._msg = msg
        self._details_list = details_list

    def print(self):
        print(f'{self.LOCATION_COLOUR}{self.TAG}{self._location}:{RESET} {self.MSG_COLOUR}{self._msg}{RESET}')

        terminal_width = shutil.get_terminal_size(fallback = (80, 40)).columns
        text_width = terminal_width - 6

        first = True
        for details in self._details_list:
            if details:
                assert isinstance(details, str)
                if first:
                    print('  ┌─' + ('─' * text_width) + '─┐')
                    first = False
                else:
                    print('  ├─' + ('─' * text_width) + '─┤')

                for line in wrap(details.rstrip(), text_width):
                    print('  │ ' + line + (' ' * (text_width - len(line))) + ' │')

        if not first:
            print('  └─' + ('─' * text_width) + '─┘')


class ProgressMsg(Message):
    LOCATION_COLOUR = '\033[32m'
    MSG_COLOUR = ''
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

    def as_comment(self) -> str:
        # Do not mark as consumed, because the user may not see it; this is mainly to assist
        # in unit test output.
        return f'/* [!!] {self._location}: {self._msg}\n{self._details_list} */'



class Progress:
    def __init__(self, show_cache_hits = False):
        self._errors = []
        self._show_cache_hits = show_cache_hits

    def show(self, msg: Message, skip = 0):
        for _ in range(skip):
            print()
        msg.print()
        if isinstance(msg, ErrorMsg):
            self._errors.append(msg)
        return msg

    def progress(self, *args, **kwargs):
        return self.show(ProgressMsg(*args), **kwargs)

    def cache_hit(self, location: str, resource: str = None):
        obj = ProgressMsg(location,
                          'Using cached value' + (f' for {resource}' if resource else ''))
        return self.show(obj) if self._show_cache_hits else obj

    def warning(self, *args, **kwargs):
        return self.show(WarningMsg(*args), **kwargs)

    def error(self, *args, **kwargs):
        return self.show(ErrorMsg(*args), **kwargs)

    def error_from_exception(self, location: str, e: Exception, *details_list: str, msg = None, **kwargs):
        return self.show(
            ErrorMsg(location,
                     f'{msg}: {str(e)}' if msg else str(e),
                     ''.join(traceback.format_exc()),
                     *details_list
            ),
            **kwargs
        )

    def get_errors(self):
        return list(self._errors)

    def clear_errors(self):
        self._errors.clear()


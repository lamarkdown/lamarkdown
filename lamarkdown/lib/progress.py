'''
'''
from markdown.util import AtomicString

from dataclasses import dataclass, field
import html
import shutil
import traceback
from xml.etree import ElementTree
from typing import List, Set


RESET = '\033[0m'

LINE_NUMBER_COLOUR = '\033[30;1m'
LINE_NUMBER_WIDTH = 4

HIGHLIGHT_COLOUR = '\033[43;30m'


def wrap(text, width):
    line_number = 1
    start_of_line = True

    if text == '':
        yield (1, '')
    while text:
        newline_index = text.find('\n')
        if newline_index != -1 and newline_index <= width:
            yield (line_number, start_of_line, text[:newline_index])
            text = text[newline_index + 1:]
            start_of_line = True
            line_number += 1
        else:
            yield (line_number, start_of_line, text[:width])
            text = text[width:]
            start_of_line = False


@dataclass
class Details:
    title: str
    content: str
    show_line_numbers: bool = False
    context_lines: int = None
    highlight_lines: Set[int] = field(default_factory = set)


class Message:
    def __init__(self, location: str, msg: str, *details_list: List[Details]):
        self._location = location
        self._msg = msg
        self._details_list = details_list

    def print(self):
        print(f'{self.LOCATION_COLOUR}{self.TAG}{self._location}:{RESET} {self.MSG_COLOUR}{self._msg}{RESET}')

        terminal_width = shutil.get_terminal_size(fallback = (80, 40)).columns
        inner_width = terminal_width - 6

        first = True
        for details in self._details_list:
            if first:
                print(f'  ┌─{"─" * inner_width}─┐')
                first = False
            else:
                print(f'  ├─{"─" * inner_width}─┤')

            if details.show_line_numbers:
                text_width = inner_width - LINE_NUMBER_WIDTH - 1

                for line_number, start_of_line, line in wrap(details.content.rstrip(), text_width):
                    if (details.context_lines is not None and
                        details.highlight_lines and
                        all(abs(line_number - hl) > details.context_lines
                            for hl in details.highlight_lines)):
                        continue

                    n_str = str(line_number).rjust(LINE_NUMBER_WIDTH) if start_of_line else (' ' * LINE_NUMBER_WIDTH)
                    hl_str = HIGHLIGHT_COLOUR if line_number in details.highlight_lines else ""
                    print(f'  │{LINE_NUMBER_COLOUR}{n_str}{RESET}  {hl_str}{line}{" " * (text_width - len(line))}{RESET} │')

            else:
                for _, _, line in wrap(details.content.rstrip(), inner_width):
                    print(f'  │ {line}{" " * (inner_width - len(line))} │')

        if not first:
            print(f'  └─{"─" * inner_width}─┘')


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
                max(len(line) for details in self._details_list for line in details.content.splitlines())
            )))

            for details in self._details_list:
                details_elem = ElementTree.SubElement(panel_elem,
                    'textarea',
                    style = self.DETAILS_STYLE,
                    rows = str(max(1, min(self.MAX_ROWS, details.content.count('\n') + 1))),
                    cols = cols,
                    readonly = ''
                )
                details_elem.text = AtomicString(details.content)

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


    def show(self, msg: Message):
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


    def error(self, location, *, msg = None, exception = None, show_traceback = True,
              output = None, code = None, highlight_lines = set(), context_lines = 6):
        details = []
        if exception:
            msg = f'{msg}: {str(exception)}' if msg else str(exception)
            if show_traceback:
                details.append(Details('Traceback', ''.join(traceback.format_exc())))

        elif not msg:
            msg = 'error'

        if output:
            details.append(Details('Output', output))

        if code:
            if exception and highlight_lines == set():
                highlight_lines = {traceback.extract_tb(exception.__traceback__)[-1].lineno}

            details.append(Details('Code',
                                   code,
                                   show_line_numbers = True,
                                   highlight_lines = highlight_lines or set(),
                                   context_lines = context_lines))

        return self.show(ErrorMsg(location, msg, *details))


    def get_errors(self):
        return list(self._errors)


    def clear_errors(self):
        self._errors.clear()


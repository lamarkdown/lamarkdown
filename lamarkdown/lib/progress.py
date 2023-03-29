'''
Logging/error handling infrastructure.
'''

from markdown.util import AtomicString

from dataclasses import dataclass, field
import html
import io
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
    def __init__(self, location: str, msg: str, details_list: List[Details] = []):
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

    PANEL_STYLE = r'''
        background: repeating-linear-gradient(-45deg,#c44,#c44 25px,#b33 25px,#b33 50px);
        padding: 0.5em;
        border-radius: 2mm;
    '''

    MSG_STYLE = r'''
        font-weight: bold;
        color: white;
        text-shadow: 1px 1px 2px black;
    '''

    LOCATION_STYLE = 'color: yellow;'

    LISTING_STYLE = r'''
        background: rgba(255, 255, 255, 0.7);
        color: black;
        padding: 0.5em;
        overflow: scroll;
        font-family: monospace;
        margin: 0.5em 0 0 0;
    '''

    GRID_LISTING_STYLE = r'''
        margin: 0.5em 0 0 0;
        background: rgba(255, 255, 255, 0.7);
        color: black;
        padding: 0.5em;
        overflow: scroll;
        font-family: monospace;
        display: grid;
        grid-template-columns: 0fr 1fr;
        white-space: pre;
    '''

    LINE_NUMBER_STYLE = r'''
        grid-column: 1;
        color: green;
        font-size: smaller;
        user-select: none;
        text-align: right;
        width: 3em;
        margin: 0 1em 0 0;
    '''

    LINE_STYLE = r'''
        grid-column: 2;
        margin: 0
    '''

    HIGHLIGHT_STYLE = r'''
        background: yellow;
    '''

    def __init__(self, *args):
        super().__init__(*args)
        self._consumed = False

    @property
    def consumed(self):
        return self._consumed


    def as_html_str(self) -> str:

        buf = io.StringIO()
        buf.write(f'''
            <details style="{self.PANEL_STYLE}">\
            <summary style="{self.MSG_STYLE}"><span style="{self.LOCATION_STYLE}">[!!] {self._location}:</span>
            {self._msg}</summary>''')

        for details in self._details_list:

            if details.show_line_numbers:
                buf.write(f'<div style="{self.GRID_LISTING_STYLE}">')

                for line_number, line in enumerate(details.content.rstrip().splitlines(), start = 1):
                    if (details.context_lines is not None and
                        details.highlight_lines and
                        all(abs(line_number - hl) > details.context_lines
                            for hl in details.highlight_lines)):
                        continue

                    hl_str = ('; ' + self.HIGHLIGHT_STYLE) if line_number in details.highlight_lines else ''
                    buf.write(f'<div style="{self.LINE_NUMBER_STYLE}">{line_number}</div>')
                    buf.write(f'<div style="{self.LINE_STYLE}{hl_str}">{line}</div>')

                buf.write('</div>')
                buf.write(r'''
                    <script>
                        document.getElementById(
                    </script>
                ''')

            else:
                buf.write(f'<pre style="{self.LISTING_STYLE}">{details.content}</pre>')

        buf.write('</details>')

        self._consumed = True
        return buf.getvalue()


    def as_dom_element(self) -> ElementTree.Element:
        elem = ElementTree.fromstring(self.as_html_str())

        if elem.text: elem.text = AtomicString(elem.text)
        for sub_elem in elem.iter():
            if sub_elem.text: sub_elem.text = AtomicString(sub_elem.text)
            if sub_elem.tail: sub_elem.tail = AtomicString(sub_elem.tail)

        return elem


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


    def progress(self, location, *, msg, advice = None):
        details_list = []
        if advice:
            details_list.append(Details('Advice', advice))
        return self.show(ProgressMsg(location, msg, details_list))


    def cache_hit(self, location: str, resource: str = None):
        obj = ProgressMsg(location,
                          'Using cached value' + (f' for {resource}' if resource else ''))
        return self.show(obj) if self._show_cache_hits else obj


    def warning(self, location, *, msg):
        return self.show(WarningMsg(*args), **kwargs)


    def error(self, location, *, msg = None, exception = None, show_traceback = True,
              output = None, code = None, highlight_lines = set(), context_lines = 6):
        details_list = []
        if exception:
            msg = f'{msg}: {str(exception)} ({exception.__class__.__name__})' if msg else str(exception)
            if show_traceback:
                details_list.append(Details('Traceback', ''.join(traceback.format_exc())))

        elif not msg:
            msg = 'error'

        if output:
            details_list.append(Details('Output', output))

        if code:
            if exception and highlight_lines == set():
                highlight_lines = {traceback.extract_tb(exception.__traceback__)[-1].lineno}

            details_list.append(Details('Code',
                                   code,
                                   show_line_numbers = True,
                                   highlight_lines = highlight_lines or set(),
                                   context_lines = context_lines))

        return self.show(ErrorMsg(location, msg, details_list))


    def get_errors(self):
        return list(self._errors)


    def clear_errors(self):
        self._errors.clear()


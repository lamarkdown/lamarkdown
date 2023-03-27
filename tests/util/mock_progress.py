import traceback
import xml.etree.ElementTree

class MockProgressException(Exception):
    pass

class MockMsg:
    def as_dom_element(self, *a, **l):
        return xml.etree.ElementTree.Element('mock msg')

    def as_html_str(self, *a, **l):
        return '<mock msg>'

class MockProgress:
    def __init__(self, expect_error: bool = False):
        self._expect_error = expect_error
        self._received_error = False

    def progress(self, *a, **k): return MockMsg()
    def cache_hit(self, *a, **k): return MockMsg()
    def warning(self, *a, **k):  return MockMsg()
    def error(self, location, msg, *a, **k):
        if self._expect_error:
            self._received_error = True
            return MockMsg()
        else:
            print(f'[!!] {location}: {msg}\n---\n{a}\n---\n{k}\n---')
            raise MockProgressException(f'{location}: {msg}')

    def error_from_exception(self, location, ex, *a, **k):
        if self._expect_error:
            self._received_error = True
            return MockMsg()
        else:
            print(f'[!!] {location}\n---')
            traceback.print_exc()
            print(f'---\n{a}\n---\n{k}\n---')
            raise MockProgressException(f'{location}: {ex}') from ex

    def get_errors(self, *a, **k): return []

    def __eq__(self, other):
        return isinstance(other, MockProgress)

    # Utility for test code
    @property
    def received_error(self):
        return self._received_error

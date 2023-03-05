import traceback
import xml.etree.ElementTree

class MockProgressException(Exception):
    pass

class MockMsg:
    def as_dom_element(self, *a, **l):
        return xml.etree.ElementTree.Element('mock')

class MockProgress:
    def __init__(self, expect_error: bool = False):
        self.expect_error = expect_error

    def progress(self, *a, **k): return MockMsg()
    def warning(self, *a, **k):  return MockMsg()
    def error(self, location, msg, *a, **k):
        if not self.expect_error:
            print(f'[!!] {location}: {msg}\n---\n{a}\n---\n{k}\n---')
            raise MockProgressException(f'{location}: {msg}')
        else:
            return MockMsg()

    def error_from_exception(self, location, ex, *a, **k):
        if not self.expect_error:
            print(f'[!!] {location}\n---')
            traceback.print_exc()
            print(f'---\n{a}\n---\n{k}\n---')
            raise MockProgressException(f'{location}: {ex}') from ex
        else:
            return MockMsg()

    def get_errors(self, *a, **k): return []

    def __eq__(self, other):
        return isinstance(other, MockProgress)

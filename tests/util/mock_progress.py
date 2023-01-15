import xml.etree.ElementTree

class MockProgressException(Exception):
    pass

class MockMsg:
    def as_dom_element(self, *a, **l):
        return xml.etree.ElementTree.Element('mock')

class MockProgress:
    def progress(self, *a, **k):             return MockMsg()
    def warning(self, *a, **k):              return MockMsg()
    def error(self, location, msg, *a, **k):
        raise MockProgressException(f'{location}: {msg}')

    def error_from_exception(self, location, ex, *a, **k):
        raise MockProgressException(f'{location}: {ex}') from ex

    def get_errors(self, *a, **k):           return []

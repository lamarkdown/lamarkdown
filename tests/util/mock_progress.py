import xml.etree.ElementTree

class MockMsg:
    def as_dom_element(self, *a, **l):
        return xml.etree.ElementTree.Element('mock')

class MockProgress:
    def progress(self, *a, **k):             return MockMsg()
    def warning(self, *a, **k):              return MockMsg()
    def error(self, *a, **k):                return MockMsg()
    def error_from_exception(self, *a, **k): return MockMsg()
    def get_errors(self, *a, **k):           return []

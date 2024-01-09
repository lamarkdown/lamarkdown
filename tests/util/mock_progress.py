import traceback
import xml.etree.ElementTree


class MockProgressException(Exception):
    pass


class MockMsg:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def as_dom_element(self, *a, **_l):
        return xml.etree.ElementTree.Element('mock msg')

    def as_html_str(self, *a, **_l):
        return '<mock msg>'

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class MockProgress:
    def __init__(self, expect_error: bool = False):
        self._expect_error = expect_error
        self.progress_messages = []
        self.cache_messages = []
        self.warning_messages = []
        self.error_messages = []

    def progress(self, location, *, msg, advice=None):
        assert isinstance(location, str) and location != ''
        assert isinstance(msg, str) and msg != ''
        assert advice is None or (isinstance(advice, str) and advice != '')

        self.progress_messages.append(m := MockMsg(location=location, msg=msg, advice=advice))
        return m

    def cache_hit(self, location, *, resource=None):
        assert isinstance(location, str) and location != ''
        assert resource is None or (isinstance(resource, str) and resource != '')

        self.cache_messages.append(m := MockMsg(location=location, resource=resource))
        return m

    def warning(self, location, *, msg):
        assert isinstance(location, str) and location != ''
        assert isinstance(msg, str) and msg != ''

        self.warning_messages.append(m := MockMsg(location=location, msg=msg))
        return m

    def error(self, location, *, msg=None, exception=None, show_traceback=False,
              output=None, code=None, highlight_lines=None, context_lines=None):

        assert isinstance(location, str) and location != ''
        assert msg is None or (isinstance(msg, str) and msg != '')
        assert exception is None or isinstance(exception, Exception)
        assert isinstance(show_traceback, bool)
        assert output is None or isinstance(output, str)
        assert code is None or isinstance(code, str)
        assert highlight_lines is None or isinstance(highlight_lines, set)
        assert context_lines is None or (isinstance(context_lines, int) and context_lines >= 0)

        if self._expect_error:
            self.error_messages.append(m := MockMsg(
                location=location, msg=msg, exception=exception,
                show_traceback=show_traceback, output=output, code=code,
                highlight_lines=highlight_lines, context_lines=context_lines))
            return m

        else:
            print(f'[!!] {location}: {msg}: {exception}')
            if exception:
                print(''.join(traceback.format_exc()))
            if output:
                print('--- output ---')
                print(output)
            if code:
                print('--- code ---')
                print(code)
            raise MockProgressException(f'{location}: {msg}: {exception}')

    def get_errors(self, *a, **k):
        return []

    def __eq__(self, other):
        return isinstance(other, MockProgress)

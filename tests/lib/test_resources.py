from ..util.mock_progress import MockProgress
from lamarkdown.lib import resources

import unittest
from unittest.mock import patch, Mock, PropertyMock

import email.utils
import io
import os
import tempfile
from textwrap import dedent
from xml.etree import ElementTree

import subprocess

class ResourcesTestCase(unittest.TestCase):

    def test_read_url(self):

        progress = MockProgress(expect_error = True)
        cache = Mock()

        # 1. Read a relative URL, which ought to become a local file read.
        with tempfile.TemporaryDirectory() as dir:
            os.chdir(dir)
            with open('testfile.txt', 'w') as w:
                w.write('test content')

            os.mkdir('testdir')
            with open(os.path.join('testdir', 'testfile2.md'), 'w') as w:
                w.write('test content 2')

            for url,                           expected in [
                ('testfile.txt',              (False, b'test content', 'text/plain')),
                ('file:testfile.txt',         (False, b'test content', 'text/plain')),
                ('testdir/testfile2.md',      (False, b'test content 2', 'text/markdown')),
                ('file:testdir/testfile2.md', (False, b'test content 2', 'text/markdown')),
            ]:
                output = resources.read_url(url, cache, progress)
                self.assertEqual(expected, output)


        # 2. Read a cached remote URL.
        with patch('urllib.request.urlopen') as mock_urlopen,\
             patch('builtins.open') as mock_open:

            cached_url = 'http://cached.example.com/file.txt'
            cache.get.side_effect = \
                lambda key: {cached_url: ('cached_content', 'text/mock')}.get(key)

            result = resources.read_url(cached_url, cache, progress)
            mock_urlopen.assert_not_called()
            mock_open   .assert_not_called()
            self.assertEqual((True, 'cached_content', 'text/mock'), result)


        # 3. Read a URL that ought to provoke network access (though patched here), with results
        #    affected by the server return status and the 'cache-control' and 'date' headers.
        url = 'http://example.com/file.txt'
        content = b'mock_remote_content'
        mime = 'text/plain'
        mock_time = 1_000_000_000
        fd = email.utils.formatdate

        for status, headers,                             exp_result,            exp_cache_time in [
            (200,   {},                                  (True, content, mime), 86400),
            (500,   {},                                  (True, b'',     None), None),
            (200,   {'cache-control':
                     'aa,no-cache,bb'},                  (True, content, mime), None),
            (200,   {'cache-control':
                     'aa,no-store,bb'},                  (True, content, mime), None),
            (200,   {'cache-control':
                     'aa,max-age=-1,bb'},                (True, content, mime), None),
            (200,   {'cache-control':
                     'aa,max-age=0,bb'},                 (True, content, mime), None),

            (200,   {'cache-control':
                       'aa,max-age=1,bb'},               (True, content, mime), 1),
            (200,   {'cache-control':
                       'aa,no-store,max-age=1,bb'},      (True, content, mime), None),

            (200,   {'cache-control': 'aa,max-age=1,bb',
                     'date': fd(mock_time)},             (True, content, mime), 1),

            (200,   {'cache-control': 'aa,max-age=3,bb',
                     'date': fd(mock_time - 1)},         (True, content, mime), 2),

            (200,   {'cache-control': 'aa,max-age=3,bb',
                     'date': fd(mock_time - 3)},         (True, content, mime), None),
        ]:
            conn = Mock()
            conn.read.return_value = content
            type(conn).status = PropertyMock(return_value = status)
            type(conn).headers = PropertyMock(return_value = headers)

            cache.reset_mock()

            with patch('urllib.request.urlopen') as mock_urlopen,\
                 patch('time.time', lambda: mock_time):

                mock_urlopen.return_value.__enter__.return_value = conn

                result = resources.read_url(url, cache, progress)
                self.assertEqual(exp_result, result)

                # Caching
                if exp_cache_time is None:
                    cache.set.assert_not_called()
                else:
                    cache.set.assert_called_with(url, (content, mime), expire = exp_cache_time)



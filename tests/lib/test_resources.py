from ..util.mock_progress import MockProgress
from lamarkdown.lib import resources

import unittest
from unittest.mock import patch, Mock, PropertyMock

import email.utils
import io
from textwrap import dedent
from xml.etree import ElementTree

class ResourcesTestCase(unittest.TestCase):

    def test_embed_stylesheet_resources(self):
        mock_url = 'data:mock'

        inputs = [
            '',
            'url(http://example.com/image.jpg)',
            'url("http://example.com/image.jpg")',
            'src("http://example.com/image.jpg")',
            'url(  "http://example.com/image.jpg"   )',
            '@import"http://example.com/image.jpg";',
            '@import  "http://example.com/image.jpg"   ;',
            '@import url("http://example.com/image.jpg");',
            r'''p{ x: "url(abc)"; /* url(def) */ y: url("ghi"); z: "url(jkl)"} /* url(mno) */''',
            r'''p{ x: url(abc) url(def); /*y: "url(ghi)";*/ z: url(jkl)}''',
        ]

        expected_urls = [
            [],
            ['http://example.com/image.jpg'],
            ['http://example.com/image.jpg'],
            ['http://example.com/image.jpg'],
            ['http://example.com/image.jpg'],
            ['http://example.com/image.jpg'],
            ['http://example.com/image.jpg'],
            ['http://example.com/image.jpg'],
            ['ghi'],
            ['abc', 'def', 'jkl'],
        ]

        expected_results = [
            '',
            f'url({mock_url})',
            f'url({mock_url})',
            f'url({mock_url})',
            f'url({mock_url})',
            f'@import "{mock_url}";',
            f'@import "{mock_url}"   ;',
            f'@import url({mock_url});',
            rf'''p{{ x: "url(abc)"; /* url(def) */ y: url({mock_url}); z: "url(jkl)"}} /* url(mno) */''',
            rf'''p{{ x: url({mock_url}) url({mock_url}); /*y: "url(ghi)";*/ z: url({mock_url})}}''',
        ]

        for inp, exp_url_list, exp_result in zip(inputs, expected_urls, expected_results):
            with patch('lamarkdown.lib.resources.make_data_url') as mock_make_data_url:
                mock_make_data_url.return_value = mock_url

                result = resources.embed_stylesheet_resources(inp, '', None, None)

                # Ensure that make_data_url() is called correctly.
                self.assertEqual(len(exp_url_list), mock_make_data_url.call_count)
                for url in exp_url_list:
                    mock_make_data_url.assert_any_call(url, '', None, None, None)

                # Check overall result.
                self.assertEqual(exp_result, result)


    def test_embed_media(self):
        mock_url = 'data:mock'

        with patch('lamarkdown.lib.resources.make_data_url') as mock_make_data_url:
            mock_make_data_url.return_value = mock_url

            root = ElementTree.Element('div')
            p = ElementTree.SubElement(root, 'p')

            # Elements that should be embedded
            img1    = ElementTree.SubElement(p, 'img',    src = 'http://example.com/image.jpg',
                                                          type = 'image/jpeg')
            source1 = ElementTree.SubElement(p, 'source', src = 'http://example.com/image2.jpg')
            audio1  = ElementTree.SubElement(p, 'audio',  src = 'http://example.com/audio.mp3',
                                                          type = 'audio/mp3')
            video1  = ElementTree.SubElement(p, 'video',  src = 'http://example.com/video.mp4')
            track1  = ElementTree.SubElement(p, 'track',  src = 'http://example.com/track.vtt',
                                                          other = 'abc')

            # Elements that should remain unchanged (because they're already embedded, or not a
            # type of element subject to being embedded.
            img2    = ElementTree.SubElement(p, 'img',    src = 'data:image/jpeg;base64,abc')
            source2 = ElementTree.SubElement(p, 'source', src = 'data:;base64,def')
            audio2  = ElementTree.SubElement(p, 'audio',  src = 'data:audio/mp3,abc')
            video2  = ElementTree.SubElement(p, 'video',  src = 'data:,def')
            track2  = ElementTree.SubElement(p, 'track',  src = '#fragment')
            div     = ElementTree.SubElement(p, 'div',    src = 'http://example.com/div')
            span    = ElementTree.SubElement(p, 'div',    src = 'http://example.com/span')

            resources.embed_media(root, None, None, None)

            # Expected calls to make_data_url().
            mock_make_data_url.assert_any_call('http://example.com/image.jpg',  None, 'image/jpeg', None, None)
            mock_make_data_url.assert_any_call('http://example.com/image2.jpg', None, None, None, None)
            mock_make_data_url.assert_any_call('http://example.com/audio.mp3', None, 'audio/mp3', None, None)
            mock_make_data_url.assert_any_call('http://example.com/video.mp4', None, None, None, None)
            mock_make_data_url.assert_any_call('http://example.com/track.vtt', None, None, None, None)
            self.assertEqual(5, mock_make_data_url.call_count)

            # Check elements that should have been converted
            for element in [img1, source1, audio1, video1, track1]:
                self.assertEqual(mock_url, element.get('src'))

            # Check elements that should not have been converted
            self.assertEqual('data:image/jpeg;base64,abc', img2.get('src'))
            self.assertEqual('data:;base64,def', source2.get('src'))
            self.assertEqual('data:audio/mp3,abc', audio2.get('src'))
            self.assertEqual('data:,def', video2.get('src'))
            self.assertEqual('#fragment', track2.get('src'))
            self.assertEqual('http://example.com/div', div.get('src'))
            self.assertEqual('http://example.com/span', span.get('src'))



    def test_make_data_url(self):

        with patch('lamarkdown.lib.resources.read_url') as mock_read_url,\
             patch('lamarkdown.lib.resources.embed_stylesheet_resources') as mock_embed_stylesheet_resources:

            input_url = 'http://example.com/mock'
            resource_path = 'mock_path/'

            content = b'mock_content'
            content_converted = 'mock_content_converted'
            b64_content = 'bW9ja19jb250ZW50'
            b64_content_converted = 'bW9ja19jb250ZW50X2NvbnZlcnRlZA=='

            mock_embed_stylesheet_resources.return_value = content_converted

            # 1. Test when read_url() _doesn't_ automatically determine the mime type

            mock_read_url.return_value = (False, content, None)

            # Plain text resource -- no stylesheet embedding
            data_url = resources.make_data_url(input_url, resource_path, 'text/plain', None, None)
            self.assertEqual(data_url, f'data:text/plain;base64,{b64_content}')

            # URL contains stylesheet -- must convert it to an embedded form.
            data_url = resources.make_data_url(input_url, resource_path, 'text/css', None, None)
            self.assertEqual(data_url, f'data:text/css;base64,{b64_content_converted}')


            # 2. Test when read_url() _does_ return a mime type, and one isn't passed in.

            mock_read_url.return_value = (False, content, 'text/css')
            data_url = resources.make_data_url(input_url, resource_path, None, None, None)
            self.assertEqual(data_url, f'data:text/css;base64,{b64_content_converted}')

            mock_read_url.return_value = (False, content, 'text/plain')
            data_url = resources.make_data_url(input_url, resource_path, None, None, None)
            self.assertEqual(data_url, f'data:text/plain;base64,{b64_content}')


            # 3. Test what happens when two mime types are available. The one passed in (and thus
            # explicit) should take precedence over the one automatically determined.

            mock_read_url.return_value = (False, content, 'text/css')
            data_url = resources.make_data_url(input_url, resource_path, 'text/plain', None, None)
            self.assertEqual(data_url, f'data:text/plain;base64,{b64_content}')

            mock_read_url.return_value = (False, content, 'text/plain')
            data_url = resources.make_data_url(input_url, resource_path, 'text/css', None, None)
            self.assertEqual(data_url, f'data:text/css;base64,{b64_content_converted}')


    def test_read_url(self):

        progress = MockProgress(expect_error = True)
        cache = Mock()

        # 1. Read a relative URL, which ought to become a local file read.
        with patch('urllib.request.urlopen') as mock_urlopen,\
             patch('builtins.open', lambda *a,**k: io.StringIO('mock_file_content')):

            result = resources.read_url('file.txt', 'dir', cache, progress)
            mock_urlopen.assert_not_called()
            self.assertEqual((False, 'mock_file_content', 'text/plain'), result)


        # 2. Read a cached remote URL.
        with patch('urllib.request.urlopen') as mock_urlopen,\
             patch('builtins.open') as mock_open:

            cached_url = 'http://cached.example.com/file.txt'
            cache.get.side_effect = \
                lambda key: {cached_url: ('cached_content', 'text/mock')}.get(key)

            result = resources.read_url(cached_url, None, cache, progress)
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

                result = resources.read_url(url, None, cache, progress)
                self.assertEqual(exp_result, result)

                # Caching
                if exp_cache_time is None:
                    cache.set.assert_not_called()
                else:
                    cache.set.assert_called_with(url, (content, mime), expire = exp_cache_time)



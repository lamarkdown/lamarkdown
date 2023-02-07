from ..util.mock_progress import MockProgress
from lamarkdown.lib import resource_writers

import unittest
from unittest.mock import patch, Mock, PropertyMock, ANY

import email.utils
import io
from textwrap import dedent
from xml.etree import ElementTree

class ResourceWritersTestCase(unittest.TestCase):

    @patch('lamarkdown.lib.resources.read_url')
    def test_make_data_url(self, mock_read_url):

        b64_orig = 'bW9ja19jb250ZW50' # base64 encoding of "mock_content"
        b64_converted = 'bW9ja19jb250ZW50X2NvbnZlcnRlZA==' # b64 of "mock_content_converted"

        mock_build_params = Mock()
        converter = Mock()
        converter.return_value = (b'mock_content_converted', 'tx/CONV')

        for mime_arg,   mime_auto,  conv,      expected_data_url in [
            (None,      None,       None,      f'data:;base64,{b64_orig}'),
            (None,      None,       converter, f'data:tx/CONV;base64,{b64_converted}'),
            ('tx/Orig', None,       None,      f'data:tx/Orig;base64,{b64_orig}'),
            ('tx/Orig', None,       converter, f'data:tx/CONV;base64,{b64_converted}'),
            (None,      'tx/_auto', None,      f'data:tx/_auto;base64,{b64_orig}'),
            (None,      'tx/_auto', converter, f'data:tx/CONV;base64,{b64_converted}'),
            ('tx/Orig', 'tx/_auto', None,      f'data:tx/Orig;base64,{b64_orig}'),
            ('tx/Orig', 'tx/_auto', converter, f'data:tx/CONV;base64,{b64_converted}')
        ]:
            mock_read_url.return_value = (False, b'mock_content', mime_auto)
            actual_data_url = resource_writers.make_data_url('http://example.com/mock',
                                                             mime_arg,
                                                             mock_build_params,
                                                             *([] if conv is None else [conv]))
            self.assertEqual(expected_data_url, actual_data_url)


    @patch('lamarkdown.lib.resource_writers.make_data_url')
    def test_stylesheet_embed(self, mock_make_data_url):
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
            rf'''p{{ x: "url(abc)";  y: url({mock_url}); z: "url(jkl)"}} ''',
            rf'''p{{ x: url({mock_url}) url({mock_url});  z: url({mock_url})}}''',
        ]
                        # data_url = make_data_url(url, None, self.build_params, self._convert)

        mock_build_params = Mock()

        for css, exp_url_list, exp_result in zip(inputs, expected_urls, expected_results):
            sw = resource_writers.StylesheetWriter(mock_build_params)
            mock_make_data_url.return_value = mock_url

            result = sw._embed(css)

            # Ensure that make_data_url() is called correctly.
            self.assertEqual(len(exp_url_list), mock_make_data_url.call_count)
            for url in exp_url_list:
                mock_make_data_url.assert_any_call(url, ANY, mock_build_params, ANY)

            # Check overall result.
            self.assertEqual(exp_result, result)
            mock_make_data_url.reset_mock()


    @patch('lamarkdown.lib.resource_writers.make_data_url')
    def test_embed_media(self, mock_make_data_url):
        mock_make_data_url.return_value = 'data:mock'

        root = ElementTree.Element('div')
        p = ElementTree.SubElement(root, 'p')

        mock_build_params = Mock()

        # Mock embedding rule that embeds everything, except elements having a special mime
        # type.
        type(mock_build_params).embed_rule = \
            lambda self, type = '', **k: type != 'no/embed'

        # We should be able to embed src= URLs in all the following cases.
        # (<embed> and <source> also have type=... attributes for specifying the mime type.
        # <input> has a type= attribute for a different purpose.)
        remote_data = [
            ('audio',  'mp3',  'audio/mpeg',             {}),
            ('audio',  'mp3',  'audio/mpeg',             {'type': 'mock/type'}),
            ('embed',  'jpg',  'image/jpeg',             {}),
            ('embed',  'jpg',  'mock/type',              {'type': 'mock/type'}), # type attr
            ('iframe', 'html', 'text/html',              {}),
            ('iframe', 'html', 'text/html',              {'type': 'mock/type'}),
            ('input',  'jpg',  'image/jpeg',             {}),
            ('input',  'jpg',  'image/jpeg',             {'type': 'image'}),
            ('input',  'jpg',  'image/jpeg',             {'type': 'mock/type'}),
            ('img',    'jpg',  'image/jpeg',             {}),
            ('img',    'jpg',  'image/jpeg',             {'type': 'mock/type'}),
            ('script', 'js',   'application/javascript', {}),
            ('script', 'js',   'application/javascript', {'type': 'mock/type'}),
            ('source', 'jpg',  'image/jpeg',             {}),
            ('source', 'jpg',  'mock/type',              {'type': 'mock/type'}), # type attr
            ('track',  'vtt',  'text/vtt',               {}),
            ('track',  'vtt',  'text/vtt',               {'type': 'mock/type'}),
            ('video',  'mp4',  'video/mp4',              {}),
            ('video',  'mp4',  'video/mp4',              {'type': 'mock/type'}),
        ]

        for tag, ext, mime_type, attr in remote_data:
            ElementTree.SubElement(p, tag, src = f'http://example.com/file.{ext}', **attr)

        # We should _avoid_ doing anything to these kinds of tags/URL combinations:
        local_data = [
            ('audio',  'data:audio/mpeg,abc',         {}),
            ('embed',  'http://example.com/file.jpg', {'type': 'no/embed'}),
            ('img',    'data:image/jpeg;base64,abc',  {}),
            ('script', 'data:;base64,def',            {}),
            ('source', 'http://example.com/file.jpg', {'type': 'no/embed'}),
            ('video',  'data:,def',                   {}),
            ('track',  '#fragment',                   {}),
            ('div',    'http://example.com/div',      {}),
            ('span',   'http://example.com/span',     {}),
        ]

        non_modified_elements = [
            (ElementTree.SubElement(p, tag, src = src, **attr), src)
            for tag, src, attr in local_data
        ]

        # Production code
        resource_writers.embed_media(root, mock_build_params)

        # Verify that embeddable things have been embedded
        for tag, ext, mime_type, attr in remote_data:
            mock_make_data_url.assert_any_call(
                f'http://example.com/file.{ext}',
                'mock/type' if mime_type == 'mock_type' else None,
                mock_build_params)

        self.assertEqual(len(remote_data), mock_make_data_url.call_count)

        # Verify non-embeddable things have not been embedded
        for element, src in non_modified_elements:
            self.assertEqual(src, element.get('src'))

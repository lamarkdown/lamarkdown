from ..util.mock_progress import MockProgress
from lamarkdown.lib import resources, resource_writers

import unittest
from unittest.mock import patch, Mock, PropertyMock, ANY

import base64
import email.utils
import io
import os
import tempfile
from textwrap import dedent
from xml.etree import ElementTree

# TODO:
# - handling of cycles in nested stylesheets


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

        url = 'http://example.com/image.jpg'
        data_url = 'data:mock'

        mock_build_params = Mock()

        mock_make_data_url.return_value = data_url

        for input_css,                 base_url, embed,  exp_urls, expected_css in [
            ('',                       '',       [],     [],       ''),

            ('/* comment */',          '',       [],     [],       ''),
            (f'"url({url})"',          '',       [url],  [],       f'"url({url})"'),
            (f"'url({url})'",          '',       [url],  [],       f"'url({url})'"),
            # TODO: also test for whitespace removal/compaction.

            (f'url({url})',            '',       [url],  [url],    f'url("{data_url}")'),
            (f'url("{url}")',          '',       [url],  [url],    f'url("{data_url}")'),
            (f'src("{url}")',          '',       [url],  [url],    f'url("{data_url}")'),
            (f'url(  "{url}"   )',     '',       [url],  [url],    f'url("{data_url}")'),
            (f'@import"{url}";',       '',       [url],  [url],    f'@import "{data_url}";'),
            (f'@import   "{url}"  ;',  '',       [url],  [url],    f'@import "{data_url}"  ;'),
            (f'@import url("{url}");', '',       [url],  [url],    f'@import url("{data_url}");'),

            (f'url({url})',            '',       [],     [],       f'url("{url}")'),
            (f'@import"{url}";',       '',       [],     [],       f'@import "{url}";'),

            (f'url({url})',            'a/b/c/', [],     [],       f'url("{url}")'),
            (f'@import"{url}";',       'a/b/c',  [],     [],       f'@import "{url}";'),

            (f'url({url})',            'a/b/c/', [url],  [url],    f'url("{data_url}")'),
            (f'@import"{url}";',       'a/b/c',  [url],  [url],    f'@import "{data_url}";'),

            (f'url(dir/file)',         'a/b/c/', [],     [],       f'url("a/b/c/dir/file")'),
            (f'@import"dir/file";',    'a/b/c',  [],     [],       f'@import "a/b/dir/file";'),

            (
                r'''p{ x: "url(abc)"; /* url(def) */ y: url("ghi"); z: "url(jkl)"} /*url(mno) */''',
                '',
                ['ghi'],
                ['ghi'],
                rf'''p{{ x: "url(abc)";  y: url("{data_url}"); z: "url(jkl)"}} '''
            ),

            (
                r'''p{ x: url(abc) url(def); /*y: "url(ghi)";*/ z: url(jkl)}''',
                '',
                ['abc', 'def', 'jkl'],
                ['abc', 'def', 'jkl'],
                rf'''p{{ x: url("{data_url}") url("{data_url}");  z: url("{data_url}")}}'''
            ),

            (
                rf'''p{{ x: url(abc) url(def) url({url}) url({url}2) }}''',
                'a/b/c',
                ['a/b/def', url],
                ['a/b/def', url],
                rf'''p{{ x: url("a/b/abc") url("{data_url}") url("{data_url}") url("{url}2") }}'''
            ),

            # Special characters
            ('''url(\\\\\\x\\y\\z\\\\)''',
             '', ['\\xyz\\'], ['\\xyz\\'], fr'url("{data_url}")'),

            ('''url(\\69 \\06d\\0061\t\\00067\\000065 )''',
             '', ['image'], ['image'], fr'url("{data_url}")'),

            ('''url("\\"\\69 \\06d\\0061\t\\00067\\000065 \\"")''',
             '', ['"image"'], ['"image"'], fr'url("{data_url}")'),

            ('''url('\\'\\69 \\06d\\0061\t\\00067\\000065 \\'')''',
             '', ["'image'"], ["'image'"], fr'url("{data_url}")'),
        ]:
            embed_rule = lambda url='', **k: url in embed
            type(mock_build_params).embed_rule = PropertyMock(return_value = embed_rule)

            sw = resource_writers.StylesheetWriter(mock_build_params)
            output_css = sw._embed(base_url, input_css)

            msg = repr(dict(input_css=input_css, base_url=base_url,
                            embed=embed, expected_css=expected_css))

            # Ensure that make_data_url() is called correctly.
            self.assertEqual(len(exp_urls), mock_make_data_url.call_count, msg = msg)
            for url in exp_urls:
                mock_make_data_url.assert_any_call(url, ANY, mock_build_params, ANY)
            mock_make_data_url.reset_mock()

            self.assertEqual(expected_css, output_css, msg = msg)


    def test_nested_stylesheets(self):
        """
        More expansive/holistic test of resources.py and resource_writers.py, as they relate to
        the embedding of stylesheets.
        """

        with tempfile.TemporaryDirectory() as dir:

            os.chdir(dir)
            os.mkdir('dir0')
            os.mkdir(os.path.join('dir0', 'dir1'))
            os.mkdir('dir2')
            os.mkdir(os.path.join('dir2', 'dir3'))
            os.mkdir(os.path.join('dir2', 'dir3', 'dir4'))

            # Test file structure:
            # |
            # +-- dir0/
            # |   |
            # |   +-- fileA.css
            # |   \-- dir1
            # |       |
            # |       +-- fileB.css
            # |       \-- fileB.txt
            # |
            # \-- dir2/
            #     |
            #     +-- fileC.css
            #     +-- fileC.txt
            #     \-- dir3/
            #         |
            #         \-- dir4/
            #             |
            #             +-- fileD.css
            #             \-- fileD.txt


            # NOTE: this test is sensitive to the exact spacing choices made by the production code.
            # Since there are multiple levels of base64 encoding, more/less whitespace results in
            # different _non-whitespace_ characters too. So care is needed!

            def nospace(s):
                return s.replace(' ', '').replace('\n', '').replace('[_]', ' ')

            orig_contentA = nospace('''
                @import[_]"dir1/fileB.css";
                @import[_]"dir1/fileB.txt";
            ''')

            orig_contentB = nospace('''
                @import[_]"../../dir2/fileC.css";
                @import[_]"../../dir2/fileC.txt";
            ''')

            orig_contentC = nospace('''
                @import[_]"dir3/dir4/fileD.txt";
                @import[_]"dir3/dir4/fileD.css";
            ''')

            orig_contentD = nospace('''
                p { color: blue }
            ''')

            with open(os.path.join('dir0', 'fileA.css'), 'w') as w:
                w.write(orig_contentA)

            for file in ['fileB.css', 'fileB.txt']:
                with open(os.path.join('dir0', 'dir1', file), 'w') as w:
                    w.write(orig_contentB)

            for file in ['fileC.css', 'fileC.txt']:
                with open(os.path.join('dir2', file), 'w') as w:
                    w.write(orig_contentC)

            for file in ['fileD.css', 'fileD.txt']:
                with open(os.path.join('dir2', 'dir3', 'dir4', file), 'w') as w:
                    w.write(orig_contentD)


            # Work out the expected result programmatically. It would be too fragile to hard-code
            # a manual calculation here.

            b64_contentD = base64.b64encode(orig_contentD.encode()).decode()
            conv_contentC = nospace(f'''
                @import[_]"dir2/dir3/dir4/fileD.txt";
                @import[_]"data:text/css;base64,{b64_contentD}";
            ''')
            b64_contentC = base64.b64encode(conv_contentC.encode()).decode()
            conv_contentB = nospace(f'''
                @import[_]"data:text/css;base64,{b64_contentC}";
                @import[_]"dir2/fileC.txt";
            ''')
            b64_contentB = base64.b64encode(conv_contentB.encode()).decode()
            conv_contentA = nospace(f'''
                @import[_]"data:text/css;base64,{b64_contentB}";
                @import[_]"dir0/dir1/fileB.txt";
            ''')
            # b64_contentA = base64.b64encode(conv_contentA.encode()).decode()


            mock_build_params = Mock()
            type(mock_build_params).resource_base_url = PropertyMock(return_value = 'dir0/')
            # Embed only .css files, not .txt files.
            type(mock_build_params).embed_rule = PropertyMock(return_value =
                                                              lambda url,**k: url.endswith('css'))

            expected = f'<style>\n{conv_contentA}\n</style>'

            for resource_spec in [
                resources.ContentResourceSpec(
                    xpaths_required = [],
                    content_factory = lambda *a: orig_contentA),
                resources.UrlResourceSpec(
                    xpaths_required = [],
                    url_factory     = lambda *a: 'fileA.css',
                    base_url        = 'dir0/',
                    cache           = Mock(),
                    embed_fn        = lambda *a: True,
                    hash_type_fn    = None,
                    mime_type       = 'text/css')
            ]:
                resource = resource_spec.make_resource(set(), Mock())
                output = resource_writers.StylesheetWriter(mock_build_params).format([resource])
                self.assertEqual(expected, output)


    def test_embed_recursion_loop(self):
        pass
        # TODO



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
        resource_writers.embed_media(root, '', mock_build_params)

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

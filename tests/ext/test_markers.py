from ..util.mock_progress import MockProgress
from ..util.hamcrest_elements import *

import unittest
from unittest.mock import patch
from hamcrest import *

import lamarkdown.ext
import lamarkdown.ext.markers
import markdown
import lxml.html

import sys
from textwrap import dedent
from xml.etree import ElementTree

sys.modules['la'] = sys.modules['lamarkdown.ext']

class MarkersTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text,
                           hook = lambda md: None,
                           **kwargs):
        md = markdown.Markdown(
            extensions = ['la.markers'],
            extension_configs = {
                'la.markers': {
                    'progress': MockProgress(),
                }
            }
        )
        hook(md)
        return md.convert(dedent(markdown_text).strip())


    def test_basic_usage(self):
        html = self.run_markdown(
            r'''
            # Heading

            /{.classX #idY attrZ="value"}

            1. Item1

                /{.classA}

            2. Item2
            ''')

        assert_that(
            lxml.html.fromstring(html),
            contains_exactly(
                is_element('h1', {}, 'Heading'),
                is_element('div', {'attrz': 'value',
                                   'class': 'classX',
                                   'id': 'idY',
                                   'style': matches_regexp(r'display:\s*none;?')}, None),
                is_element('ol', {}, space(),
                    is_element('li', {}, space(),
                        is_element('p', {}, 'Item1'),
                        is_element('div', {'style': matches_regexp(r'display:\s*none;?')}, None),
                    ),
                    is_element('li', {}, space(),
                        is_element('p', {}, 'Item2'),
                    ),
                )
            ))


    def test_non_usage(self):
        '''
        Check that we respect AtomicStrings, and can handle empty elements.

        We're reaching inside to test the TreeProcessor within the extension directly, because it's
        awkward to arrange the right input test data otherwise.
        '''

        root = ElementTree.fromstring(r'''
            <div>
                <p></p>
                <p>/{.classX}</p>
                <p>/{.classX}</p>
            </div>
        ''')
        root[1].text = markdown.util.AtomicString(root[1].text)

        lamarkdown.ext.markers.MarkersTreeProcessor(None, MockProgress()).run(root)

        assert_that(
            root,
            contains_exactly(
                is_element('p', {}, None),
                is_element('p', {}, '/{.classX}'),
                is_element('div', {'class': 'classX'}, None)))



    def test_extension_setup(self):
        import importlib
        import importlib.metadata

        module_name, class_name = importlib.metadata.entry_points(
            group = 'markdown.extensions')['la.markers'].value.split(':', 1)
        cls = importlib.import_module(module_name).__dict__[class_name]

        assert_that(
            cls,
            same_instance(lamarkdown.ext.markers.MarkersExtension))

        instance = lamarkdown.ext.markers.makeExtension()

        assert_that(
            instance,
            instance_of(lamarkdown.ext.markers.MarkersExtension))

        class MockBuildParams:
            def __getattr__(self, name):
                raise ModuleNotFoundError

        with patch('lamarkdown.lib.build_params.BuildParams', MockBuildParams()):
            instance = lamarkdown.ext.markers.makeExtension()

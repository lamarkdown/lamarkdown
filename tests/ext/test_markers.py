from ..util import html_block_processor
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

def whitespace():
    return matches_regexp(r'\s*')

def is_element(tag = None, *, text = None, tail = None, children = [], **attrib):
    if 'class' not in attrib and 'className' in attrib:
        attrib['class'] = attrib['className']
        del attrib['className']

    return all_of(
        has_properties(tag = tag,
                       text = text,
                       tail = tail,
                       attrib = has_entries(**attrib)),
        empty() if len(children) == 0 else contains_exactly(*children)
    )



class MarkersTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text,
                           hook = lambda md: None,
                           **kwargs):
        md = markdown.Markdown(
            extensions = ['la.markers']
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

        # assert_that(
        #     lxml.html.fromstring(html),
        #     contains_exactly(
        #         has_properties(tag = 'h1', text = 'Heading'),
        #         has_properties(tag = 'div',
        #                        attrib = has_entries({
        #                            'attrz': 'value',
        #                            'class': 'classX',
        #                            'id': 'idY',
        #                            'style': matches_regexp(r'display:\s*none;?')})),
        #         all_of(
        #             has_properties(tag = 'ol'),
        #             contains_exactly(1
        #                 has_properties(tag = 'li')
        #             )
        #         )
        #     ))

        # assert_that(
        #     lxml.html.fromstring(html),
        #     is_element('div', children = [
        #         is_element('h1', text = 'Heading', tail = whitespace()),
        #         is_element('div',
        #                    attrz = 'value',
        #                    className = 'classX',
        #                    id = 'idY',
        #                    style = matches_regexp(r'display:\s*none;?')),
        #         is_element('ol')
        #         # is_element('ol', children = [
        #         #     is_element('li', children = [
        #         #         is_element('p', text = 'Item1'),
        #         #         is_element('div', className = 'classA', style = matches_regexp(r'display:\s*none;?')),
        #         #     ]),
        #         #     is_element('li', children = [
        #         #         is_element('p', text = 'Item2')
        #         #     ])
        #         # ])
        #     ]))

        self.assertRegex(
            html,
            r'''(?x)
            \s* <h1>Heading</h1>
            \s* <div[ ]attrZ="value"[ ]class="classX"[ ]id="idY"[ ]style="display:\s*none;?"\s*(/>|></div>)
            \s* <ol>
            \s* <li>
            \s* <p>Item1</p>
            \s* <div[ ]class="classA"[ ]style="display:\s*none;?"\s*(/>|></div>)
            \s* </li>
            \s* <li>
            \s* <p>Item2</p>
            \s* </li>
            \s* </ol>
            \s*
            '''
        )

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

        lamarkdown.ext.markers.MarkersTreeProcessor(None).run(root)

        assert_that(
            root,
            contains_exactly(
                has_properties(tag = 'p', text = None),
                has_properties(tag = 'p', text = '/{.classX}'),
                has_properties(tag = 'div', attrib = has_entries({'class': 'classX'}))))



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

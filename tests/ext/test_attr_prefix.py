from __future__ import annotations
from ..util.markdown_ext import entry_point_cls
import lamarkdown.ext
import lamarkdown.ext.attr_prefix

import unittest
from unittest.mock import patch
from hamcrest import assert_that, contains_exactly, instance_of, same_instance
from ..util.hamcrest_elements import space, is_element

import markdown
import lxml.html

import sys
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']


class AttrPrefixTestCase(unittest.TestCase):

    def run_markdown(self,
                     markdown_text,
                     hook = lambda md: None,
                     **kwargs):
        md = markdown.Markdown(
            extensions = ['la.attr_prefix']
        )
        hook(md)
        return md.convert(dedent(markdown_text).strip())


    def test_basic_usage(self):
        html = self.run_markdown(
            r'''
            # Heading

            {.classX #idY attrZ="value"}
            1. Item1

                {:.classA}
                Some text

            2. Item2
            ''')

        assert_that(
            lxml.html.fromstring(html),
            contains_exactly(
                is_element('h1', {}, 'Heading'),
                is_element(
                    'ol', {'class': 'classX', 'id': 'idY', 'attrz': 'value'}, space(),
                    is_element(
                        'li', {}, space(),
                        is_element('p', {}, 'Item1'),
                        is_element('p', {'class': 'classA'}, 'Some text')
                    ),
                    is_element(
                        'li', {}, space(),
                        is_element('p', {}, 'Item2')
                    )
                )
            )
        )


    def test_variations(self):

        for input, expected_attrib in [
            ('{.classA}', {'class': 'classA'}),
            ('{:.classA}', {'class': 'classA'}),
            ('{ .classA}', {'class': 'classA'}),
            ('{: .classA}', {'class': 'classA'}),

            ('{:#idA}', {'id': 'idA'}),
            ('{:attr-a=valueA}', {'attr-a': 'valueA'}),
            ('{:attr-a="valueA"}', {'attr-a': 'valueA'}),
            ('{:#idA .classA attr-a=valueA}',
                {'id': 'idA', 'class': 'classA', 'attr-a': 'valueA'}),

            ('{:#idA}\n{:.classA}\n{attr-a=valueA}',
                {'id': 'idA', 'class': 'classA', 'attr-a': 'valueA'}),
            ('{:#idA}\n{#idB}\n{ #idC}', {'id': 'idA'}),
            ('{:.classA}\n{.classB}\n{ .classC}', {'class': 'classC classB classA'}),

            ('{:#idA}\n\n{:.classA}\n\n{attr-a=valueA}',
                {'id': 'idA', 'class': 'classA', 'attr-a': 'valueA'}),
            ('{:#idA}\n\n{#idB}\n\n{ #idC}', {'id': 'idA'}),
            ('{:.classA}\n\n{.classB}\n\n{ .classC}', {'class': 'classC classB classA'}),
        ]:
            html = self.run_markdown(f'{input}\nSome text')

            assert_that(
                lxml.html.fromstring(html),
                is_element('p', expected_attrib, 'Some text'))


    def test_extension_setup(self):
        assert_that(
            entry_point_cls('la.attr_prefix'),
            same_instance(lamarkdown.ext.attr_prefix.AttrPrefixExtension))

        instance = lamarkdown.ext.attr_prefix.makeExtension()

        assert_that(
            instance,
            instance_of(lamarkdown.ext.attr_prefix.AttrPrefixExtension))

        class MockBuildParams:
            def __getattr__(self, name):
                raise ModuleNotFoundError

        with patch('lamarkdown.lib.build_params.BuildParams', MockBuildParams()):
            instance = lamarkdown.ext.attr_prefix.makeExtension()

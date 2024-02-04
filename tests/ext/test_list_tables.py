from __future__ import annotations
from ..util.markdown_ext import entry_point_cls, assert_regex
import lamarkdown.ext
import lamarkdown.ext.list_tables

import unittest
from unittest.mock import patch
from hamcrest import assert_that, instance_of, same_instance

import markdown

import sys
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']


class ListTablesTestCase(unittest.TestCase):

    def run_markdown(self,
                     markdown_text,
                     **kwargs):
        md = markdown.Markdown(
            extensions = ['la.list_tables', 'la.attr_prefix']
        )
        return md.convert(dedent(markdown_text).strip())


    def test_tbody_only(self):
        html = self.run_markdown(
            r'''
            {-list-table attr="0"}
            *   - one
                    {attr="1"}
                - _two_
                    {attr="2"}
            *   - x **three** x
                    {attr="3"}
                - four
                    {attr="4"}
            ''')

        assert_regex(
            html,
            r'''
            <table[ ]attr="0">
                <tbody>
                    <tr>
                        <td[ ]attr="1">one</td>
                        <td[ ]attr="2"><em>two</em></td>
                    </tr>
                    <tr>
                        <td[ ]attr="3">x[ ]<strong>three</strong>[ ]x</td>
                        <td[ ]attr="4">four</td>
                    </tr>
                </tbody>
            </table>
            ''')


    def test_extra_columns(self):
        html = self.run_markdown(
            r'''
            {-list-table}
            *   one

                - two
                - three

                four

            *   five

                six

                - seven
                - eight

                nine

                ten
            ''')

        assert_regex(
            html,
            r'''
            <table>
                <tbody>
                    <tr>
                        <td>one</td>
                        <td>two</td>
                        <td>three</td>
                        <td>four</td>
                    </tr>
                    <tr>
                        <td> \s* <p>five</p> \s* <p>six</p> \s* </td>
                        <td>seven</td>
                        <td>eight</td>
                        <td> \s* <p>nine</p> \s* <p>ten</p> \s* </td>
                    </tr>
                </tbody>
            </table>
            ''')


    def test_thead_only(self):
        'Dubious use case, but it should work.'
        html = self.run_markdown(
            r'''
            {-list-table attr="0"}
            *   - # one           {attr="1"}
                - # _two_         {attr="2"}
            *   - # x **three** x {attr="3"}
                - # four          {attr="4"}
            ''')

        assert_regex(
            html,
            r'''
            <table[ ]attr="0">
                <thead>
                    <tr>
                        <th[ ]attr="1">one</th>
                        <th[ ]attr="2"><em>two</em></th>
                    </tr>
                    <tr>
                        <th[ ]attr="3">x[ ]<strong>three</strong>[ ]x</th>
                        <th[ ]attr="4">four</th>
                    </tr>
                </thead>
            </table>
            ''')


    def test_thead_tbody_tfoot(self):
        html = self.run_markdown(
            r'''
            {-list-table}
            *   - # one
                - # two
            *   - three
                - # four
            *   - # five
                - six
            *   - # seven
                - # eight
            ''')

        assert_regex(
            html,
            r'''
            <table>
                <thead>
                    <tr>
                        <th>one</th>
                        <th>two</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>three</td>
                        <th>four</th>
                    </tr>
                    <tr>
                        <th>five</th>
                        <td>six</td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr>
                        <th>seven</th>
                        <th>eight</th>
                    </tr>
                </tfoot>
            </table>
            ''')


    def test_thead_override(self):
        for text in [
                r'''
                {-list-table}
                *   - # one
                    - # two
                *   - three
                    - four
                ''',

                r'''
                {-list-table}
                * #
                    - # one
                    - # two
                *   - three
                    - four
                ''',

                r'''
                {-list-table}
                * #
                    - one
                    - # two
                *   - three
                    - four
                ''',

                r'''
                {-list-table}
                * #
                    - # one
                    - two
                *   - three
                    - four
                ''',

                r'''
                {-list-table}
                * #
                    - one
                    - two
                *   - three
                    - four
                ''']:

            assert_regex(
                self.run_markdown(text),
                r'''
                <table>
                    <thead>
                        <tr>
                            <th>one</th>
                            <th>two</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>three</td>
                            <td>four</td>
                        </tr>
                    </tbody>
                </table>
                ''')


    def test_thead_multiple_rows(self):
        html = self.run_markdown(
            r'''
            {-list-table}
            *   - # one
                - # two
            * #
                - # three
                - # four
            * #
                - five
                - # six
            * #
                - # seven
                - eight
            * #
                - nine
                - ten
            *   - eleven
                - twelve
            ''')

        assert_regex(
            html,
            r'''
            <table>
                <thead>
                    <tr>
                        <th>one</th>
                        <th>two</th>
                    </tr>
                    <tr>
                        <th>three</th>
                        <th>four</th>
                    </tr>
                    <tr>
                        <th>five</th>
                        <th>six</th>
                    </tr>
                    <tr>
                        <th>seven</th>
                        <th>eight</th>
                    </tr>
                    <tr>
                        <th>nine</th>
                        <th>ten</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>eleven</td>
                        <td>twelve</td>
                    </tr>
                </tbody>
            </table>
            ''')


    def test_heading_tree(self):
        html = self.run_markdown(
            r'''
            {-list-table}
            * #
                - one
                    - oneA
                    - oneB
                        - oneBA
                - two
                    - twoA
                        - twoAA
                        - twoAB
                        - twoAC
                    - twoB
                - three
            *   - oneA_data
                - oneBA_data
                - twoAA_data
                - twoAB_data
                - twoAC_data
                - twoB_data
                - three_data
            ''')

        assert_regex(
            html,
            r'''
            <table>
                <thead>
                    <tr>
                        <th[ ]colspan="2">one</th>
                        <th[ ]colspan="4">two</th>
                        <th[ ]rowspan="0">three</th>
                    </tr>
                    <tr>
                        <th[ ]rowspan="0">oneA</th>
                        <th>oneB</th>
                        <th[ ]colspan="3">twoA</th>
                        <th[ ]rowspan="0">twoB</th>
                    </tr>
                    <tr>
                        <th>oneBA</th>
                        <th>twoAA</th>
                        <th>twoAB</th>
                        <th>twoAC</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>oneA_data</td>
                        <td>oneBA_data</td>
                        <td>twoAA_data</td>
                        <td>twoAB_data</td>
                        <td>twoAC_data</td>
                        <td>twoB_data</td>
                        <td>three_data</td>
                    </tr>
                </tbody>
            </table>
            ''')

    def test_nested_tables(self):
        html = self.run_markdown(
            r'''
            {-list-table}
            * #
                - one

                    {-list-table}
                    *   - 1
                        - 2
                    *   - 3
                        - 4

                - two

            *   - three
                - four

                    {-list-table}
                    *   - 5
                        - 6
                    *   - 7
                        - 8
            ''')

        assert_regex(
            html,
            r'''
            <table>
                <thead>
                    <tr>
                        <th>
                            <p>one</p>
                            <table>
                                <tbody>
                                    <tr> \s* <td>1</td> \s* <td>2</td> \s* </tr>
                                    <tr> \s* <td>3</td> \s* <td>4</td> \s* </tr>
                                </tbody>
                            </table>
                        </th>
                        <th>two</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>three</td>
                        <td>
                            <p>four</p>
                            <table>
                                <tbody>
                                    <tr> \s* <td>5</td> \s* <td>6</td> \s* </tr>
                                    <tr> \s* <td>7</td> \s* <td>8</td> \s* </tr>
                                </tbody>
                            </table>
                        </td>
                    </tr>
                </tbody>
            </table>
            ''')



    def test_extension_setup(self):
        assert_that(
            entry_point_cls('la.list_tables'),
            same_instance(lamarkdown.ext.list_tables.ListTablesExtension))

        instance = lamarkdown.ext.list_tables.makeExtension()

        assert_that(
            instance,
            instance_of(lamarkdown.ext.list_tables.ListTablesExtension))

        class MockBuildParams:
            def __getattr__(self, name):
                raise ModuleNotFoundError

        with patch('lamarkdown.lib.build_params.BuildParams', MockBuildParams()):
            instance = lamarkdown.ext.list_tables.makeExtension()

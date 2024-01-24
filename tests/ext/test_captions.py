from ..util.markdown_ext import entry_point_cls, HtmlInsert
import lamarkdown.ext.captions

import unittest
from unittest.mock import patch
from hamcrest import assert_that, instance_of, same_instance
from ..util.hamcrest_elements import space, is_element

import markdown
import lxml.html

import sys
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']


class CaptionsTestCase(unittest.TestCase):

    def run_markdown(self,
                     markdown_text,
                     extra_extensions: list = [],
                     **kwargs):
        md = markdown.Markdown(
            extensions = ['la.captions', 'attr_list', *extra_extensions]
        )
        return md.convert(dedent(markdown_text).strip())


    def test_image(self):
        html = self.run_markdown(
            r'''
            Test caption.
            {::caption cap_attr="cap_value"}

            ![Test alt](mock_image.jpg){img_attr="img_value"}
            {#theid .aclass fig_attr="fig_value"}
            ''')

        assert_that(
            lxml.html.fromstring(html),
            is_element(
                'figure', {'id': 'theid',
                           'class': 'aclass',
                           'fig_attr': 'fig_value'}, None,
                is_element('figcaption', {'cap_attr': 'cap_value'}, 'Test caption.'),
                is_element('img', {'src':      'mock_image.jpg',
                                   'alt':      'Test alt',
                                   'img_attr': 'img_value'}, None)
            )
        )


    def test_multiparagraph_caption(self):
        html = self.run_markdown(
            r'''
            {::caption}
            > Caption paragraph 1.
            >
            > Caption paragraph 2.

            Fig content.
            ''',
            extra_extensions = ['la.attr_prefix'])

        print(html)

        assert_that(
            lxml.html.fromstring(html),
            is_element(
                'figure', {}, None,
                is_element(
                    'figcaption', {}, space(),
                    is_element('p', {}, 'Caption paragraph 1.'),
                    is_element('p', {}, 'Caption paragraph 2.'),
                    tail = 'Fig content.\n')
            )
        )


    def test_table(self):
        html = self.run_markdown(
            r'''
            Test caption.
            {::caption cap_attr="cap_value"}

            {#theid .aclass tab_attr="tab_value"}
            colA  | colB
            ----- | ----
            cellA | cellB
            ''',
            extra_extensions = ['tables', 'la.attr_prefix']
        )

        # Note: this won't work quite as expected if you embed raw table HTML within the markdown.
        # (Such raw HTML only becomes part of the document in the post-processing stage, and all
        # la.captions will see is a <p> element containing placeholder text.)

        # Even so, it will still work at a practical level; la.captions will enclose the <table>
        # in a <figure> element, an arrangement anticipated by the HTML spec.

        assert_that(
            lxml.html.fromstring(html),
            is_element(
                'table', {'id': 'theid',
                          'class': 'aclass',
                          'tab_attr': 'tab_value'}, space(),
                is_element('caption', {'cap_attr': 'cap_value'}, 'Test caption.'),
                is_element(
                    'thead', {}, space(),
                    is_element(
                        'tr', {}, space(),
                        is_element('th', {}, 'colA'),
                        is_element('th', {}, 'colB'))),
                is_element(
                    'tbody', {}, space(),
                    is_element(
                        'tr', {}, space(),
                        is_element('td', {}, 'cellA'),
                        is_element('td', {}, 'cellB'))),
            )
        )


    def test_figure(self):

        html = self.run_markdown(
            r'''
            Test caption.
            {::caption cap_attr="cap_value"}

            X
            ''',
            extra_extensions = [HtmlInsert(
                '<figure id="theid" class="aclass" fig_attr="fig_value"><p>Fig text</p></figure>')]
        )

        assert_that(
            lxml.html.fromstring(html),
            is_element(
                'figure', {'id': 'theid',
                           'class': 'aclass',
                           'fig_attr': 'fig_value'}, space(),
                is_element('figcaption', {'cap_attr': 'cap_value'}, 'Test caption.'),
                is_element('p', {}, 'Fig text'),
            )
        )


    def test_figure_existing_caption(self):

        html = self.run_markdown(
            r'''
            New caption.
            {::caption}

            X
            ''',
            extra_extensions = [HtmlInsert(
                '<figure id="theid" class="aclass" fig_attr="fig_value">'
                '<figcaption>Existing caption.</figcaption><p>Fig text</p></figure>')]
        )

        assert_that(
            lxml.html.fromstring(html),
            is_element(
                'figure', {'id': 'theid',
                           'class': 'aclass',
                           'fig_attr': 'fig_value'}, space(),
                is_element(
                    'figcaption', {}, 'Existing caption.',
                    is_element('p', {}, 'New caption.')),
                is_element('p', {}, 'Fig text'),
            )
        )


    # def test_listing(self):
    #     html = self.run_markdown(
    #         r'''
    #         Para1.
    #
    #         ```
    #         TestCode
    #         ```
    #
    #         Para2.
    #         ''',
    #         autowrap_listings = True,
    #         extra_extensions = ['fenced_code']
    #         # extra_extensions = ['pymdownx.superfences']
    #     )
    #
    #     print(html)




    def test_extension_setup(self):
        assert_that(
            entry_point_cls('la.captions'),
            same_instance(lamarkdown.ext.captions.CaptionsExtension))

        instance = lamarkdown.ext.captions.makeExtension()

        assert_that(
            instance,
            instance_of(lamarkdown.ext.captions.CaptionsExtension))

        class MockBuildParams:
            def __getattr__(self, name):
                raise ModuleNotFoundError

        with patch('lamarkdown.lib.build_params.BuildParams', MockBuildParams()):
            instance = lamarkdown.ext.captions.makeExtension()

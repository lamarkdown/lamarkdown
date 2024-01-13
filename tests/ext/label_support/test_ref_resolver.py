from lamarkdown.ext.label_support.ref_resolver import RefResolver
from ...util.hamcrest_elements import is_element, space

import unittest
from unittest.mock import Mock
from hamcrest import assert_that

from xml.etree import ElementTree


def mock_find_labeller(element_type: str):
    mock_labeller = Mock()
    mock_labeller.as_string_core = Mock(return_value = f'mock-label-for-{element_type}')
    return mock_labeller


class RefResolverTestCase(unittest.TestCase):

    def test_element_types(self):
        rr = RefResolver()

        root = ElementTree.fromstring('''
            <div>
            <p>Paragraph1 <a href="#id1">##</a></p>
            <p>Paragraph2 <a href="#id2">##x</a></p>
            <p>Paragraph3 <a href="#id3">##{x}</a></p>
            <p>Paragraph4 <a href="#id4">##l</a></p>
            <p>Paragraph5 <a href="#id5">##{l}</a></p>
            <p>Paragraph6 <a href="#id6">##h</a></p>
            <p>Paragraph7 <a href="#id7">##{h}</a></p>
            <p>Paragraph8 <a href="#id8">##h2</a></p>
            <p>Paragraph9 <a href="#id9">##{h2}</a></p>
            <p>Paragraph10 <a href="#id10">## ##x ##{x} ##l ##{l} ##h ##{h} ##h2 ##{h2}</a></p>
            </div>
            ''')

        rr.find_refs(root)


        assert_that(
            root,
            is_element(
                'div', {}, space(),
                is_element(
                    'p', {}, 'Paragraph1 ',
                    is_element(
                        'a', {'href': '#id1'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##'))),

                is_element(
                    'p', {}, 'Paragraph2 ',
                    is_element(
                        'a', {'href': '#id2'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##x'))),

                is_element(
                    'p', {}, 'Paragraph3 ',
                    is_element(
                        'a', {'href': '#id3'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##{x}'))),

                is_element(
                    'p', {}, 'Paragraph4 ',
                    is_element(
                        'a', {'href': '#id4'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##l'))),

                is_element(
                    'p', {}, 'Paragraph5 ',
                    is_element(
                        'a', {'href': '#id5'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##{l}'))),

                is_element(
                    'p', {}, 'Paragraph6 ',
                    is_element(
                        'a', {'href': '#id6'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##h'))),

                is_element(
                    'p', {}, 'Paragraph7 ',
                    is_element(
                        'a', {'href': '#id7'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##{h}'))),

                is_element(
                    'p', {}, 'Paragraph8 ',
                    is_element(
                        'a', {'href': '#id8'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##h2'))),

                is_element(
                    'p', {}, 'Paragraph9 ',
                    is_element(
                        'a', {'href': '#id9'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##{h2}'))),

                is_element(
                    'p', {}, 'Paragraph10 ',
                    is_element(
                        'a', {'href': '#id10'}, space(),
                        is_element('span', {'class': 'la-ref'}, '##'),
                        is_element('span', {'class': 'la-ref'}, '##x'),
                        is_element('span', {'class': 'la-ref'}, '##{x}'),
                        is_element('span', {'class': 'la-ref'}, '##l'),
                        is_element('span', {'class': 'la-ref'}, '##{l}'),
                        is_element('span', {'class': 'la-ref'}, '##h'),
                        is_element('span', {'class': 'la-ref'}, '##{h}'),
                        is_element('span', {'class': 'la-ref'}, '##h2'),
                        is_element('span', {'class': 'la-ref'}, '##{h2}'))),
            )
        )


        for i in range(1, 11):
            rr.resolve_refs(ElementTree.Element('div', id = f'id{i}'), mock_find_labeller)

        assert_that(
            root,
            is_element(
                'div', {}, space(),
                is_element(
                    'p', {}, 'Paragraph1 ',
                    is_element(
                        'a', {'href': '#id1'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-'))),

                is_element(
                    'p', {}, 'Paragraph2 ',
                    is_element(
                        'a', {'href': '#id2'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-'))),

                is_element(
                    'p', {}, 'Paragraph3 ',
                    is_element(
                        'a', {'href': '#id3'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-'))),

                is_element(
                    'p', {}, 'Paragraph4 ',
                    is_element(
                        'a', {'href': '#id4'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-ol'))),

                is_element(
                    'p', {}, 'Paragraph5 ',
                    is_element(
                        'a', {'href': '#id5'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-ol'))),

                is_element(
                    'p', {}, 'Paragraph6 ',
                    is_element(
                        'a', {'href': '#id6'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-h'))),

                is_element(
                    'p', {}, 'Paragraph7 ',
                    is_element(
                        'a', {'href': '#id7'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-h'))),

                is_element(
                    'p', {}, 'Paragraph8 ',
                    is_element(
                        'a', {'href': '#id8'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-h2'))),

                is_element(
                    'p', {}, 'Paragraph9 ',
                    is_element(
                        'a', {'href': '#id9'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-h2'))),

                is_element(
                    'p', {}, 'Paragraph10 ',
                    is_element(
                        'a', {'href': '#id10'}, space(),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-'),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-'),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-'),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-ol'),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-ol'),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-h'),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-h'),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-h2'),
                        is_element('span', {'class': 'la-ref'}, 'mock-label-for-h2')))
            )
        )


    def test_nesting(self):
        rr = RefResolver()
        root = ElementTree.fromstring('<a href="#theid">##h<em>##h<strong>##h<span>##h</span>##h'
                                      '</strong>##h<span>##h</span>##h</em>##h</a>')

        rr.find_refs(root)


        is_ref1 = is_element('span', {'class': 'la-ref'}, '##h')
        assert_that(
            root,
            is_element(
                'a', {}, '',
                is_ref1,
                is_element(
                    'em', {}, '',
                    is_ref1,
                    is_element(
                        'strong', {}, '',
                        is_ref1,
                        is_element(
                            'span', {}, '',
                            is_ref1),
                        is_ref1),
                    is_ref1,
                    is_element(
                        'span', {}, '',
                        is_ref1),
                    is_ref1),
                is_ref1)
        )

        rr.resolve_refs(ElementTree.Element('div', id = 'theid'), mock_find_labeller)

        is_ref2 = is_element('span', {'class': 'la-ref'}, 'mock-label-for-h')
        assert_that(
            root,
            is_element(
                'a', {}, '',
                is_ref2,
                is_element(
                    'em', {}, '',
                    is_ref2,
                    is_element(
                        'strong', {}, '',
                        is_ref2,
                        is_element(
                            'span', {}, '',
                            is_ref2),
                        is_ref2),
                    is_ref2,
                    is_element(
                        'span', {}, '',
                        is_ref2),
                    is_ref2),
                is_ref2)
        )


    def test_text_embedding(self):
        rr = RefResolver()

        root = ElementTree.fromstring('<a href="#theid">abc##h def##{h}ghi##h jkl</a>')
        rr.find_refs(root)
        rr.resolve_refs(ElementTree.Element('div', id = 'theid'), mock_find_labeller)

        assert_that(
            root,
            is_element(
                'a', {}, 'abc',
                is_element('span', {'class': 'la-ref'}, 'mock-label-for-h', tail = ' def'),
                is_element('span', {'class': 'la-ref'}, 'mock-label-for-h', tail = 'ghi'),
                is_element('span', {'class': 'la-ref'}, 'mock-label-for-h', tail = ' jkl')))



    def test_escaping(self):
        rr = RefResolver()

        root = ElementTree.fromstring(r'<a href="#theid">abc\##h def\##{h}ghi#\#h jkl</a>')
        rr.find_refs(root)

        assert_that(
            root,
            is_element('a', {}, r'abc\##h def\##{h}ghi#\#h jkl'))

        rr.resolve_refs(ElementTree.Element('div', id = 'theid'), mock_find_labeller)

        assert_that(
            root,
            is_element('a', {}, r'abc\##h def\##{h}ghi#\#h jkl'))



    def test_no_id(self):
        rr = RefResolver()

        root = ElementTree.fromstring(r'<a href="#id1">##h</a>')
        rr.find_refs(root)

        assert_that(
            root,
            is_element(
                'a', {}, '',
                is_element('span', {'class': 'la-ref'}, '##h')))

        rr.resolve_refs(ElementTree.Element('div', id = 'id2'), mock_find_labeller)

        assert_that(
            root,
            is_element(
                'a', {}, '',
                is_element('span', {'class': 'la-ref'}, '##h')))


    def test_unknown_element_type(self):
        rr = RefResolver()

        root = ElementTree.fromstring(r'<a href="#theid">##h</a>')
        rr.find_refs(root)

        assert_that(
            root,
            is_element(
                'a', {}, '',
                is_element('span', {'class': 'la-ref'}, '##h')))

        def mock_find_labeller(_: str):
            return None

        rr.resolve_refs(ElementTree.Element('div', id = 'theid'), mock_find_labeller)

        assert_that(
            root,
            is_element(
                'a', {}, '',
                is_element('span', {'class': 'la-ref'}, '##h')))

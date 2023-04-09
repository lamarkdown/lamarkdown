from lamarkdown.ext import util
import unittest
from hamcrest import *

import markdown

import re
from xml.etree import ElementTree


class UtilTestCase(unittest.TestCase):

    def test_set_attributes(self):

        regex = re.compile(rf'(?x){util.ATTR}')

        element = ElementTree.Element('span')
        util.set_attributes(element, None)
        assert_that(element.attrib, is_({}))

        for attr_str, attr in [
            (r'#theid',             {'id': 'theid'}),
            (r'.theclass',          {'class': 'theclass'}),
            (r'theattr=thevalue',   {'theattr': 'thevalue'}),
            (r'theattr="thevalue"', {'theattr': 'thevalue'}),
            (
                r'#theid theattr="thevalue" .theclass',
                {'id': 'theid', 'class': 'theclass', 'theattr': 'thevalue'}
            ),
        ]:
            element = ElementTree.Element('span')
            util.set_attributes(element, attr_str)
            assert_that(element.attrib, is_(attr))

            for prefix in ['', ':', ': ', ':  ']:
                element = ElementTree.Element('span')
                util.set_attributes(element, regex.match('{' + prefix + attr_str + '}'))
                assert_that(element.attrib, is_(attr))


    def test_strip_namespaces(self):
        xml = r'''
            <abc:x xmlns:abc="http://example.com">
                <y z="z-value" />
                <abc:y z="z-value" />
                <y abc:z="z-value" />
                <abc:y abc:z="z-value" />
            </abc:x>
        '''
        element = ElementTree.fromstring(xml)

        assert_that(element.tag, is_('{http://example.com}x'))
        assert_that(element[3].tag, is_('{http://example.com}y'))
        assert_that(element[3].attrib, is_({'{http://example.com}z': 'z-value'}))

        util.strip_namespaces(element)

        assert_that(element.tag, is_('x'))
        for i in range(4):
            assert_that(element[i].tag, is_('y'))
            assert_that(element[i].attrib, is_({'z': 'z-value'}))


    def test_opaque_tree(self):
        xml = '<x>text 1<y />text 2<z>text 3</z></x>'
        element = ElementTree.fromstring(xml)

        for actual, expected in [
            (element.text, 'text 1'),
            (element[0].tail, 'text 2'),
            (element[1].text, 'text 3'),
        ]:
            assert_that(
                actual,
                all_of(is_(expected), not_(instance_of(markdown.util.AtomicString))))

        util.opaque_tree(element)

        for actual, expected in [
            (element.text, 'text 1'),
            (element[0].tail, 'text 2'),
            (element[1].text, 'text 3'),
        ]:
            assert_that(
                actual,
                all_of(is_(expected), instance_of(markdown.util.AtomicString)))

        assert_that(element[0].text, none())
        assert_that(element[1].tail, none())

from lamarkdown.ext import util
import unittest
from hamcrest import *

import markdown

from xml.etree import ElementTree

class UtilTestCase(unittest.TestCase):

    def test_strip_namespaces(self):
        xml = '<abc:x xmlns:abc="http://example.com">text 1<abc:y abc:z="z-value" />text 2</abc:x>'
        element = ElementTree.fromstring(xml)

        assert_that(element.tag, is_('{http://example.com}x'))
        assert_that(element[0].tag, is_('{http://example.com}y'))
        assert_that(element[0].attrib, is_({'{http://example.com}z': 'z-value'}))

        util.strip_namespaces(element)

        assert_that(element.tag, is_('x'))
        assert_that(element[0].tag, is_('y'))
        assert_that(element[0].attrib, is_({'z': 'z-value'}))


    def test_opaque_tree(self):
        xml = '<abc:x xmlns:abc="http://example.com">text 1<abc:y abc:z="z-value" />text 2</abc:x>'
        element = ElementTree.fromstring(xml)

        assert_that(
            element.text,
            all_of(
                is_('text 1'),
                not_(instance_of(markdown.util.AtomicString))))
        assert_that(
            element[0].tail,
            all_of(
                is_('text 2'),
                not_(instance_of(markdown.util.AtomicString))))

        util.opaque_tree(element)

        assert_that(
            element.text,
            all_of(
                is_('text 1'),
                instance_of(markdown.util.AtomicString)))
        assert_that(
            element[0].tail,
            all_of(
                is_('text 2'),
                instance_of(markdown.util.AtomicString)))

from lamarkdown.lib import directives
from ..util.mock_progress import MockProgress

import unittest
from hamcrest import (assert_that, contains_exactly, contains_string, empty, has_properties, is_,
                      not_)
import lxml
import markdown
from textwrap import dedent


class DirectivesTestCase(unittest.TestCase):

    def test_conversion(self):
        '''
        Do short-form directives get converted to the long-form, where there are no clashes?
        '''

        md = markdown.Markdown(extensions = ['attr_list'])
        directives.init(md)

        tree = lxml.html.fromstring(md.convert(dedent(r'''
            para1
            {-mock-directive1 #p1}

            * item1
                {#i1 -mock-directive2="xyz"}
            * item2
                {-mock-directive3="def" md-mock-directive3="jhi" #i2}
            * item3
                {#i3}

            para2
            {#p2 -mock-directive4="abc" }
            ''')))

        assert_that(
            tree.xpath('.//*[@id="p1"][@md-mock-directive1="-mock-directive1"]'),
            not_(empty()))

        assert_that(
            tree.xpath('.//*[@id="i1"][@md-mock-directive2="xyz"]'),
            not_(empty()))

        assert_that(
            tree.xpath('.//*[@id="i2"][@md-mock-directive3="jhi"]'),
            not_(empty()))

        assert_that(
            tree.xpath('.//*[@id="p2"][@md-mock-directive4="abc"]'),
            not_(empty()))


    def test_immediate_retrieval(self):
        '''
        Can we retrieve directives within Python-Markdown's tree-processing stage?
        '''

        md = markdown.Markdown(extensions = ['attr_list'])
        progress = MockProgress()
        d = directives.Directives(progress)

        class TestTreeProcessor(markdown.treeprocessors.Treeprocessor):
            def run(self, root):
                self.ran = True
                assert_that(
                    d.pop_bool('mock-directive1', root.find('.//*[@id="p1"]'), 'TEST'),
                    is_(True))

                assert_that(
                    d.pop_bool('mock-directive2', root.find('.//*[@id="p2"]'), 'TEST'),
                    is_(True))

                assert_that(
                    d.pop('mock-directive3', root.find('.//*[@id="p3"]'), 'TEST'),
                    is_('abc'))

                assert_that(
                    d.pop('mock-directive4', root.find('.//*[@id="p4"]'), 'TEST'),
                    is_('def'))

                assert_that(progress.warning_messages, empty())


        proc = TestTreeProcessor()
        md.treeprocessors.register(proc, 'test-tree-processor', 0)
        md.convert(dedent(
            r'''
            para
            {-mock-directive1 #p1}

            para
            {md-mock-directive2 #p2}

            para
            {-mock-directive3="abc" #p3}

            para
            {md-mock-directive4="def" #p4}
            '''))

        self.assertTrue(proc.ran)


    def test_post_retrieval(self):
        '''
        Can we retrieve directives from a tree parsed by LXML, after Python-Markdown has finished?
        '''

        md = markdown.Markdown(extensions = ['attr_list'])
        directives.init(md)
        root = lxml.html.fromstring(md.convert(dedent(
            r'''
            para
            {-mock-directive1 #p1}

            para
            {md-mock-directive2 #p2}

            para
            {-mock-directive3="abc" #p3}

            para
            {md-mock-directive4="def" #p4}
            ''')))

        progress = MockProgress()
        d = directives.Directives(progress)

        assert_that(
            d.pop_bool('mock-directive1', root.find('.//*[@id="p1"]'), 'TEST'),
            is_(True))

        assert_that(
            d.pop_bool('mock-directive2', root.find('.//*[@id="p2"]'), 'TEST'),
            is_(True))

        assert_that(
            d.pop('mock-directive3', root.find('.//*[@id="p3"]'), 'TEST'),
            is_('abc'))

        assert_that(
            d.pop('mock-directive4', root.find('.//*[@id="p4"]'), 'TEST'),
            is_('def'))

        assert_that(progress.warning_messages, empty())


    def test_formatting(self):
        d = directives.Directives(MockProgress())
        assert_that(
            d.format('mock-directive'),
            is_('-mock-directive'))

        assert_that(
            d.format('mock-directive', 'abc'),
            is_('-mock-directive="abc"'))


    def test_warnings(self):
        '''
        Do we get warnings, as expected, for mis-specifying directives?
        '''

        md = markdown.Markdown(extensions = ['attr_list'])

        class TestTreeProcessor(markdown.treeprocessors.Treeprocessor):
            def run(self, root):
                self.ran = True

                progress = MockProgress()
                d = directives.Directives(progress)

                assert_that(
                    d.pop_bool('mock-directive1', root.find('.//*[@id="p1"]'), 'TEST'),
                    is_(True))

                assert_that(
                    progress.warning_messages,
                    contains_exactly(has_properties({
                        'location': 'TEST',
                        'msg': contains_string('expects no value')
                    })))

                progress = MockProgress()
                d = directives.Directives(progress)

                assert_that(
                    d.pop('mock-directive2', root.find('.//*[@id="p2"]'), 'TEST'),
                    is_('jhi'))

                assert_that(
                    progress.warning_messages,
                    contains_exactly(has_properties({
                        'location': 'TEST',
                        'msg': contains_string('Avoid writing both')
                    })))


        proc = TestTreeProcessor()
        md.treeprocessors.register(proc, 'test-tree-processor', 0)
        md.convert(dedent(
            r'''
            para
            {-mock-directive1="abc" #p1}

            para
            {md-mock-directive2="def" -mock-directive2="jhi" #p2}
            '''))

        self.assertTrue(proc.ran)

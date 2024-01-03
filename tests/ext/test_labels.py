from ..util import mock_progress, html_block_processor
import lamarkdown.ext

import unittest
from unittest.mock import Mock, patch
from hamcrest import *

import markdown
import lxml.html

import re
import sys
import tempfile
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']


HEADING_TESTDATA = r'''
    # Section 1
    ## Section 1.1
    ## Section 1.2
    ## Section 1.3
    # _Section_ 2
    ## **Section** 2.1
    ### Section 2.1.1
    #### Section 2.1.1.1
    ##### Section 2.1.1.1.1
    ###### Section 2.1.1.1.1.1
    ## Section 2.2
'''


ORDERED_LIST_TESTDATA = r'''
    1. ItemA
        1. ItemAA
        2. ItemAB
            1. ItemABA
    2. ItemB
        1. ItemBA
            1. ItemBAA
        2. ItemBB
    3. ItemC
    4. ItemD
'''

class LabelsTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text,
                           more_extensions = [],
                           expect_error = False,
                           # hook = lambda md: None,
                           **kwargs):
        # self.progress = mock_progress.MockProgress(expect_error = expect_error)
        md = markdown.Markdown(
            extensions = ['la.labels', *more_extensions],
            extension_configs = {'la.labels': {
                # 'progress': self.progress,
                **kwargs
            }}
        )
        # hook(md)
        return md.convert(dedent(markdown_text).strip())


    def test_default_headings(self):
        '''Check a simple tree of headings.'''

        html = self.run_markdown(HEADING_TESTDATA)

        self.assertRegex(
            html,
            fr'''(?xs)
            \s* <h1>Section[ ]1</h1>
            \s* <h2>Section[ ]1.1</h2>
            \s* <h2>Section[ ]1.2</h2>
            \s* <h2>Section[ ]1.3</h2>
            \s* <h1><em>Section</em>[ ]2</h1>
            \s* <h2><strong>Section</strong>[ ]2.1</h2>
            \s* <h3>Section[ ]2.1.1</h3>
            \s* <h4>Section[ ]2.1.1.1</h4>
            \s* <h5>Section[ ]2.1.1.1.1</h5>
            \s* <h6>Section[ ]2.1.1.1.1.1</h6>
            \s* <h2>Section[ ]2.2</h2>
            \s*
            '''
        )


    def test_headings_at_h1(self):
        '''Check a simple tree of headings.'''

        html = self.run_markdown(HEADING_TESTDATA, h_labels = "H.1 ,*")

        self.assertRegex(
            html,
            fr'''(?xs)
            \s* <h1><span[ ]class="la-label">1[ ]</span>Section[ ]1</h1>
            \s* <h2><span[ ]class="la-label">1.1[ ]</span>Section[ ]1.1</h2>
            \s* <h2><span[ ]class="la-label">1.2[ ]</span>Section[ ]1.2</h2>
            \s* <h2><span[ ]class="la-label">1.3[ ]</span>Section[ ]1.3</h2>
            \s* <h1><span[ ]class="la-label">2[ ]</span><em>Section</em>[ ]2</h1>
            \s* <h2><span[ ]class="la-label">2.1[ ]</span><strong>Section</strong>[ ]2.1</h2>
            \s* <h3><span[ ]class="la-label">2.1.1[ ]</span>Section[ ]2.1.1</h3>
            \s* <h4><span[ ]class="la-label">2.1.1.1[ ]</span>Section[ ]2.1.1.1</h4>
            \s* <h5><span[ ]class="la-label">2.1.1.1.1[ ]</span>Section[ ]2.1.1.1.1</h5>
            \s* <h6><span[ ]class="la-label">2.1.1.1.1.1[ ]</span>Section[ ]2.1.1.1.1.1</h6>
            \s* <h2><span[ ]class="la-label">2.2[ ]</span>Section[ ]2.2</h2>
            \s*
            '''
        )

    def test_headings_at_h2(self):
        '''Check a simple tree of headings.'''

        html = self.run_markdown(HEADING_TESTDATA, h_labels = "H.1 ,*", h_level = 2)

        self.assertRegex(
            html,
            fr'''(?xs)
            \s* <h1>Section[ ]1</h1>
            \s* <h2><span[ ]class="la-label">1[ ]</span>Section[ ]1.1</h2>
            \s* <h2><span[ ]class="la-label">2[ ]</span>Section[ ]1.2</h2>
            \s* <h2><span[ ]class="la-label">3[ ]</span>Section[ ]1.3</h2>
            \s* <h1><em>Section</em>[ ]2</h1>
            \s* <h2><span[ ]class="la-label">1[ ]</span><strong>Section</strong>[ ]2.1</h2>
            \s* <h3><span[ ]class="la-label">1.1[ ]</span>Section[ ]2.1.1</h3>
            \s* <h4><span[ ]class="la-label">1.1.1[ ]</span>Section[ ]2.1.1.1</h4>
            \s* <h5><span[ ]class="la-label">1.1.1.1[ ]</span>Section[ ]2.1.1.1.1</h5>
            \s* <h6><span[ ]class="la-label">1.1.1.1.1[ ]</span>Section[ ]2.1.1.1.1.1</h6>
            \s* <h2><span[ ]class="la-label">2[ ]</span>Section[ ]2.2</h2>
            \s*
            '''
        )


    def test_default_ordered_lists(self):
        html = self.run_markdown(ORDERED_LIST_TESTDATA)

        self.assertRegex(
            html,
            fr'''(?xs)
            \s* <ol>
            \s* <li>ItemA
            \s*     <ol>
            \s*         <li>ItemAA</li>
            \s*         <li>ItemAB
            \s*             <ol>
            \s*                 <li>ItemABA</li>
            \s*             </ol>
            \s*         </li>
            \s*     </ol>
            \s* </li>
            \s* <li>ItemB
            \s*     <ol>
            \s*         <li>ItemBA
            \s*             <ol>
            \s*                 <li>ItemBAA</li>
            \s*             </ol>
            \s*         </li>
            \s*         <li>ItemBB</li>
            \s*     </ol>
            \s* </li>
            \s* <li>ItemC</li>
            \s* <li>ItemD</li>
            \s* </ol>
            \s*
            ''')


    def test_ordered_lists(self):
        html = self.run_markdown(ORDERED_LIST_TESTDATA, ol_labels = 'L.1 ,*')

        self.assertRegex(
            html,
            fr'''(?xs)
            \s* <ol[ ]class="la-labelled">
            \s* <li><span[ ]class="la-label">1[ ]</span>ItemA
            \s*     <ol[ ]class="la-labelled">
            \s*         <li><span[ ]class="la-label">1.1[ ]</span>ItemAA</li>
            \s*         <li><span[ ]class="la-label">1.2[ ]</span>ItemAB
            \s*             <ol[ ]class="la-labelled">
            \s*                 <li><span[ ]class="la-label">1.2.1[ ]</span>ItemABA</li>
            \s*             </ol>
            \s*         </li>
            \s*     </ol>
            \s* </li>
            \s* <li><span[ ]class="la-label">2[ ]</span>ItemB
            \s*     <ol[ ]class="la-labelled">
            \s*         <li><span[ ]class="la-label">2.1[ ]</span>ItemBA
            \s*             <ol[ ]class="la-labelled">
            \s*                 <li><span[ ]class="la-label">2.1.1[ ]</span>ItemBAA</li>
            \s*             </ol>
            \s*         </li>
            \s*         <li><span[ ]class="la-label">2.2[ ]</span>ItemBB</li>
            \s*     </ol>
            \s* </li>
            \s* <li><span[ ]class="la-label">3[ ]</span>ItemC</li>
            \s* <li><span[ ]class="la-label">4[ ]</span>ItemD</li>
            \s* </ol>
            \s*
            ''')


    def test_extension_setup(self):
        import importlib
        import importlib.metadata

        module_name, class_name = importlib.metadata.entry_points(
            group = 'markdown.extensions')['la.labels'].value.split(':', 1)
        cls = importlib.import_module(module_name).__dict__[class_name]

        assert_that(
            cls,
            same_instance(lamarkdown.ext.labels.LabelsExtension))

        instance = lamarkdown.ext.labels.makeExtension(h_labels = 'mock_label_template')

        assert_that(
            instance,
            instance_of(lamarkdown.ext.labels.LabelsExtension))

        assert_that(
            instance.getConfig('h_labels'),
            is_('mock_label_template'))

        class MockBuildParams:
            def __getattr__(self, name):
                raise ModuleNotFoundError

        with patch('lamarkdown.lib.build_params.BuildParams', MockBuildParams()):
            instance = lamarkdown.ext.labels.makeExtension()

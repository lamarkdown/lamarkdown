from ..util.mock_progress import MockProgress
import unittest

import lamarkdown.ext
import markdown

import datetime
import re
import sys
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']

class EvalTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text, **kwargs):
        md = markdown.Markdown(
            extensions = ['la.eval'],
            extension_configs = {'la.eval':
            {
                'progress': MockProgress(),
                **kwargs
            }}
        )
        return md.convert(dedent(markdown_text).strip())


    def test_date(self):
        html = self.run_markdown(
            r'''
            Sometext $`date` sometext
            ''')

        self.assertRegex(
            html,
            fr'''(?x)
            <p>Sometext[ ]
            <span>
            {re.escape(str(datetime.date.today())).replace(' ', '[ ]')}
            </span>
            [ ]sometext</p>
            '''
        )

    def test_custom_replacement(self):
        html = self.run_markdown(
            r'''
            Sometext $`xyz` sometext
            ''',
            replace = {'xyz': 'test replacement'}
        )

        self.assertRegex(
            html,
            fr'''(?x)
            <p>Sometext[ ]
            <span>
            test[ ]replacement
            </span>
            [ ]sometext</p>
            '''
        )


    def test_code_eval(self):
        html = self.run_markdown(
            r'''
            Sometext $`111+222` sometext
            ''',
            allow_code = True
        )

        self.assertRegex(
            html,
            fr'''(?x)
            <p>Sometext[ ]
            <span>
            333
            </span>
            [ ]sometext</p>
            '''
        )


    def test_code_eval_disabled(self):
        html = self.run_markdown(
            r'''
            Sometext $`111+222` sometext
            ''',
            allow_code = False
        )

        self.assertNotIn('333', html)


    def test_delimiter(self):
        html = self.run_markdown(
            r'''
            Sometext $```'triple delimiter'``` sometext
            ''',
            allow_code = True
        )

        self.assertIn('triple delimiter', html)


    def test_alt_delimiter(self):
        html = self.run_markdown(
            r'''
            Sometext #///'alt delimiter'///& sometext
            ''',
            allow_code = True,
            start = '#',
            end = '&',
            delimiter = '/'
        )

        self.assertIn('alt delimiter', html)

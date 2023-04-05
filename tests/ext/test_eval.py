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

    def run_markdown(self, markdown_text, expect_error = False, **kwargs):
        md = markdown.Markdown(
            extensions = ['la.eval'],
            extension_configs = {'la.eval':
            {
                'progress': MockProgress(expect_error),
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
        for replace in [
            {'xyz': 'test replacement'},
            {'xyz': lambda: 'test replacement'}
        ]:
            html = self.run_markdown(
                r'''
                Sometext $`xyz` sometext
                ''',
                replace = replace
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
            allow_exec = True
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
            expect_error = True,
            allow_exec = False
        )

        self.assertNotIn('333', html)


    def test_delimiter(self):
        html = self.run_markdown(
            r'''
            Sometext $```'triple delimiter'``` sometext
            ''',
            allow_exec = True
        )

        self.assertIn('triple delimiter', html)


    # def test_alt_delimiter(self):
    #     html = self.run_markdown(
    #         r'''
    #         Sometext #///'alt delimiter'///& sometext
    #         ''',
    #         allow_exec = True,
    #         start = '#',
    #         end = '&',
    #         delimiter = '/'
    #     )
    #
    #     self.assertIn('alt delimiter', html)

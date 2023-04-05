from ..util.mock_progress import MockProgress
import unittest
from unittest.mock import patch
from hamcrest import *

import lamarkdown.ext
import markdown

import datetime
import re
import sys
from textwrap import dedent

sys.modules['la'] = sys.modules['lamarkdown.ext']

class EvalTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text, expect_error = False, **kwargs):
        self.progress = MockProgress(expect_error)
        md = markdown.Markdown(
            extensions = ['la.eval'],
            extension_configs = {'la.eval':
            {
                'progress': self.progress,
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

    def test_repl_error(self):
        def error_fn(): raise Exception

        html = self.run_markdown(
            r'''
            Sometext $`xyz` sometext
            ''',
            replace = {'xyz': error_fn},
            expect_error = True
        )

        assert_that(
            self.progress.error_messages,
            contains_exactly(has_property('location', 'la.eval')))


    def test_eval_error(self):
        html = self.run_markdown(
            r'''
            Sometext $`[][0]` sometext
            ''',
            allow_exec = True,
            expect_error = True
        )

        assert_that(
            self.progress.error_messages,
            contains_exactly(has_property('location', 'la.eval')))


    def test_extension_setup(self):
        import importlib
        import importlib.metadata

        module_name, class_name = importlib.metadata.entry_points(
            group = 'markdown.extensions')['la.eval'].value.split(':', 1)
        cls = importlib.import_module(module_name).__dict__[class_name]

        assert_that(
            cls,
            same_instance(lamarkdown.ext.eval.EvalExtension))

        instance = lamarkdown.ext.eval.makeExtension(replace = {'mock': 'replacement'})

        assert_that(
            instance,
            instance_of(lamarkdown.ext.eval.EvalExtension))

        assert_that(
            instance.getConfig('replace'),
            is_({'mock': 'replacement'}))

        class MockBuildParams:
            def __getattr__(self, name):
                raise ModuleNotFoundError

        with patch('lamarkdown.lib.build_params.BuildParams', MockBuildParams()):
            instance = lamarkdown.ext.eval.makeExtension()

from lamarkdown.ext.label_support.label_templates import *
from lamarkdown.ext.label_support.counter_types import *
import unittest
from hamcrest import *


class LabelTemplatesTestCase(unittest.TestCase):

    def test_parse(self):
        parser = LabelTemplateParser()

        for (template_str, expected_template) in [
            ('(',   LabelTemplate(prefix = '(',
                                  separator = '',
                                  suffix = '',
                                  parent_type = None,
                                  counter_type = None,
                                  child_template = None)),
            ('(a)', LabelTemplate(prefix = '(',
                                  separator = '',
                                  suffix = ')',
                                  parent_type = None,
                                  counter_type = get_counter_type('a'),
                                  child_template = None))
        ]:
            assert_that(expected_template, equal_to(parser.parse(template_str)))


    def test_parse_error(self):
        parser = LabelTemplateParser()

        for template_str in ['invalid-counter', 'a.a', 'X.a.a']:
            try:
                template = parser.parse(template_str)
                self.fail(f'Parsing "{template_str}" should have raised LabelTemplateException, but produced template "{template}" instead')
            except LabelTemplateException:
                pass

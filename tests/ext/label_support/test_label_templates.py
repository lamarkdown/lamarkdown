from lamarkdown.ext.label_support.label_templates import *
from lamarkdown.ext.label_support.counter_types import *
import unittest
from hamcrest import *


class LabelTemplatesTestCase(unittest.TestCase):

    def test_parse(self):
        parser = LabelTemplateParser()

        def template(pre, sep, suf, ctype, ptype, inner):
            return LabelTemplate(prefix = pre, separator = sep, suffix = suf,
                                 counter_type = ctype, parent_type = ptype, inner_template = inner)

        for (template_str, expected_template) in [
            # Basic templates
            ('(',       template('(',   '',  '',  None,                  None, None)),
            ('(a',      template('(',   '',  '',  get_counter_type('a'), None, None)),
            ('a)',      template('',    '',  ')', get_counter_type('a'), None, None)),
            ('(a)',     template('(',   '',  ')', get_counter_type('a'), None, None)),

            # Parent counter specification
            ('(X.a)',   template('(',   '.', ')', get_counter_type('a'), '',   None)),
            ('X.a',     template('',    '.', '',  get_counter_type('a'), '',   None)),
            ('(H.a)',   template('(',   '.', ')', get_counter_type('a'), 'h',  None)),
            ('(H3.a)',  template('(',   '.', ')', get_counter_type('a'), 'h3', None)),
            ('(L.a)',   template('(',   '.', ')', get_counter_type('a'), 'ol', None)),

            # Handling of '-' (allowed as an internal character within counter names)
            ('-X-lower-alpha-', template('-', '-', '-', get_counter_type('lower-alpha'), '', None)),

            # Quoted literals
            ('"(a)"',         template('(a)',       '', '',    None,                  None, None)),
            ("'(a)'",         template('(a)',       '', '',    None,                  None, None)),
            ('"(a,""b,""c)"', template('(a,"b,"c)', '', '',    None,                  None, None)),
            ("'(d,''e,''f)'", template("(d,'e,'f)", '', '',    None,                  None, None)),

            ('a"a"',          template('',       '',    'a',   get_counter_type('a'), None, None)),
            ('a."a".',        template('',       '',    '.a.', get_counter_type('a'), None, None)),
            ('X"a"a',         template('',       'a',   '',    get_counter_type('a'), '',   None)),
            ('X."a".a',       template('',       '.a.', '',    get_counter_type('a'), '',   None)),

            # Inner templates
            ('(a),[1]',             template('(', '', ')',  get_counter_type('a'), None,
                                        template('[', '', ']', get_counter_type('1'), None,
                                            None))),

            ('(H.a),[L:1],{X;i}',   template('(', '.', ')',  get_counter_type('a'), 'h',
                                        template('[', ':', ']', get_counter_type('1'), 'ol',
                                            template('{', ';', '}', get_counter_type('i'), '',
                                                None)))),
        ]:
            assert_that(parser.parse(template_str),
                        equal_to(expected_template),
                        f'Parsing template "{template_str}"')


    def test_parse_inner_wildcard(self):
        parser = LabelTemplateParser()

        for template_str in ['a,*', '(1),*', 'X.i,*']:
            template = parser.parse(template_str)
            assert_that(template.inner_template, same_instance(template))

        template = parser.parse('a,(1),X.i,*')
        assert_that(template.inner_template.inner_template.inner_template,
                    same_instance(template.inner_template.inner_template))


    def test_parse_error(self):
        parser = LabelTemplateParser()

        for template_str in ['invalid-counter', 'a.a', 'X.a.a', 'a"']:
            try:
                template = parser.parse(template_str)
                self.fail(f'Parsing "{template_str}" should have raised LabelTemplateException, but produced template "{template}" instead')
            except LabelTemplateException:
                pass

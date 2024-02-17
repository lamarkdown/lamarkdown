from lamarkdown.ext.label_support.label_templates import (LabelTemplate, LabelTemplateParser,
                                                          LabelTemplateException)
from lamarkdown.ext.label_support.standard_counter_types import get_counter_type
import unittest
from hamcrest import assert_that, equal_to, same_instance


class LabelTemplatesTestCase(unittest.TestCase):

    def test_parse(self):
        parser = LabelTemplateParser()

        def template(pre, sep, suf, ct, ptype, inner):
            return LabelTemplate(prefix = pre,
                                 separator = sep,
                                 suffix = suf,
                                 counter_type = get_counter_type(ct) if ct else None,
                                 parent_type = ptype,
                                 inner_template = inner)

        for (template_str, expected_template) in [
            # Basic templates
            ('(',       template('(',   '',  '',  None, None, None)),
            ('(a',      template('(',   '',  '',  'a',  None, None)),
            ('a)',      template('',    '',  ')', 'a',  None, None)),
            ('(a)',     template('(',   '',  ')', 'a',  None, None)),

            # Parent counter specification
            ('(X.a)',   template('(',   '.', ')', 'a', '',   None)),
            ('X.a',     template('',    '.', '',  'a', '',   None)),
            ('(H.a)',   template('(',   '.', ')', 'a', 'h',  None)),
            ('(H3.a)',  template('(',   '.', ')', 'a', 'h3', None)),
            ('(L.a)',   template('(',   '.', ')', 'a', 'ol', None)),

            # Multicharacter counter names and handling of internal '-'
            ('octal',      template('',  '',  '',   'octal', None, None)),
            ('(octal)',    template('(', '',  ')',  'octal', None, None)),
            ('X-octal',    template('',  '-', '',   'octal', '',   None)),
            ('(X-octal)',  template('(', '-', ')',  'octal', '',   None)),

            # Counter names that happen to start with a valid parent specifier
            ('hebrew',     template('', '', '',    'hebrew', None, None)),
            ('-H-hebrew-', template('-', '-', '-', 'hebrew', 'h',  None)),
            ('lao',        template('', '', '',    'lao',    None, None)),
            ('-L-lao-',    template('-', '-', '-', 'lao',    'ol', None)),

            # Handling of internal '-' (part of the counter-name)
            ('lower-alpha',     template('',  '',  '',  'lower-alpha', None, None)),
            ('-X-lower-alpha-', template('-', '-', '-', 'lower-alpha', '',   None)),

            # Quoted literals
            ('"(a)"',         template('(a)',       '', '',    None, None, None)),
            ("'(a)'",         template('(a)',       '', '',    None, None, None)),
            ('"(a,""b,""c)"', template('(a,"b,"c)', '', '',    None, None, None)),
            ("'(d,''e,''f)'", template("(d,'e,'f)", '', '',    None, None, None)),

            ('a"a"',          template('',       '',    'a',   'a',  None, None)),
            ('a."a".',        template('',       '',    '.a.', 'a',  None, None)),
            ('X"a"a',         template('',       'a',   '',    'a',  '',   None)),
            ('X."a".a',       template('',       '.a.', '',    'a',  '',   None)),

            # Inner templates
            ('(a),[1]',
                template('(', '', ')', 'a', None,
                         template('[', '', ']', '1', None,
                                  None))),

            ('(H.a),[L:1],{X;i}',
                template('(', '.', ')', 'a', 'h',
                         template('[', ':', ']', '1', 'ol',
                                  template('{', ';', '}', 'i', '',
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
                self.fail(f'Parsing "{template_str}" should have raised LabelTemplateException, '
                          f'but produced template "{template}" instead')
            except LabelTemplateException:
                pass

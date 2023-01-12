from ..util.mock_progress import MockProgress
from lamarkdown.lib import md_compiler, build_params

import unittest
from hamcrest import *

import markdown
import lxml
import cssutils

import os
import tempfile
from textwrap import dedent


class MdCompilerTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_dir_context = tempfile.TemporaryDirectory()
        self.tmp_dir = self.tmp_dir_context.__enter__()
        self.html_file = os.path.join(self.tmp_dir, 'testdoc.html')

        self.html_parser = lxml.html.HTMLParser(
            recover = False,    # Don't accept broken HTML
            no_network = True,  # Don't load remote resources
        )
        self.css_parser = cssutils.CSSParser(
            parseComments = False,
            validate = True
        )


    def tearDown(self):
        self.tmp_dir_context.__exit__(None, None, None)


    def set_results(self, html_file):
        # Parse with lxml to ensure that the output is well formed, and to allow it to be queried
        # with XPath expressions.
        self.root = lxml.html.parse(html_file, self.html_parser)

        # Now find and parse the CSS code, if any:
        self.css_sheets = [self.css_parser.parseString(elem.text) for elem in self.root.xpath('/html/head/style')]

        self.full_html = lxml.html.tostring(self.root, with_tail = False, encoding = 'unicode')

        # We probably want to just check the whole <body> element at once though.
        self.body_html = lxml.html.tostring(self.root.find('body'), with_tail = False, encoding = 'unicode')


    def run_md_compiler(self, markdown = '', build = None, build_defaults = True, is_live = False):
        doc_file   = os.path.join(self.tmp_dir, 'testdoc.md')
        build_file = os.path.join(self.tmp_dir, 'testbuild.py')
        build_dir  = os.path.join(self.tmp_dir, 'build')

        with open(doc_file, 'w') as writer:
            writer.write(dedent(markdown))

        if build is not None:
            with open(build_file, 'w') as writer:
                 writer.write(dedent(build))

        bp = build_params.BuildParams(
            src_file = doc_file,
            target_file = self.html_file,
            build_files = [build_file] if build else [],
            build_dir = build_dir,
            build_defaults = build_defaults,
            cache = {},
            progress = MockProgress(),
            is_live = is_live
        )

        md_compiler.compile(bp)
        self.set_results(self.html_file)


    def test_basic(self):
        self.run_md_compiler(
            r'''
            # Heading

            Paragraph1
            ''',
            build_defaults = False)

        # The meta charset declaration should be there as a matter of course.
        assert_that(
            self.root.xpath('/html/head/meta[@charset="utf-8"]'),
            contains_exactly(instance_of(lxml.html.HtmlElement)))

        # The title should be taken from the <h1> element.
        assert_that(
            self.root.xpath('/html/head/title')[0].text,
            is_('Heading'))

        # Check the document structure.
        assert_that(
            self.body_html,
            matches_regexp(
                r'''(?x)
                \s* <body>
                \s* <h1> Heading </h1>
                \s* <p> Paragraph1 </p>
                \s* </body>
                \s*
                '''
            )
        )


    def test_css(self):
        self.run_md_compiler(
            markdown =  r'''
                # Heading

                Paragraph1
                ''',
            build = r'''
                import lamarkdown as la
                la.css(r"h1 { background: blue; font-weight: bold; }")
                la.css(r"h2 { background: green; }")

                # Testing selectors: 'h3' should not match (there's no '### Sub-sub-heading' in the
                # markdown document), but 'h1' should. Note: we're testing the 'if_selector' parameter.
                # The 'h3' at the start of the CSS is irrelevant to our test.

                la.css(r"h3 { background: yellow; }",  if_selectors = ["h3"])
                la.css(r"h3 { background: yellow; }",  if_selectors = "h3")
                la.css(r"h3 { background: magenta; }", if_selectors = ["h3", "h1"])

                # Testing XPaths: "//h5" should not match, but "//h1" should.

                la.css(r"h4 { background: yellow; }",  if_xpaths = ["//h5"])
                la.css(r"h4 { background: yellow; }",  if_xpaths = "//h5")
                la.css(r"h4 { background: orange; }",  if_xpaths = ["//h5", "//h1"])

                # Testing rule creation with pre-selected selectors. "li" and "span" don't match, but
                # "p" does.

                la.css_rule(["li", "p", "span"], r"color: red")
                ''',
            build_defaults = False
        )

        expected_css = self.css_parser.parseString(
            r'''
            h1 {
                background: blue;
                font-weight: bold;
            }
            h2 { background: green; }
            h3 { background: magenta; }
            h4 { background: orange; }
            p {
                color: red;
            }
            ''')

        assert_that(
            [s.cssText for s in self.css_sheets],
            contains_exactly(expected_css.cssText)
        )


    def test_js(self):
        self.run_md_compiler(
            markdown = r'''
                # Heading

                Paragraph1
                ''',
            build = r'''
                import lamarkdown as la
                la.js(r"console.log('a')")
                la.js(r"console.log('b')")
                la.js(r"console.log('c')", if_selectors = ["h3"])
                la.js(r"console.log('d')", if_selectors = ["h3", "h1"])
                la.js(r"console.log('e')", if_xpaths = "//h5")
                la.js(r"console.log('f')", if_xpaths = ["//h5", "//h1"])
                ''',
            build_defaults = False
        )

        expected_js = dedent(r'''
            console.log('a')
            console.log('b')
            console.log('d')
            console.log('f')
        ''')

        assert_that(
            self.root.xpath('/html/body/script')[0].text.strip(),
            is_(expected_js.strip()))


    def test_variants(self):
        '''Checks whether we can compile variant documents, and in particular tests these API
        functions: variants(), base_name(), name(), target() and prune().'''

        self.run_md_compiler(
            markdown = r'''
                # Heading

                Paragraph1

                Paragraph2
                ''',
            build = r'''
                import lamarkdown as la
                def variant_a():
                    la.base_name()

                def variant_b():
                    la.name("variant_b1")

                def variant_c():
                    la.target(lambda original: original + ".variant_c1.html")

                def variant_d():
                    def d1():
                        la.css(r"h1 { color: red; }")

                    def d2():
                        la.css(r"h1 { color: blue; }")

                    la.variants(d1, d2)
                    la.css(r"h1 { color: red; }")

                def variant_e():
                    la.prune("p")

                def variant_f():
                    la.prune("h1")

                la.variants(variant_a, variant_b, variant_c, variant_d, variant_e, variant_f)
            ''',
            build_defaults = False
        )

        def for_(f):
            self.set_results(os.path.join(self.tmp_dir, f + '.html'))

        def exists():
            assert_that(self.root.xpath('/html/body/h1')[0].text, is_('Heading'))

        # Check variant A, which should have the default name.
        exists()

        # Check variant B, where we pick a custom variant name (target suffix).
        for_('testdoc_variant_b1')
        exists()

        # Check variant C, where we pick a different target name, based on the original name,
        # using a function.
        for_('testdoc.html.variant_c1')
        exists()

        # Check sub-variants D1 and D2:
        for_('testdoc_variant_d_d1')
        assert_that(self.css_sheets[0].cssText.decode(), contains_string('color: red'))

        for_('testdoc_variant_d_d2')
        assert_that(self.css_sheets[0].cssText.decode(), contains_string('color: blue'))

        # Check variant E, which should be missing its 'p' elements:
        for_('testdoc_variant_e')
        assert_that(self.root.xpath('/html/body/h1'), not_(empty()))
        assert_that(self.root.xpath('/html/body/p'),  is_(empty()))

        # Check variant F, which should be missing its 'h1' element:
        for_('testdoc_variant_f')
        assert_that(self.root.xpath('/html/body/h1'), is_(empty()))
        assert_that(self.root.xpath('/html/body/p'),  not_(empty()))


    def test_tree_queries(self):
        self.run_md_compiler(
            markdown = r'''
                # Heading1

                Paragraph1

                # Heading2

                Paragraph2
                ''',
            build = r'''
                import lamarkdown as la
                import lxml.etree

                def for_each_h1(element):
                    element.text += " h1"

                def for_each_p(element):
                    element.text += " p"

                def modify_tree(root):
                    lxml.etree.SubElement(root, "div", attrib={"id": "test"})

                la.with_selector("h1", for_each_h1)
                la.with_xpath("//p", for_each_p)
                la.with_tree(modify_tree)
            ''',
            build_defaults = False
        )

        assert_that(
            [elem.text for elem in self.root.xpath('//h1')],
            contains_exactly('Heading1 h1', 'Heading2 h1'))

        assert_that(
            [elem.text for elem in self.root.xpath('//p')],
            contains_exactly('Paragraph1 p', 'Paragraph2 p'))

        assert_that(
            self.root.xpath('//div')[0].attrib,
            is_({'id': 'test'}))

    # API functions:
    # ---
    #def get_build_dir():
    #def get_env():
    #def get_params():
    #def extensions(*extensions: Union[str,Extension]):
    #def extension(extension: Union[str,Extension], cfg_dict = {}, **cfg_kwargs):
    #def css_files(*url_list: List[str], **kwargs):
    #def js_files(*url_list: List[str], **kwargs):
    #def wrap_content(start: str, end: str):
    #def wrap_content_inner(start: str, end: str):
    #def embed_resources(embed: Optional[bool] = True):
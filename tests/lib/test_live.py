from ..util.mock_progress import MockProgress
from ..util.mock_cache import MockCache
from lamarkdown.lib import build_params, live, md_compiler

import unittest
from unittest.mock import Mock, patch

from hamcrest import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import os
import tempfile
from textwrap import dedent
import threading
import time
import urllib.request



class LiveTestCase(unittest.TestCase):

    def setUp(self):
        browser_opts = webdriver.firefox.options.Options()
        browser_opts.add_argument('--headless')
        self.browser = webdriver.Firefox(options = browser_opts)
        self.update_n = 0

    def tearDown(self):
        # self.updater.shutdown()
        self.browser.quit()
        pass


    def find_attr(self, selector, attr):
        return [elem.get_attribute(attr)
                for elem in self.browser.find_elements(By.CSS_SELECTOR, selector)]


    def wait_for_update(self, msg, timeout_secs = 2):
        self.update_n += 1

        try:
            WebDriverWait(self.browser, timeout_secs).until(
                EC.text_to_be_present_in_element_attribute(
                    (By.CSS_SELECTOR, f'#{live.CONTROL_PANEL_ID}'),
                    'data-update-n',
                    str(self.update_n)))
        except TimeoutException as e:
            raise AssertionError(
                f'Timeout - document not refreshed after {timeout_secs} seconds: {msg}') from e


    @patch('lamarkdown.lib.resources.read_url')
    def test_watch_live(self, mock_read_url):
        mock_read_url.return_value = (False, b'', None)

        with tempfile.TemporaryDirectory() as dir:
            os.chdir(dir)
            with open('doc.md', 'w') as f:
                f.write(dedent('''
                    # Doc Heading

                    Paragraph 1
                    {.class1}

                    Paragraph 2
                    {.class2}
                '''))

            with open('build_a.py', 'w') as f:
                f.write(dedent('''
                    import lamarkdown as la
                    la('attr_list')
                '''))

            extra_file_a = os.path.join('subdir_a', 'extra_a.txt')
            extra_file_b = os.path.join('subdir_b', 'extra_b.txt')
            extra_file_c = os.path.join('subdir_c', 'extra_c.txt')

            os.mkdir('subdir_a')
            os.mkdir('subdir_b')
            with open(extra_file_a, 'w') as f:
                f.write('A')


            cache = MockCache()
            base_build_params = build_params.BuildParams(
                src_file = 'doc.md',
                target_file = 'doc.html',
                build_files = ['build_a.py', 'build_b.py'],
                build_dir = 'build',
                build_defaults = True,
                cache = cache,
                progress = MockProgress(),
                is_live = True,
                allow_exec_cmdline = False,
                live_update_deps = {extra_file_a, extra_file_b, extra_file_c}
            )
            complete_build_params = md_compiler.compile(base_build_params)

            updater = live.LiveUpdater(base_build_params, complete_build_params)

            threading.Thread(
                target = lambda: updater.run(address = '127.0.0.1',
                                             port_range = range(14100, 14101),
                                             launch_browser = False),
            ).start()

            try:
                # The server needs a bit of time to start up (asynchronously) before we query it.
                # But the browser (selenium) will almost certainly take longer anyway.

                self.browser.get('http://127.0.0.1:14100')

                assert_that(self.find_attr('title', 'textContent'), contains_exactly('Doc Heading'))
                assert_that(self.find_attr('h1', 'textContent'),    contains_exactly('Doc Heading'))
                assert_that(
                    self.find_attr('p', 'textContent'),
                    contains_exactly('Paragraph 1', 'Paragraph 2')
                )
                assert_that(self.find_attr(f'#{live.CONTROL_PANEL_ID}', 'data-update-n'), '0')


                # Test dependencies
                # -----------------

                with open('doc.md', 'w') as f:
                    f.write(dedent('''
                        # Doc Heading B

                        Paragraph 1
                        {.class1}

                        Paragraph 2
                        {.class2}
                    '''))

                self.wait_for_update('Modified doc.md')
                assert_that(self.find_attr('title', 'textContent'), contains_exactly('Doc Heading B'))
                assert_that(self.find_attr('h1',    'textContent'), contains_exactly('Doc Heading B'))

                with open('build_a.py', 'w') as f:
                    f.write(dedent('''
                        import lamarkdown as la
                        la('attr_list')
                        la.prune('.class1')
                    '''))

                self.wait_for_update('Modified build_a.py')
                assert_that(self.find_attr('p', 'textContent'), contains_exactly('Paragraph 2'))

                with open('build_b.py', 'w') as f:
                    f.write(dedent('''
                        import lamarkdown as la
                        la('attr_list')
                        la.with_html(lambda html: html + '<p>Paragraph 3</p>')
                    '''))

                self.wait_for_update('Added new build_b.py')
                assert_that(self.find_attr('p', 'textContent'), contains_exactly('Paragraph 2',
                                                                                 'Paragraph 3'))

                os.remove('build_a.py')
                self.wait_for_update('Deleted build_a.py')
                assert_that(self.find_attr('p', 'textContent'), contains_exactly('Paragraph 1',
                                                                                 'Paragraph 2',
                                                                                 'Paragraph 3'))

                with open('build_a.py', 'w') as f:
                    f.write(dedent('''
                        import lamarkdown as la
                        la('attr_list')
                    '''))
                self.wait_for_update('Added new build_a.py')
                assert_that(self.find_attr('p', 'textContent'), contains_exactly('Paragraph 1',
                                                                                 'Paragraph 2',
                                                                                 'Paragraph 3'))

                os.remove('build_b.py')
                self.wait_for_update('Deleted build_b.py')
                assert_that(self.find_attr('p', 'textContent'), contains_exactly('Paragraph 1',
                                                                                 'Paragraph 2'))

                # Modifying/creating extra dependency files

                with open(extra_file_a, 'w') as f:
                    f.write('AA')

                self.wait_for_update(f'Modified {extra_file_a}')

                with open(extra_file_b, 'w') as f:
                    f.write('BB')

                self.wait_for_update(f'Added new {extra_file_b}')

                os.mkdir('subdir_c')
                with open(extra_file_c, 'w') as f:
                    f.write('CC')

                self.wait_for_update(f'Added new {extra_file_c} (including directory creation)')

                # Moving files and directories

                os.rename(extra_file_a, extra_file_a + '1')
                self.wait_for_update(f'Renamed {extra_file_a} to {extra_file_a}1')

                os.rename(extra_file_b, os.path.join('subdir_a', 'extra_b.txt'))
                self.wait_for_update(f'Moved {extra_file_b} to subdir_a/ (monitored)')

                os.mkdir('subdir_d')
                os.rename(extra_file_c, os.path.join('subdir_d', 'extra_c.txt'))
                self.wait_for_update(f'Moved {extra_file_c} to subdir_d/ (unmonitored)')

                # Restore one of the files, so we can see what happens when we rename the whole
                # parent directory
                with open(extra_file_a, 'w') as f:
                    f.write('AA')
                self.wait_for_update(f'Restored {extra_file_a}')
                os.rename('subdir_a', 'subdir_a1')
                self.wait_for_update(f'Renamed subdir_a/ to subdir_a1/')


                # Test variants
                # -------------

                with open('build_a.py', 'w') as f:
                    f.write(dedent('''
                        import lamarkdown as la
                        la('attr_list')

                        def VariantA(): la.prune('.class2')
                        def VariantB(): la.prune('.class1')

                        la.variants(VariantA, VariantB)
                    '''))


                self.wait_for_update('Modified build_a.py to specify VariantA and VariantB')

                urls = self.find_attr(f'#{live.CONTROL_PANEL_ID} a', 'href')
                assert_that(
                    urls,
                    contains_exactly('http://127.0.0.1:14100/VariantA/index.html',
                                     'http://127.0.0.1:14100/VariantB/index.html')
                )

                self.browser.get(urls[0])
                assert_that(self.find_attr(f'#{live.CONTROL_PANEL_ID} a', 'href'), equal_to(urls))
                assert_that(self.find_attr('p', 'textContent'), contains_exactly('Paragraph 1'))

                self.browser.get(urls[1])
                assert_that(self.find_attr(f'#{live.CONTROL_PANEL_ID} a', 'href'), equal_to(urls))
                assert_that(self.find_attr('p', 'textContent'), contains_exactly('Paragraph 2'))

                with open('build_a.py', 'w') as f:
                    f.write(dedent('''
                        import lamarkdown as la
                        la('attr_list')

                        def VariantA1(): la.with_html(lambda html: html + '<div id="x">A1</div>')
                        def VariantA2(): la.with_html(lambda html: html + '<div id="x">A2</div>')
                        def VariantB1(): la.with_html(lambda html: html + '<div id="x">B1</div>')
                        def VariantB2(): la.with_html(lambda html: html + '<div id="x">B2</div>')
                        def VariantA(): la.variants(VariantA1, VariantA2)
                        def VariantB(): la.variants(VariantB1, VariantB2)

                        la.variants(VariantA, VariantB)
                    '''))

                self.wait_for_update(
                    'Modified build_a.py to specify variants A and B, with sub-variants A1, A2, B1 and B2')

                urls = self.find_attr(f'#{live.CONTROL_PANEL_ID} a', 'href')
                assert_that(
                    urls,
                    contains_exactly('http://127.0.0.1:14100/VariantA1/index.html',
                                     'http://127.0.0.1:14100/VariantA2/index.html',
                                     'http://127.0.0.1:14100/VariantB1/index.html',
                                     'http://127.0.0.1:14100/VariantB2/index.html')
                )

                for i, name in enumerate(['A1', 'A2', 'B1', 'B2']):
                    self.browser.get(urls[i])
                    assert_that(self.find_attr('div#x', 'textContent'), contains_exactly(name))

                with open('build_a.py', 'w') as f:
                    f.write(dedent('''
                        import lamarkdown as la
                        la('attr_list')
                    '''))

                self.wait_for_update('Modified build_a.py to revert to no variants')
                assert_that(self.find_attr(f'#{live.CONTROL_PANEL_ID} a', 'href'), empty())
                assert_that(self.find_attr('p', 'textContent'), contains_exactly('Paragraph 1',
                                                                                 'Paragraph 2'))
                assert_that(self.find_attr('div#x', 'textContent'), empty())


                # Clean builds
                # ------------

                cache['mock_key'] = 'mock_value'
                self.browser.find_element(By.CSS_SELECTOR,
                                          f'#{live.CONTROL_PANEL_CLEAN_BUTTON_ID}').click()
                self.wait_for_update('Clean build')
                assert_that(cache, is_not(has_key('mock_key')))

            finally:
                updater.shutdown()


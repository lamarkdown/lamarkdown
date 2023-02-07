from ..util.mock_progress import MockProgress
from lamarkdown.lib import fenced_blocks, build_params

import unittest
from unittest.mock import Mock, PropertyMock

# from xml.etree import ElementTree

class FencedBlocksTestCase(unittest.TestCase):

    def test_command_formatter(self):
        # It's a safe-ish bet that 'python3' is installed on the test machine.
        fmt = fenced_blocks.command_formatter(
            Mock(),
            ['python3', '-c', r'text = input() ; print(f"<div>{text}</div>")']
        )

        output = fmt('Hello', 'mock-lang', 'mock-class', {}, None).strip()
        self.assertEqual('<div>Hello</div>', output)


    def test_caching_formatter(self):
        mock_formatter = Mock()
        mock_formatter.return_value = '<div>Hello</div>'

        mock_build_params = Mock()
        type(mock_build_params).cache = PropertyMock(return_value = {}) # Trivial 'cache'

        fmt = fenced_blocks.caching_formatter(mock_build_params, 'mock', mock_formatter)

        for source, language, css_class, options in [
            ('text1', 'lang1', 'class1', {'op': 1}),
            ('text1', 'lang1', 'class1', {'op': 1}),

            ('text1', 'lang1', 'class1', {'op': 2}),
            ('text1', 'lang1', 'class2', {'op': 1}),
            ('text1', 'lang2', 'class1', {'op': 1}),
            ('text2', 'lang1', 'class1', {'op': 1}),

            ('text2', 'lang2', 'class2', {'op': 2}),
            ('text2', 'lang2', 'class2', {'op': 2}),
        ]:
            result = fmt(source, language, css_class, options, None).strip()
            self.assertEqual('<div>Hello</div>', result)

        mock_formatter.assert_any_call('text1', 'lang1', 'class1', {'op': 1}, None)
        mock_formatter.assert_any_call('text1', 'lang1', 'class1', {'op': 2}, None)
        mock_formatter.assert_any_call('text1', 'lang1', 'class2', {'op': 1}, None)
        mock_formatter.assert_any_call('text1', 'lang2', 'class1', {'op': 1}, None)
        mock_formatter.assert_any_call('text2', 'lang1', 'class1', {'op': 1}, None)
        mock_formatter.assert_any_call('text2', 'lang2', 'class2', {'op': 2}, None)
        self.assertEqual(6, mock_formatter.call_count)


    def test_exec_formatter(self):
        mock_build_params = Mock()
        # TODO

    def test_attr_formatter(self):
        pass
        # TODO

    def test_matplotlib_formatter(self):
        mock_build_params = Mock()
        # TODO

    def test_r_plot_formatter(self):
        mock_build_params = Mock()
        # TODO


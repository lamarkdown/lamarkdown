from lamarkdown.lib.build_params import BuildParams
from ..util.mock_cache import MockCache
from ..util.mock_progress import MockProgress
import unittest

from lamarkdown import *  # noqa: F403


class ApiImplTestCase(unittest.TestCase):

    def test_wildcard_import(self):

        BuildParams(
            src_file = 'mock_src.md',
            target_file = 'mock_target.html',
            build_files = [],
            build_dir = 'mock_dir',
            build_defaults = False,
            build_cache = MockCache(),
            fetch_cache = MockCache(),
            progress = MockProgress(),
            is_live = False,
            allow_exec_cmdline = False
        ).set_current()

        # Test whether the API functions exist as a result of 'from lamarkdown import *'.

        # It might seem obvious that this would work, but the production code must take explicit
        # action (defining self.__all__) to allow it, because the API module is unconventionally
        # defined as a class, lamarkdown.lib.api_impl.ApiImpl, which is instantiated and
        # transplanted into sys.modules.

        css('mock_css')  # noqa: F405
        js('mock_js')    # noqa: F405

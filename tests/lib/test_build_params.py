from ..util.mock_progress import MockProgress
from ..util.mock_cache import MockCache
from lamarkdown.lib.api_impl import ApiImpl
from lamarkdown.lib.build_params import BuildParams
from lamarkdown.lib.directives import Directives

import unittest
from hamcrest import assert_that, has_entries


class BuildParamsTestCase(unittest.TestCase):

    def setUp(self):
        progress = MockProgress()
        BuildParams.set_current(BuildParams(
            src_file = 'mock_src.md',
            target_file = 'mock_target.html',
            build_files = [],
            build_dir = 'mock_dir',
            build_defaults = False,
            build_cache = MockCache(),
            fetch_cache = MockCache(),
            progress = progress,
            directives = Directives(progress),
            is_live = False,
            allow_exec_cmdline = False
        ))


    def tearDown(self):
        BuildParams.current = None


    def test_replacing_extension_configs(self):
        api = ApiImpl()
        api('ext',
            int1 = 1,
            str1 = 'value1',
            list1 = [1],
            dict1 = {'k1': 'v1'},
            set1 = {1})

        assert_that(
            BuildParams.current.named_extensions,
            has_entries({
                'ext': has_entries({
                    'str1': 'value1',
                    'list1': [1],
                    'dict1': {'k1': 'v1'},
                    'set1': {1}
                })
            })
        )

        # Replace half the values
        api('ext', str1 = 'value2', list1 = [2])

        assert_that(
            BuildParams.current.named_extensions,
            has_entries({
                'ext': has_entries({
                    'str1': 'value2',
                    'list1': [2],
                    'dict1': {'k1': 'v1'},
                    'set1': {1}
                })
            })
        )

        # Replace the other half:
        api('ext', dict1 = {'k2': 'v2'}, set1 = {2})

        assert_that(
            BuildParams.current.named_extensions,
            has_entries({
                'ext': has_entries({
                    'str1': 'value2',
                    'list1': [2],
                    'dict1': {'k2': 'v2'},
                    'set1': {2}
                })
            })
        )


    def test_extending_extension_configs(self):
        api = ApiImpl()
        api('ext',
            str1 = 'value1',
            list1 = [1],
            dict1 = {'k1': 'v1'},
            set1 = {1},
            str2 = api.extendable('value2', join=';'),
            list2 = api.extendable([2]),
            dict2 = api.extendable({'k2': 'v2'}),
            set2  = api.extendable({2}))

        # ExtendableValue should transparently resolve to its underlying value(s).
        assert_that(
            BuildParams.current.named_extensions,
            has_entries({
                'ext': has_entries({
                    'str1': 'value1',
                    'list1': [1],
                    'dict1': {'k1': 'v1'},
                    'set1': {1},
                    'str2': 'value2',
                    'list2': [2],
                    'dict2': {'k2': 'v2'},
                    'set2': {2}
                })
            })
        )


        # Should cause all the config options to be extended (not replaced)
        api('ext',
            str1 = api.extendable('value3', join=';'),
            list1 = api.extendable([3]),
            dict1 = api.extendable({'k3': 'v3'}),
            set1 = api.extendable({3}),
            str2 = 'value4',
            list2 = [4],
            dict2 = {'k4': 'v4'},
            set2  = {4})

        assert_that(
            BuildParams.current.named_extensions,
            has_entries({
                'ext': has_entries({
                    'str1': 'value1;value3',
                    'list1': [1, 3],
                    'dict1': {'k1': 'v1', 'k3': 'v3'},
                    'set1': {1, 3},
                    'str2': 'value2;value4',
                    'list2': [2, 4],
                    'dict2': {'k2': 'v2', 'k4': 'v4'},
                    'set2': {2, 4}
                })
            })
        )


        # Now check what happens when we add ExtendableValues to each other:
        str3 = api.extendable('value5')
        str3.extend('value6')

        list3 = api.extendable([5])
        list3.extend([6])

        dict3 = api.extendable({'k5': 'v5'})
        dict3.extend({'k6': 'v6'})

        set3 = api.extendable({5})
        set3.extend({6})


        api('ext',
            str1 = str3, list1 = list3, dict1 = dict3, set1 = set3,
            str2 = str3, list2 = list3, dict2 = dict3, set2 = set3)

        assert_that(
            BuildParams.current.named_extensions,
            has_entries({
                'ext': has_entries({
                    'str1': 'value1;value3;value5;value6',
                    'list1': [1, 3, 5, 6],
                    'dict1': {'k1': 'v1', 'k3': 'v3', 'k5': 'v5', 'k6': 'v6'},
                    'set1': {1, 3, 5, 6},
                    'str2': 'value2;value4;value5;value6',
                    'list2': [2, 4, 5, 6],
                    'dict2': {'k2': 'v2', 'k4': 'v4', 'k5': 'v5', 'k6': 'v6'},
                    'set2': {2, 4, 5, 6}
                })
            })
        )


    def test_callback_extension_configs(self):

        valA = 'value1'
        valB = 'value2'

        api = ApiImpl()
        api('ext',
            str1 = api.late(lambda: valA),
            str2 = api.extendable(api.late(lambda: valB)),
            str3 = 'value3')

        api('ext', str3 = api.extendable('value4'))
        api('ext', str3 = api.late(lambda: valA))
        api('ext', str3 = 'value5')
        api('ext', str3 = api.extendable(api.late(lambda: valB)))

        valA = 'value11'
        valB = 'value12'

        assert_that(
            BuildParams.current.named_extensions['ext'],
            has_entries({
                'str1': 'value11',
                'str2': 'value12',
                'str3': 'value3value4value11value5value12'
            })
        )

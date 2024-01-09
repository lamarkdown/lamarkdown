'''
# API entry point

Build files need only 'import lamarkdown'.
'''

from .lib.api_impl import ApiImpl
import sys

# Actual API implementation is an ApiImpl instance (inheriting from 'module').
api = ApiImpl()

# Add all the normal package contents, particularly sub-packages like 'ext'.
api.__dict__.update(locals())

# Install the API module.
sys.modules[__name__] = api

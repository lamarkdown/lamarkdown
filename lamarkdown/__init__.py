'''
# API entry point

Build files need only 'import lamarkdown'.
'''

from .lib.api_impl import ApiImpl, ValueFactory, ResourceSpec, Condition, ResourceInfo
import sys

# Actual API implementation is an ApiImpl instance (inheriting from 'module').
new_module = ApiImpl()

# Makes 'from lamarkdown import *' work. This would potentially be confusing if it didn't work.
new_module.__all__ = dir(new_module)

# Add all the normal package contents, particularly sub-packages like 'ext'.
new_module.__dict__.update(locals())

# Install the API module.
sys.modules[__name__] = new_module

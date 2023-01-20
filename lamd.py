#!/usr/bin/python

# Script for running Lamarkdown directly from the repository, without properly installing it. 
# (Actual installation will use `pyproject.toml` and bypass this file.)

# (1) Create an abbreviation of the lamarkdown.ext package. This has the same outcome as the 
# [tool.poetry.plugins."markdown.extensions"] section in `pyproject.toml`, but the latter only 
# works if the package is properly installed, so we cannot rely on it here.
import lamarkdown.ext
import sys
sys.modules['la'] = sys.modules['lamarkdown.ext']

# (2) Invoke normal entry point.
from lamarkdown.lib import lamd
lamd.main()

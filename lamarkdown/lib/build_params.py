'''
The 'build parameters' are all the information (apart from the source markdown file) needed to
build a completed HTML document.

This file also maintains a global instance of this state, BuildParams.current, which is accessed by
build modules.
'''

from markdown.extensions import Extension

import copy
from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Dict, List, Optional, Set, Union

@dataclass
class Resource:
    '''
    A resource represents a snippet of CSS/JS code, or a CSS/JS URL, produced conditionally
    depending on whether a set/subset of XPath expressions were found in the document. That is, the
    resource "knows when it's needed".
    '''
    value_factory: Callable[[Set[str]],Optional[str]]
    xpaths: List[str] = field(default_factory=list)


@dataclass
class BuildParams:
    current: ClassVar[Optional['BuildParams']] = None

    # These fields are not intended to be modified once set:
    src_file: str
    target_file: str
    build_files: List[str]
    build_dir: str
    build_defaults: bool

    # These fields *are* modifiable by build modules:
    variants:          Dict[str,List[str]]        = field(default_factory=dict)
    extensions:        List[Union[str,Extension]] = field(default_factory=list)
    extension_configs: Dict[str,Dict[str,Any]]    = field(default_factory=dict)
    css:               List[Resource]             = field(default_factory=list)
    css_files:         List[Resource]             = field(default_factory=list)
    js:                List[Resource]             = field(default_factory=list)
    js_files:          List[Resource]             = field(default_factory=list)
    content_start:     str                        = ''
    content_end:       str                        = ''
    env:               Dict[str,Any]              = field(default_factory=dict)

    def set_current(self):
        BuildParams.current = self

    def alt_target_file(self, variant):
        base, ext = self.target_file.rsplit('.', 1)
        return base + variant + '.' + ext

    @property
    def src_base(self):
        return self.src_file.rsplit('.', 1)[0]

    @property
    def target_base(self):
        return self.target_file.rsplit('.', 1)[0]

    @property
    def target_files(self) -> Dict[str,str]:
        if self.variants:
            target_base_name, target_file_ext = self.target_file.rsplit('.', 1)
            return {variant: f'{target_base_name}{variant}.{target_file_ext}' for variant in self.variants.keys()}

        else:
            return {'': self.target_file}

    @property
    def xpaths(self) -> Set[str]:
        '''
        The set of all XPath expressions specified by all CSS/JS resources.
        '''
        return {xpath for res_list in (self.css, self.css_files, self.js, self.js_files)
                      for res in res_list
                      for xpath in res.xpaths}

    def copy(self):
        return copy.deepcopy(self)

    def reset(self):
        self.variants = {}
        self.extensions = []
        self.extension_configs = {}
        self.css = []
        self.css_files = []
        self.js = []
        self.js_files = []
        self.content_start = ''
        self.content_end = ''
        self.env = {}


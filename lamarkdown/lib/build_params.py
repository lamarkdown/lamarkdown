'''
The 'build parameters' are all the information (apart from the source markdown file) needed to
build a completed HTML document.

This file also maintains a global instance of this state, BuildParams.current, which is accessed by
build modules.
'''

from markdown.extensions import Extension
import lxml.etree

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Dict, List, Optional, Set

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
class Variant:
    name: str
    build_fn: Callable[[],None]

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Environment(dict):
    def __deepcopy__(self, memo):
        new_env = Environment()
        for key, value in self.items():
            try:
                new_env[key] = deepcopy(value, memo)
            except TypeError:
                # Some types (like module) cannot be deep-copied, so we just reuse the reference.
                new_env[key] = value
        return new_env


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
    name:              str                        = ''
    variant_name_sep:  str                        = '_'
    variants:          List[Variant]              = field(default_factory=list)
    #extensions:        Set[Union[str,Extension]] = field(default_factory=set)
    #extension_configs: Dict[str,Dict[str,Any]]   = field(default_factory=dict)
    named_extensions:  Dict[str,Dict[str,Any]]    = field(default_factory=dict)
    obj_extensions:    List[Extension]            = field(default_factory=list)
    tree_hooks:        List[Callable]             = field(default_factory=list)
    css:               List[Resource]             = field(default_factory=list)
    css_files:         List[Resource]             = field(default_factory=list)
    js:                List[Resource]             = field(default_factory=list)
    js_files:          List[Resource]             = field(default_factory=list)
    content_start:     str                        = ''
    content_end:       str                        = ''
    env:               Dict[str,Any]              = field(default_factory=Environment)
    output_namer:      Callable[[str],str]        = lambda t: t

    def set_current(self):
        BuildParams.current = self

    @property
    def src_base(self):
        return self.src_file.rsplit('.', 1)[0]

    @property
    def target_base(self):
        return self.target_file.rsplit('.', 1)[0]

    @property
    def output_file(self):
        return self.output_namer(self.target_file)

    @property
    def resource_xpaths(self) -> Set[str]:
        '''
        The set of all XPath expressions specified by all CSS/JS resources.
        '''
        return {xpath for res_list in (self.css, self.css_files, self.js, self.js_files)
                      for res in res_list
                      for xpath in res.xpaths}

    def reset(self):
        self.name = ''
        self.variant_name_sep = '_'
        self.variants = []
        #self.extensions = set()
        #self.extension_configs = {}
        self.named_extensions = {}
        self.obj_extensions = []
        self.tree_hooks = []
        self.css = []
        self.css_files = []
        self.js = []
        self.js_files = []
        self.content_start = ''
        self.content_end = ''
        self.env = Environment()
        self.output_namer = lambda t: t


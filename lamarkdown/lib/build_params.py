'''
The 'build parameters' are all the information (apart from the source markdown file) needed to
build a completed HTML document.

This file also maintains a global instance of this state, BuildParams.current, which is accessed by
build modules.
'''

from .resources import ResourceSpec
from .progress import Progress
from markdown.extensions import Extension
import diskcache
import lxml.etree

from copy import deepcopy
from dataclasses import dataclass, field
import os.path
from typing import Any, Callable, ClassVar, Dict, Iterable, List, Optional, Set

class ResourceError(Exception): pass


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

EmbedRule = Callable[[str,str,str],bool]
ResourceHashRule = Callable[[str,str,str],Optional[str]]

def default_embed_rule(url: str, mime_type: str, tag: str) -> bool:
    return not (
        tag in {'audio', 'video', 'iframe'} or
        mime_type.startswith('audio/') or
        mime_type.startswith('video/')
    )

def default_resource_hash_rule(url: str, mime_type: str, tag: str) -> str:
    return None


@dataclass
class BuildParams:
    current: ClassVar[Optional['BuildParams']] = None

    # These fields are not intended to be modified once set:
    src_file: str
    target_file: str
    build_files: List[str]
    build_dir: str
    build_defaults: bool
    cache: diskcache.Cache
    progress: Progress
    is_live: bool
    allow_exec_cmdline: bool

    # These fields *are* modifiable by build modules (or even extensions):
    name:                 str                        = ''
    variant_name_sep:     str                        = '_'
    variants:             List[Variant]              = field(default_factory=list)
    named_extensions:     Dict[str,Dict[str,Any]]    = field(default_factory=dict)
    obj_extensions:       List[Extension]            = field(default_factory=list)
    tree_hooks:           List[Callable]             = field(default_factory=list)
    html_hooks:           List[Callable]             = field(default_factory=list)
    font_codepoints:      Set[int]                   = field(default_factory=set)
    css_vars:             Dict[str,str]              = field(default_factory=dict)
    css:                  List[ResourceSpec]         = field(default_factory=list)
    js:                   List[ResourceSpec]         = field(default_factory=list)
    custom_resource_path: str                        = None
    embed_rule:           EmbedRule                  = default_embed_rule
    resource_hash_rule:   ResourceHashRule           = default_resource_hash_rule
    env:                  Dict[str,Any]              = field(default_factory=Environment)
    output_namer:         Callable[[str],str]        = lambda t: t
    allow_exec:           bool                       = False
    live_update_deps:     Set[str]                   = field(default_factory=set)

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
    def resource_path(self):
        return self.custom_resource_path or os.path.dirname(os.path.abspath(self.src_file))

    @property
    def resource_xpaths(self) -> Set[str]:
        '''
        The set of all XPath expressions specified by all CSS/JS resources.
        '''
        return {xpath for res_list in (self.css, self.js)
                      for res in res_list
                      for xpath in res.xpaths_required}


    def reset(self):
        self.name = ''
        self.variant_name_sep = '_'
        self.variants = []
        self.named_extensions = {}
        self.obj_extensions = []
        self.tree_hooks = []
        self.html_hooks = []
        self.font_codepoints = set()
        self.css_vars = {}
        self.css = []
        self.js = []
        self.custom_resource_path = None
        self.embed_rule = default_embed_rule
        self.resource_hash_rule = default_resource_hash_rule
        self.env = Environment()
        self.output_namer = lambda t: t
        self.live_update_deps = set()
        self.allow_exec = self.allow_exec_cmdline


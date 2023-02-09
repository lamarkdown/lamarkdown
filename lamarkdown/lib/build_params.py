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
from typing import *

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


R = TypeVar('R')
class Rule(Protocol[R]):
    def __call__(self, *, url: str,
                          type: str,
                          tag: str,
                          attr: Dict[str,str]) -> R: ...

# Note: all 'rule' callbacks should accept a '**kwargs' parameter. The actual keyword arguments
# supplied include _some subset_ of: 'url', 'type' (mime type), 'tag' and 'attr', and possibly
# others in the future.

def default_embed_rule(type: str = '', tag: str = '', **kwargs) -> bool:
    return not (
        tag in ('audio', 'video', 'iframe') or
        type.startswith('audio/') or
        type.startswith('video/')
    )

def default_resource_hash_rule(**kwargs) -> Optional[str]:
    return None

def default_scale_rule(**kwargs) -> float:
    return 1.0



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
    resource_base_url:    str                        = ''
    embed_rule:           Rule[bool]                 = default_embed_rule
    resource_hash_rule:   Rule[Optional[str]]        = default_resource_hash_rule
    scale_rule:           Rule[float]                = default_scale_rule
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
        self.resource_base_url = ''
        self.embed_rule         = default_embed_rule
        self.resource_hash_rule = default_resource_hash_rule
        self.scale_rule         = default_scale_rule
        self.env = Environment()
        self.output_namer = lambda t: t
        self.live_update_deps = set()
        self.allow_exec = self.allow_exec_cmdline


'''
The 'build parameters' are all the information (apart from the source markdown file) needed to
build a completed HTML document.

This file also maintains a global instance of this state, BuildParams.current, which is accessed by
build modules.
'''

from __future__ import annotations # For Python 3.7 compatibility
import copy
from dataclasses import dataclass, field, InitVar
from typing import Any, ClassVar, Optional, Union

def _list(): return field(default_factory=list)
def _dict(): return field(default_factory=dict)

@dataclass
class BuildParams:
    current: ClassVar[Optional[BuildParams]] = None

    src_file: InitVar[str]
    target_file: InitVar[str]
    build_files: InitVar[list[str]]
    build_dir: InitVar[str]

    variants: dict[str,list[str]] = _dict()
    extensions: list[Union[str,markdown.extensions.Extension]] = _list()
    extension_configs: dict[str,dict[str,Any]] = _dict()
    css: str = ''
    css_files: list[str] = _list()
    js: str = ''
    js_files: list[str] = _list()
    content_start: str = ''
    content_end: str = ''
    env: dict[str,Any] = _dict()

    def __post_init__(self, src_file: str, target_file: str, build_files: list[str], build_dir: str):
        self.__src_file = src_file
        self.__target_file = target_file
        self.__build_files = build_files
        self.__build_dir = build_dir

    def set_current(self):
        BuildParams.current = self

    @property
    def src_file(self): return self.__src_file

    @property
    def target_file(self): return self.__target_file

    @property
    def build_files(self): return list(self.__build_files)

    @property
    def build_dir(self): return self.__build_dir


    def alt_target_file(self, variant):
        target_base_name, target_file_ext = self.target_file.rsplit('.', 1)
        return target_base_name + variant + '.' + target_file_ext

    @property
    def target_files(self) -> dict[str,str]:
        if self.variants:
            target_base_name, target_file_ext = self.target_file.rsplit('.', 1)
            return {variant: f'{target_base_name}{variant}.{target_file_ext}' for variant in self.variants.keys()}

        else:
            return {'': self.target_file}

    def copy(self):
        return copy.deepcopy(self)

    def reset(self):
        self.variants = {}
        self.extensions = []
        self.extension_configs = {}
        self.css = ''
        self.css_files = []
        self.js = ''
        self.js_files = []
        self.content_start = ''
        self.content_end = ''
        self.env = {}


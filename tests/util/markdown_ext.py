import importlib
import sys
from typing import Tuple


def entry_point_cls(name: str) -> Tuple[str, str]:

    if sys.version_info >= (3, 10):
        entry_point = importlib.metadata.entry_points(group='markdown.extensions')[name]

    else:
        entry_point = next(
            ep
            for ep in importlib.metadata.entry_points()['markdown.extensions']
            if ep.name == name
        )

    module_name, class_name = entry_point.value.split(':', 1)
    return importlib.import_module(module_name).__dict__[class_name]

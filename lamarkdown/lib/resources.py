from .progress import Progress

import diskcache

from base64 import b64encode
from dataclasses import dataclass
import hashlib
import html
import os.path
import re
from typing import Callable, List, Optional, Set


class Resource:
    def as_style(self)  -> str: raise NotImplementedError
    def as_script(self) -> str: raise NotImplementedError
    def get_raw_content(self) -> str: raise NotImplementedError
    def add_or_coalesce(self, res_list) -> str: raise NotImplementedError
    def prepend_or_coalesce(self, res_list) -> str: raise NotImplementedError


def _check(val, label):
    if not isinstance(val, str):
        raise ValueError(f'{label} should be a string; was {type(val)}')
    return val


class ContentResource:
    def __init__(self, content: str):
        self.content = _check(content, 'content')

    def as_style(self) -> str:
        # Strip CSS comments at the beginning of lines
        css = re.sub('(^|\n)\s*/\*.*?\*/', '\n', self.content, flags = re.DOTALL)

        # Strip CSS comments at the end of lines
        css = re.sub('/\*.*?\*/\s*($|\n)', '\n', css, flags = re.DOTALL)

        # Normalise line breaks
        css = re.sub('(\s*\n)+\s*', '\n', css, flags = re.DOTALL)

        return f'<style>\n{css}\n</style>'


    def as_script(self) -> str:
        return f'<script>\n{self.content}\n</script>'

    def get_raw_content(self) -> str:
        return self.content

    def add_or_coalesce(self, res_list):
        if len(res_list) > 0 and isinstance(res_list[-1], ContentResource):
            res_list[-1] = ContentResource(f'{res_list[-1].content}\n{self.content}')
        else:
            res_list.append(self)

    def prepend_or_coalesce(self, res_list):
        if len(res_list) > 0 and isinstance(res_list[0], ContentResource):
            res_list[0] = ContentResource(f'{self.content}\n{res_list[0].content}')
        else:
            res_list.insert(0, self)


class UrlResource:
    def __init__(self, url: str, hash: str = None, hash_type: str = None):
        self.url = _check(url, 'url')
        self.hash = hash
        self.hash_type = hash_type

    def _integrity(self):
        return f' integrity="{self.hash_type}-{self.hash}" crossorigin="anonymous"' if self.hash else ''
        #return f' integrity="{self.hash_type}-{self.hash}"' if self.hash else ''

    def as_style(self)   -> str:
        return f'<link rel="stylesheet" href="{html.escape(self.url)}"{self._integrity()} />'

    def as_script(self) -> str:
        return f'<script src="{html.escape(self.url)}"{self._integrity()}></script>'

    def get_raw_content(self) -> str:
        return ''

    def add_or_coalesce(self, res_list):
        res_list.append(self)

    def prepend_or_coalesce(self, res_list):
        res_list.insert(0, self)



class ResourceSpec:
    def __init__(self, xpaths: List[str]):
        self._xpaths = xpaths

    @property
    def xpaths_required(self):
        return self._xpaths

    def make_resource(self, xpaths_found: Set[str], progress: Progress) -> Optional[Resource]:
        raise NotImplementedError


class ContentResourceSpec(ResourceSpec):
    def __init__(self, xpaths_required: List[str],
                       content_factory: Callable[[Set[str]],Optional[str]]):
        super().__init__(xpaths_required)
        self.content_factory = content_factory

    def make_resource(self, xpaths_found: Set[str], progress: Progress) -> Optional[Resource]:
        content = self.content_factory(xpaths_found.intersection(self.xpaths_required))
        return ContentResource(content) if content else None


class UrlResourceSpec(ResourceSpec):
    URL_SCHEME_REGEX = re.compile('[a-z]+:')

    def __init__(self, xpaths_required: List[str],
                       url_factory: Callable[[Set[str]],Optional[str]],
                       cache: diskcache.Cache,
                       embed: Optional[bool] = None,
                       hash_type: Optional[str] = None,
                       base_path: str = None,
                       mime_type: str = None,
                       embed_policy: Callable[[],Optional[bool]] = lambda _: None,
                       hash_type_policy: Callable[[],Optional[str]] = lambda _: None):

        super().__init__(xpaths_required)
        self.url_factory = url_factory
        self.embed = embed
        self.hash_type = hash_type
        self.base_path = base_path
        self.mime_type = mime_type
        self.embed_policy = embed_policy
        self.hash_type_policy = hash_type_policy

        #if hash_type and hash_type not in ['sha256', 'sha384', 'sha512']:
            #raise ValueError(f'Unsupported hash type: {hash_type}')


    def _read_url(self, url, progress: Progress) -> bytes:
        if self.URL_SCHEME_REGEX.match(url):
            content_bytes = self.cache.get(url)

            if content_bytes is None:
                with urllib.request.urlopen(url) as conn:
                    try:
                        content_bytes = conn.read()

                        # TODO: observe and respect the HTTP headers 'Expires' and 'Cache-Control'.
                        #expires = conn.headers.get('Expires')
                        self.cache[url] = content_bytes
                    except OSError as e:
                        progress.error_from_exception(url, e)
                        content_bytes = b'' # FIXME: can we pick a value that will be "visible" within the document?

            return (True, content_bytes)

        else:
            with open(os.path.join(self.base_path, url), 'rb') as reader:
                return (False, reader.read())


    def make_resource(self, xpaths_found: Set[str], progress) -> Optional[Resource]:
        url = self.url_factory(xpaths_found.intersection(self.xpaths_required))
        if url is None:
            return None

        embed_policy = self.embed_policy()
        embed = (
            (embed_policy is True      and self.embed is not False) or
            (embed_policy is not False and self.embed is True)
        )

        hash_type = self.hash_type or self.hash_type_policy()
        if hash_type and hash_type not in ['sha256', 'sha384', 'sha512']:
            progress.error(f'"{url}"', f'Unsupported hash type: {hash_type}')
            hash_type = 'sha256'

        if embed:
            _, content_bytes = self._read_url(url, progress)
            url = f'data:{self.mime_type or ""};base64,{b64encode(content_bytes).decode()}'
            return UrlResource(url)

        elif hash_type:
            # Note: relies on the fact that hashlib.new() and the HTML 'integrity' attribute both
            # use the same strings 'sha256', 'sha384' and 'sha512'.
            remote, content_bytes = self._read_url(url, progress)
            hash = b64encode(hashlib.new(hash_type, content_bytes).digest()).decode()

            if not remote:
                progress.warning(
                    f'"{url}"',
                    f'Using hashing on relative URLs is supported but not recommended. The browser may refuse to load the resource when accessing the document from local storage.')

            return UrlResource(url = url, hash = hash, hash_type = hash_type)

        else:
            return UrlResource(url = url)


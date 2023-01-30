from .progress import Progress

import diskcache

from base64 import b64encode
import email.utils
import hashlib
import mimetypes
import os.path
import re
import time
from typing import Callable, List, Optional, Set, Tuple, Union
import urllib.request


DEFAULT_USER_AGENT = None
DEFAULT_CACHE_EXPIRY = 86400 # By default, cache resources for 24 hours
URL_SCHEME_REGEX = re.compile('[a-z]+:')

def read_url(url: str,
             resource_path: str,
             cache,
             progress: Progress,
             user_agent = DEFAULT_USER_AGENT) -> Tuple[bool, bytes, str]:
    if URL_SCHEME_REGEX.match(url):
        cache_entry = cache.get(url)

        if cache_entry is None:
            progress.progress('External resource', f'Downloading {url}...')
            with urllib.request.urlopen(url) as conn:
                try:
                    content_bytes = conn.read()

                    try:
                        status = conn.status
                    except AttributeError:
                        # Py3.9 replaced getstatus() with status, but <3.9 still use getstatus().
                        status = conn.getstatus()

                    if status == 200: # Should we accept other 2xx codes? Not sure.

                        # Try to determine the mime type
                        mime_type = conn.headers.get('content-type') # Might be None
                        if mime_type is None:
                            mime_type, _ = mimetypes.guess_type(url)

                        # Try to find the actual cache expiry time, as reported by the server
                        cache_expiry = DEFAULT_CACHE_EXPIRY
                        cache_control = conn.headers.get('cache-control')
                        if cache_control is not None:
                            directives = cache_control.split(',')
                            if 'no-cache' in directives or 'no-store' in directives:
                                cache_expiry = 0 # No-caching!

                            else:
                                for d in directives:
                                    d = d.strip()
                                    if d.startswith('max-age='):
                                        try:
                                            cache_expiry = int(d[8:])
                                        except ValueError:
                                            pass # Just use the default.

                        # Take into account time elapsed since content generation. (We assume that
                        # the client and server clocks agree, though negative elapsed time is
                        # obviously bogus, and we throw that out.)
                        generation_time = email.utils.parsedate_tz(conn.headers.get('date', ''))
                        if generation_time is not None:
                            elapsed = time.time() - email.utils.mktime_tz(generation_time)
                            if elapsed > 0:
                                cache_expiry -= elapsed

                        # Insert downloaded content into cache, if appropriate
                        if cache_expiry > 0:
                            cache.set(url, (content_bytes, mime_type), expire = cache_expiry)

                    else: # status != 200
                        progress.error(url,
                                       f'Server returned {status} code',
                                       content_bytes.decode(errors = 'ignore'))
                        content_bytes = b''
                        mime_type = None

                except OSError as e:
                    progress.error_from_exception(url, e)
                    content_bytes = b''

        else:
            progress.progress('External resource', f'Using cached value of {url}')
            content_bytes, mime_type = cache_entry

        return (True, content_bytes, mime_type)

    else:
        with open(os.path.join(resource_path, url), 'rb') as reader:
            mime_type, _ = mimetypes.guess_type(url)
            return (False, reader.read(), mime_type)


def make_data_url(url: str,
                  resource_path: str,
                  mime_type: str,
                  cache,
                  progress: Progress,
                  converter: Callable[[bytes,str],Tuple[bytes,str]] = lambda c,m: (c,m)) -> str:
    _, content_bytes, auto_mime_type = read_url(url, resource_path, cache, progress)
    mime_type = mime_type or auto_mime_type
    content_bytes, mime_type = converter(content_bytes, mime_type)

    return f'data:{mime_type or ""};base64,{b64encode(content_bytes).decode()}'


def _check(val, label):
    if not isinstance(val, str):
        raise ValueError(f'{label} should be a string; was {type(val)}')
    return val


class ContentResource:
    def __init__(self, content: str):
        self.content = _check(content, 'content')


class UrlResource:
    def __init__(self, url: str, to_embed: bool = False, hash: str = None, hash_type: str = None):
        self.url = _check(url, 'url')
        self.to_embed = to_embed
        self.hash = hash
        self.hash_type = hash_type

    def integrity_attr(self):
        return f' integrity="{self.hash_type}-{self.hash}" crossorigin="anonymous"' if self.hash else ''


Resource = Union[UrlResource,ContentResource]
OptResource = Optional[Resource]

class ResourceSpec:
    def __init__(self, xpaths: List[str]):
        self._xpaths = xpaths

    @property
    def xpaths_required(self):
        return self._xpaths

    def make_resource(self, xpaths_found: Set[str],
                            progress: Progress) -> OptResource:
        raise NotImplementedError


class ContentResourceSpec(ResourceSpec):
    def __init__(self, xpaths_required: List[str],
                       content_factory: Callable[[Set[str]],Optional[str]]):
        super().__init__(xpaths_required)
        self.content_factory = content_factory

    def make_resource(self, xpaths_found: Set[str], progress: Progress) -> OptResource:
        content = self.content_factory(xpaths_found.intersection(self.xpaths_required))
        return ContentResource(content) if content else None


class UrlResourceSpec(ResourceSpec):

    def __init__(self, xpaths_required: List[str],
                       url_factory: Callable[[Set[str]],Optional[str]],
                       cache: diskcache.Cache,
                       embed: Optional[bool],
                       hash_type: Optional[str],
                       resource_path: str,
                       mime_type: str,
                       embed_policy: Callable[[],Optional[bool]],     # = lambda _: None,
                       hash_type_policy: Callable[[],Optional[str]]): # = lambda _: None):

        super().__init__(xpaths_required)
        self.url_factory = url_factory
        self.cache = cache
        self.embed = embed
        self.hash_type = hash_type
        self.resource_path = resource_path
        self.mime_type = mime_type
        self.embed_policy = embed_policy
        self.hash_type_policy = hash_type_policy


    def make_resource(self, xpaths_found: Set[str],
                            progress: Progress) -> OptResource:
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
            return UrlResource(url = url, to_embed = True)

        elif hash_type:
            # Note: relies on the fact that hashlib.new() and the HTML 'integrity' attribute both
            # use the same strings 'sha256', 'sha384' and 'sha512'.
            is_remote, content_bytes, _mime_type = read_url(url, self.resource_path, self.cache, progress)
            hash = b64encode(hashlib.new(hash_type, content_bytes).digest()).decode()

            if not is_remote:
                progress.warning(
                    f'"{url}"',
                    f'Using hashing on relative URLs is supported but not recommended. The browser may refuse to load the resource when accessing the document from local storage.')

            return UrlResource(url = url, hash = hash, hash_type = hash_type)

        else:
            return UrlResource(url = url)




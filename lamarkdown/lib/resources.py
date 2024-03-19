from __future__ import annotations
from .progress import Progress

import diskcache  # type: ignore

import abc
import base64
import email.utils
import hashlib
import mimetypes
import re
import socket
import time
from typing import Callable
import urllib.error
import urllib.parse
import urllib.request

NAME = 'resource specification'

DEFAULT_USER_AGENT = None
DEFAULT_CACHE_EXPIRY = 86400  # By default, cache resources for 24 hours
REMOTE_URL_SCHEME_REGEX = re.compile('(?!(file|data):)[a-z]+:')


def read_url(url: str,
             cache,
             progress: Progress,
             user_agent = DEFAULT_USER_AGENT) -> tuple[bool, bytes | None, str | None]:

    NAME = 'fetching'

    if REMOTE_URL_SCHEME_REGEX.match(url):
        cache_entry = cache.get(url)

        if cache_entry is None:
            progress.progress(NAME, msg = url)
            mime_type = None
            try:
                with urllib.request.urlopen(url) as conn:
                    content_bytes = conn.read()

                    try:
                        status = conn.status
                    except AttributeError:
                        # Py3.9 replaced getstatus() with status, but <3.9 still use getstatus().
                        status = conn.getstatus()

                    if status == 200:  # Should we accept other 2xx codes? Not sure.

                        # Try to determine the mime type
                        mime_type = conn.headers.get('content-type')  # Might be None
                        if mime_type is None:
                            mime_type, _ = mimetypes.guess_type(url)

                        # Try to find the actual cache expiry time, as reported by the server
                        cache_expiry = DEFAULT_CACHE_EXPIRY
                        cache_control = conn.headers.get('cache-control')
                        if cache_control is not None:
                            directives = cache_control.split(',')
                            if 'no-cache' in directives or 'no-store' in directives:
                                cache_expiry = 0  # No-caching!

                            else:
                                for d in directives:
                                    d = d.strip()
                                    if d.startswith('max-age='):
                                        try:
                                            cache_expiry = int(d[8:])
                                        except ValueError:
                                            pass  # Just use the default.

                        # Take into account time elapsed since content generation. (We assume that
                        # the client and server clocks agree, though negative elapsed time is
                        # obviously bogus, and we throw that out.)
                        generation_time = email.utils.parsedate_tz(conn.headers.get('date', ''))
                        if generation_time is not None:
                            elapsed = int(time.time() - email.utils.mktime_tz(generation_time))
                            if elapsed > 0:
                                cache_expiry -= elapsed

                        # Insert downloaded content into cache, if appropriate
                        if cache_expiry > 0:
                            cache.set(url, (content_bytes, mime_type), expire = cache_expiry)

                    else:  # status != 200
                        progress.error(NAME,
                                       msg = f'Server returned {status} code',
                                       output = content_bytes.decode(errors = 'ignore'))
                        # content_bytes = b''
                        # mime_type = ''
                        content_bytes = None
                        mime_type = None

            except OSError as e:
                if isinstance(e, urllib.error.URLError) and isinstance(e.reason, socket.gaierror):
                    progress.error(NAME,
                                   msg = f'{e.reason.strerror} while reading "{url}"',
                                   show_traceback = False)
                else:
                    progress.error(NAME, exception = e)
                # content_bytes = b''
                content_bytes = None

        else:
            progress.cache_hit(NAME, resource = url)
            content_bytes, mime_type = cache_entry

        return (True, content_bytes, mime_type)

    else:
        # For local files and data URLs
        if not (url.startswith('file:') or url.startswith('data:')):
            url = f'file:{url}'

        try:
            with urllib.request.urlopen(url) as reader:
                # Using urllib (instead of open()) avoids needing to convert path separators from
                # / to \ on Windows.

                mime_type = reader.headers.get('content-type')  # Might be None
                if mime_type is None:
                    mime_type, _ = mimetypes.guess_type(url)
                return (False, reader.read(), mime_type)

        except urllib.error.URLError as e:
            progress.error(NAME,
                           msg = f'Cannot read "{url}"',
                           exception = e,
                           show_traceback = False)
            # return (False, b'', '')
            return (False, None, None)



def _check(val, label):
    if not isinstance(val, str):
        raise ValueError(f'{label} should be a string; was {type(val)}')
    return val


class ContentResource:
    def __init__(self, content: str):
        self.content = _check(content, 'content')


class UrlResource:
    def __init__(self, url: str, to_embed: bool = False, hash: tuple[str, str] | None = None):
        self._url = _check(url, 'url')
        self._to_embed = to_embed
        self._hash = hash

    def integrity_attr(self):
        if self._hash is None:
            return ''
        else:
            hash_type, hash_value = self._hash
            return f' integrity="{hash_type}-{hash_value}" crossorigin="anonymous"'

    @property
    def url(self) -> str:
        return self._url

    @property
    def to_embed(self) -> bool:
        return self._to_embed


class ResourceSpec(abc.ABC):
    def __init__(self, xpaths: list[str]):
        self._xpaths = xpaths

    @property
    def xpaths_required(self):
        return self._xpaths

    @abc.abstractmethod
    def make_resource(self,
                      xpaths_found: set[str],
                      progress: Progress) -> UrlResource | ContentResource | None:
        raise NotImplementedError


class ContentResourceSpec(ResourceSpec):
    def __init__(self,
                 xpaths_required: list[str],
                 content_factory: Callable[[set[str]], str | None]):
        super().__init__(xpaths_required)
        self.content_factory = content_factory

    def make_resource(self,
                      xpaths_found: set[str],
                      progress: Progress) -> UrlResource | ContentResource | None:

        content = self.content_factory(xpaths_found.intersection(self.xpaths_required))
        return ContentResource(content) if content else None


class UrlResourceSpec(ResourceSpec):

    def __init__(self,
                 xpaths_required: list[str],
                 url_factory: Callable[[set[str]], str | None],
                 base_url: str,
                 cache: diskcache.Cache,
                 embed_fn: Callable[[], bool],
                 hash_type_fn: Callable[[], str | None]):

        super().__init__(xpaths_required)
        self.url_factory = url_factory
        self.base_url = base_url
        self.cache = cache
        self.embed_fn = embed_fn
        self.hash_type_fn = hash_type_fn


    def make_resource(self,
                      xpaths_found: set[str],
                      progress: Progress) -> UrlResource | ContentResource | None:
        url = self.url_factory(xpaths_found.intersection(self.xpaths_required))
        if url is None:
            return None

        url = urllib.parse.urljoin(self.base_url, url)

        embed = self.embed_fn()
        if embed:
            return UrlResource(url = url, to_embed = True)

        hash_type = self.hash_type_fn()
        if hash_type not in [None, 'sha256', 'sha384', 'sha512']:
            progress.error(NAME,
                           msg = f'Unsupported hash type "{hash_type}" for "{url}"')
            hash_type = 'sha256'

        if hash_type:
            # Note: relies on the fact that hashlib.new() and the HTML 'integrity' attribute both
            # use the same strings 'sha256', 'sha384' and 'sha512'.
            is_remote, content_bytes, _ = read_url(url, self.cache, progress)
            hash = base64.b64encode(hashlib.new(hash_type, content_bytes or b'').digest()).decode()

            if not is_remote:
                progress.warning(
                    NAME,
                    msg = 'Using hashing on relative URLs is supported but not recommended. The '
                    'browser may refuse to load the resource when accessing the document from '
                    'local storage. ("{url}")')

            return UrlResource(url = url, hash = (hash_type, hash))

        else:
            return UrlResource(url = url)

from .progress import Progress

import diskcache

from base64 import b64encode
from dataclasses import dataclass
import email.utils
import hashlib
import html
import io
import mimetypes
import os.path
import re
import time
from typing import Callable, List, Optional, Set, Tuple
import urllib.request


DEFAULT_CACHE_EXPIRY = 86400 # By default, cache resources for 24 hours
URL_SCHEME_REGEX = re.compile('[a-z]+:')

def read_url(url: str,
             resource_path: str,
             cache,
             progress: Progress) -> Tuple[bool, bytes, str]:
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
                  progress: Progress) -> str:
    _, content_bytes, auto_mime_type = read_url(url, resource_path, cache, progress)
    mime_type = mime_type or auto_mime_type
    if mime_type == 'text/css':
        # If we're sure the URL points to a stylesheet, then it may have its own external resources,
        # and we must embed those too.
        content_bytes = embed_stylesheet_resources(
            content_bytes.decode(errors = 'ignore'),
            resource_path,
            cache,
            progress
        ).encode()

    return f'data:{mime_type or ""};base64,{b64encode(content_bytes).decode()}'


CSS_COMMENT_REGEX = re.compile(r'(?xs)/\*.*?\*/')
CSS_STRING_REGEX_BASE = r'''
    (?P<quote>['"])
    (?P<str>
        (
            (?!(?P=quote)) [^\\\n] # Not the operative quote symbol, and not \ or \n
            | \\\\
            | \\.
        )*
    )
    (?P=quote)
'''
# FYI: the syntax (?!(?P=quote)) is a negative lookahead backreference. That is, the next character
# must not be the <quote> character. Then [^\\\n] consumes that character, whatever it is.


CSS_STRING_REGEX = re.compile(fr'(?xs){CSS_STRING_REGEX_BASE}')
CSS_URL_REGEX = re.compile(fr'''(?xs)
    \b(url|src)
    \(\s*
    (
        (?P<url>
            (
                [^"'()\\\x00-\x20]
                | \\\\
                | \\.
            )*
        )
        |
        {CSS_STRING_REGEX_BASE}
    )
    \s*\)
''')

# CSS @import can be written either '@import "..."' or '@import url(...)'. We're only matching the
# former here, because we can handle all 'url(...)' constructs via CSS_URL_REGEX.
#
# Also, we're only matching the _start_ of an @import rule, which can contain other notation after
# the URL.
CSS_IMPORT_REGEX = re.compile(fr'''(?xs)
    @import
    \s*
    {CSS_STRING_REGEX_BASE}
''')

# Matches an escape sequence within a CSS string or url() token.
CSS_STR_ESCAPE_REGEX = re.compile(r'''(?xs)
    \\
    (
        (?P<hex> [0-9a-zA-Z]{1,6})
        [ ]?
        |
        (?P<ch> .)
    )
''')

def embed_stylesheet_resources(stylesheet, resource_path, cache, progress):

    # Note 1
    # ------
    # CSS '@import's will be dealt with by encoding the imported stylesheet as a data URL (just as
    # for other external resources). This is not great from a space-efficiency POV, because it can
    # lead to nested base64 encodings. Each layer of base64 encoding will increase the size by 1/3.
    #
    # It's _tempting_ to take '@import's and embed their content directly in the current stylesheet.
    # Unfortunately, this is not _quite_ semantically identical to an @import, for reasons to do
    # with rule ordering and namespaces (https://www.w3.org/TR/css-cascade-5/#at-import).
    #
    # (The CSS 4 draft contains src() (https://www.w3.org/TR/css-values-4/#funcdef-src), which may
    # provide another way to avoid nested base64 encoding. We could extract all the data URLs,
    # assign them to CSS variables, and refer back to them with src(--var) (which we cannot do with
    # url()). However, as of Jan 2023, CSS 4 remains a draft and presumably not well supported.)

    # Note 2
    # ------
    # Using cssutils (https://pypi.org/project/cssutils/; https://cssutils.readthedocs.io) seemed
    # like a good idea at first, but its API is relatively complex for the task we have, and lacks
    # any mechanism for finding URLs (i.e., we'd still need string searching). Regexes are cruder,
    # but simpler here, and there's nothing that ought to trip us up.

    # Note 3
    # ------
    # Under CSS 4, it seems possible to make a URL using a complex expression involving variables,
    # functions and string concatenation, by using src(). If so, we'll have to give up on embedding
    # such resources (using regexes, anyway).

    with io.StringIO() as buf:
        while len(stylesheet) > 0:

            # Look for comments and strings (outside of a URL/import context). We need to explicitly
            # skip over them, since we don't want to go looking for URLs inside them.
            skip_match = CSS_COMMENT_REGEX.match(stylesheet) or CSS_STRING_REGEX.match(stylesheet)
            if skip_match:
                buf.write(skip_match.group())
                stylesheet = stylesheet[skip_match.end():]
                if len(stylesheet) == 0:
                    break

            # Look for url(), src() and @import.
            match = CSS_URL_REGEX.match(stylesheet) or CSS_IMPORT_REGEX.match(stylesheet)
            if match:
                g = match.groupdict()
                url = g.get('url') or g.get('str')
                # CSS_URL_REGEX has both 'url' and 'str' groups. CSS_IMPORT_REGEX has only 'str'.

                if url.startswith('data:') or url.startswith('#'):
                    # Data URLs are already embedded, and so are fragment URLs (implicitly).
                    buf.write(url)

                else:
                    # Translate escapes in original URL
                    def escape_repl(m):
                        ch = m.group("ch")
                        return ch if ch else chr(int(m.group('hex'), base=16))
                    url = CSS_STR_ESCAPE_REGEX.sub(escape_repl, url)

                    # Grab the URL content and make a Data URL. (make_data_url() _shouldn't_ give us
                    # back a URL with any characters that need escaping.)
                    data_url = make_data_url(url, resource_path, None, cache, progress)

                    if match.group().startswith('@import'):
                        buf.write(f'@import "{data_url}"') # Don't terminate with ';', because we
                                                           # haven't taken ';' from the input yet.
                    else:
                        buf.write(f'url({data_url})')

                stylesheet = stylesheet[match.end():]

            else:
                # Nothing else matched, so just skip over one character.
                buf.write(stylesheet[0])
                stylesheet = stylesheet[1:]

        return buf.getvalue()



def embed_media(root_element,
                resource_path: str,
                cache,
                progress: Progress):

    media_elements = {'img', 'audio', 'video', 'track', 'source'}
    for element in root_element.iter():
        if element.tag in media_elements:
            src = element.get('src')
            if src is not None and not src.startswith('data:') and not src.startswith('#'):
                mime_type = element.get('type')
                element.set('src', make_data_url(src, resource_path, mime_type, cache, progress))


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
            return UrlResource(make_data_url(url, self.resource_path, self.mime_type, self.cache, progress))

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



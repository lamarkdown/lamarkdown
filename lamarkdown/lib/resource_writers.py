from .build_params import BuildParams
from .progress import Progress
from .resources import UrlResource, ContentResource, read_url, make_data_url

import fontTools.ttLib
import fontTools.subset

import html
import io
import re
from typing import Iterable, List, Union


RList = List[Union[UrlResource,ContentResource]]

class ResourceWriter:
    def __init__(self, build_params: BuildParams):
        self.build_params = build_params

    def format(self, resource_list: RList):
        buffer = io.StringIO()
        self.write(buffer, resource_list)
        return buffer.getvalue()

    def write(self, buffer, resource_list: RList):
        raise NotImplementedError

    def _write_in_order(self, buffer, resource_list: RList):
        start_content_index = None
        index = 0
        for res in resource_list:
            if isinstance(res, UrlResource):
                if start_content_index is not None:
                    self._write_content(buffer, resource_list[start_content_index:(index + 1)])
                    start_content_index = 0

                self._write_url(buffer, res)

            elif isinstance(res, ContentResource):
                if start_content_index is None:
                    start_content_index = index

            else:
                raise AssertionError

        if start_content_index is not None:
            self._write_content(buffer, resource_list[start_content_index:])

    def _write_urls_first(self, buffer, resource_list: RList):
        content_resource_list = []
        for res in resource_list:
            if isinstance(res, UrlResource):
                self._write_url(buffer, res)
            elif isinstance(res, ContentResource):
                content_resource_list.append(res)
            else:
                raise AssertionError
        self._write_content(buffer, content_resource_list)

    def _write_content(self, buffer, resource_sublist: Iterable[ContentResource]):
        raise NotImplementedError

    def _write_url(self, buffer, resource: UrlResource):
        raise NotImplementedError



class StylesheetWriter(ResourceWriter):

    CSS_COMMENT_REGEX = re.compile(r'(?xs)/\*.*?\*/')
    CSS_NEWLINE_REGEX = re.compile(r'(\s*\n)+\s*')

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

        # Find and discard trailing 'format()' declaration. (It's not useful for embedded data URLs,
        # and if we're changing font formats from ttf to woff2, it's not going to be correct either.)
        (
            \s* format \( [^)]* \)
        )?
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


    def write(self, buffer, resource_list: RList):
        self._write_urls_first(buffer, resource_list)


    def _write_content(self, buffer, resource_sublist: Iterable[ContentResource]):
        buffer.write('<style>\n')
        for res in resource_sublist:
            buffer.write(self._embed(res.content))
        buffer.write('\n</style>')

    def _write_url(self, buffer, res: UrlResource):
        if res.to_embed:
            _, content_bytes, _ = read_url(res.url,
                                           self.build_params.resource_path,
                                           self.build_params.cache,
                                           self.build_params.progress)

            buffer.write(f'<style>\n{self._embed(content_bytes.decode())}\n</style>')

        else:
            href = html.escape(res.url)
            integrity = res.integrity_attr()
            buffer.write(f'<link rel="stylesheet" href="{href}"{integrity} />')


    def _embed(self, css):
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
            while len(css) > 0:

                # Look for comments and strings (outside of a URL/import context). We need to explicitly
                # skip over them, since we don't want to go looking for URLs inside them.
                comment_match = self.CSS_COMMENT_REGEX.match(css)
                if comment_match:
                    css = css[css.end():]
                    if len(css) == 0: break

                str_match = self.CSS_STRING_REGEX.match(css)
                if str_match:
                    buf.write(str_match.group()) # Retain the actual string in the output
                    css = css[str_match.end():]
                    if len(css) == 0: break

                # Normalise
                newline_match = self.CSS_NEWLINE_REGEX.match(css)
                if newline_match:
                    buf.write('\n') # One newline only
                    css = css[newline_match.end():]
                    if len(css) == 0: break

                # Look for url(), src() and @import.
                match = self.CSS_URL_REGEX.match(css) or self.CSS_IMPORT_REGEX.match(css)
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
                        url = self.CSS_STR_ESCAPE_REGEX.sub(escape_repl, url)

                        # Grab the URL content and make a Data URL. (make_data_url() _shouldn't_ give us
                        # back a URL with any characters that need escaping.)
                        data_url = make_data_url(url,
                                                 self.build_params.resource_path,
                                                 None,
                                                 self.build_params.cache,
                                                 self.build_params.progress,
                                                 self._convert)

                        if match.group().startswith('@import'):
                            buf.write(f'@import "{data_url}"') # Don't terminate with ';', because we
                                                               # haven't taken ';' from the input yet.
                        else:
                            buf.write(f'url({data_url})')

                    css = css[match.end():]

                else:
                    # Nothing else matched, so just skip over one character.
                    buf.write(css[0])
                    css = css[1:]

            return buf.getvalue()


    def _convert(self, content_bytes: bytes, mime_type: str) -> (bytes, str):
        if mime_type == 'text/css':
            # If we're sure the URL points to a stylesheet, then it may have its own external resources,
            # and we must embed those too.
            content_bytes = self._embed(content_bytes.decode(errors = 'ignore')).encode()

        elif mime_type in ['font/ttf', 'font/otf']:
            # We'll take this opportunity to convert any embedded TTF resources into WOFF2 format,
            # and strip out unused glyphs (or at least ones that don't map to any code points in
            # our list).
            #
            # Both of these things should save us some space. (WOFF2 isn't supported by IE, but
            # that's a sacrifice I'm willing to make.)

            cache_key = ('ttf-to-woff2', content_bytes, self.build_params.font_codepoints)
            if cache_key in self.build_params.cache:
                content_bytes = self.build_params.cache[cache_key]

            else:
                subsetter = fontTools.subset.Subsetter()
                subsetter.populate(unicodes = self.build_params.font_codepoints)

                font = fontTools.ttLib.TTFont(io.BytesIO(content_bytes))
                font.flavor = 'woff2'
                subsetter.subset(font)

                buf = io.BytesIO()
                font.save(buf)
                content_bytes = buf.getvalue()
                self.build_params.cache[cache_key] = content_bytes

            mime_type = 'font/woff2'

        return (content_bytes, mime_type)




class ScriptWriter(ResourceWriter):

    def write(self, buffer, resource_list: RList):
        self._write_in_order(buffer, resource_list)

    def _write_content(self, buffer, resource_sublist: Iterable[ContentResource]):
        buffer.write('<script>\n')
        for resource in resource_sublist:
            buffer.write(resource.content)
        buffer.write('\n</script>')

    def _write_url(self, buffer, resource: UrlResource):
        src = html.escape(resource.url)
        integrity = resource.integrity_attr()
        buffer.write(f'<script src="{src}"{integrity}></script>')



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

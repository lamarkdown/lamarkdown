from .build_params import BuildParams, Resource

import os.path
import re
import urllib.request
from typing import List

_URL_SCHEME_REGEX = re.compile('[a-z]+:')


def embed(build_params: BuildParams):
    policy = build_params.embed_resources
    base_path = (build_params.resource_path or
                 os.path.dirname(os.path.abspath(build_params.src_file)))

    embed_res_list(build_params.css, build_params.css_files, policy, base_path)
    embed_res_list(build_params.js,  build_params.js_files,  policy, base_path)


def embed_res_list(embedded_resources: List[Resource],
                   linked_resources: List[Resource],
                   policy: bool,
                   base_path: str):

    i = 0
    j = 0
    while i < len(linked_resources):
        res = linked_resources[i]

        # Note: 'policy' and 'res.embed' can each be True, False or None. Hence the more explicit
        # checking below.

        link = res.value
        if (link is not None and
            ((policy is True and res.embed is not False) or
             (policy is not False and res.embed is True)) and
            not _URL_SCHEME_REGEX.match(link)):

            #if _URL_SCHEME_REGEX.match(link):
                #with urllib.request.urlopen(link) as conn:
                    ## TODO: handle exceptions, timeouts, caching, progress reporting, encoding
                    #text = conn.read().decode()
            #else:
                #with open(os.path.join(base_path, link)) as reader:
                    #text = reader.read()

            with open(os.path.join(base_path, link)) as reader:
                text = reader.read()

            # Insert rather than append, to try to maintain the ordering, which may be important.
            # That is, linked resources would occur before inline resources, and so newly-embedded
            # resources should also occur before existing inline resources.
            embedded_resources.insert(
                j,
                Resource(
                    value_factory = lambda _: text,
                    xpaths        = res.xpaths,
                    reified       = True,
                    value         = text
                )
            )
            j += 1
            linked_resources.pop(i)

        else:
            # Either:
            # (a) the resource has been filtered out, or
            # (b) the build file says not to embed, or
            # (c) the resource is remote.
            i += 1




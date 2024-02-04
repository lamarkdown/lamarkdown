# Settings and Compilation

Here we describe Lamarkdown's core functionality in detail, and how to use it.

## Build Files {#build_files}

When compiling a given Markdown file, Lamarkdown first looks for _build files_. By default, these are:

1. `md_build.py`, and/or
2. A `.py` file with the same base name as the Markdown file (e.g., for `example.md`, it would be `example.py`).

If both of these exist, both will be loaded, `md_build.py` first.

Build files contain executable Python code that makes calls to the [Build File API](api_reference.md), to apply Markdown extensions, provide document style information, and otherwise programmatically hook into the compilation process.

If build file(s) exist, but are empty, Lamarkdown will revert to the most basic syntax and functionality supported by Python-Markdown, and produce unstyled output.

However, if you run Lamarkdown _without_ a build file, it behave _as if_ the following build file was given:

```python
import lamarkdown as la
la.m.doc()
```

The [`m.doc()` build module][m.doc] adds a certain set of Markdown extensions, as well as styling the output to better resemble a conventional document. When writing a build file, you can include or omit `m.doc()`, as per your preference.

To add a Markdown extension, you call the [`lamarkdown` module][lamarkdown_call] itself. Many extensions have their own settings, which you can configure by passing keyword arguments. If you don't need to supply any extension options, you can list multiple extensions in one call:

```python
import lamarkdown as la
la('attr_list', 'admonition')
la('toc', marker = '[[TOC]]', title = 'Contents')
```

To add styling information, call [`css()`][css] or [`css_files()`][css_files]:

```python
import lamarkdown as la
la.css('''
    .note {
        border: 1px solid #0080c0;
        background: #80c0ff;
        padding: 0.5em;
    }
    ''')
la.css_files('style1.css', 'style2.css')
```

By default, CSS files provided to `css_files()` will actually be [embedded](#embedding) in the output, rather than linked, because the goal of Lamarkdown is broadly to create _standalone_ output files.

The following command-line options affect how build-files are loaded:

{-list-table}
* #
    - Option
    - Description
*   - `-b`{.nowrap} / `--build FILE`{.nowrap}
    - Load an (additional) build file.
*   - `-B`{.nowrap} / `--no-auto-build-files`{.nowrap}
    - Don't try to load the default build files (`md_build.py` or `<source>.py`), even if they exist.
*   - `-D`{.nowrap} / `--no-build-defaults`{.nowrap}
    - Even if no build files are loaded, _don't_ apply the defaults.


<!-- ## Live Updating -->

## Directives {#directives}

Lamarkdown adopts a convention, whereby authors may add specially-named attributes to parts of the document, which cause Lamarkdown (or a Lamarkdown extension) to perform certain kinds of structural transformations.

These attributes are called _directives_. Their names begin with `-` (e.g., `-label`), to distinguish them from genuine HTML attributes. Directives are (if validly specified) deleted before the final output is generated.

This approach relies on the `attr_list` or [`la.attr_prefix`][attr_prefix] extensions (designed to let authors add HTML attributes to elements). Thus, all directive processing must happen _after_ these extensions have run.

Specific directives include the following:

Directive | Description
--------- | -----------
`-caption` | With the [`la.captions`][captions] extension, this identifies the caption for a figure or table, and causes both to be wrapped (if appropriate) within a `<figure>` element.
`-list-table`{.nowrap} | With the [`la.list_tables`][list_tables] extension, and when applied to a list (containing nested lists), this converts it into a table
`-label=...`{.nowrap} | With the [`la.labels`][labels] extension, and when applied to a heading, list, figure or table, this specifies a template for the numbering of that element.
`-no-label`{.nowrap} | With the `la.labels` extension, when applied to an element, causes any labelling to be omitted.
[`-scale=...`{.nowrap}](#scaling) | When applied to an image, this scales both dimensions of the image by a linear factor.
[`-abs-scale`{.nowrap}](#scaling) | When applied to an image, this disregards any global scaling rule.

Directives have a long(er) form, starting with `md-` (e.g., `md-caption`). The short `-` form is converted to the long `md-` form during Markdown processing, so that they won't be rejected by subsequent HTML parsing. It is not generally necessary to use the long form inside Markdown documents, but it is possible.


!!! note "Design Notes"

    The `-` at the start of directives is intended to minimise confusion relative to other possible syntactic choices, while requiring no extra Markdown parsing code beyond the existing `attr_list` extension.

    It's useful to have _some_ means of distinguishing directives from ordinary HTML attributes, because:

    * The two groups have quite different semantics; and
    * We'd like to avoid possible future conflicts between the two.

    To address other possible choices:

    * Simply always using `md-` creates extra clutter.
    * Using a different special character (e.g., `!directive=...`) runs into the problem that `attr_list` converts almost all special characters to `_`, so we wouldn't be able to narrowly define which character we're actually using.
    * Using `_` itself (e.g., `_directive=...`) also seems to imply "private/internal use", especially in connection with Python.
    * Using `:` (which isn't converted to `_`) conflicts somewhat with the enclosing list syntax; e.g., in `{:directive=...}`, the the `:` will be interpreted as the start of the list, not part of the name. We could insist that authors put a space after the `{`, but this still leaves room for confusion.
    * A _trailing_ `:` would result in the syntax `directive:=...`, in which `:=` has the misleading appearance of a special operator.
    * A XML namespace (e.g., `md:directive=...`) creates extra clutter, and would also raise questions about how to formally define that namespace, and how it formally relates to HTML.
    * HTML attributes are case-insensitive, so a convention based on casing (e.g., `Directive=...`) risks unforeseen conflicts.
    * Anything more elaborate is unlikely to be recognised by `attr_list`, and would require separate parsing.


## Variants {#variants}

Lamarkdown can generate multiple output files, each with different build configuration, given a single input file.

To arrange this, call [`variants()`][variants_call] and pass in one or more functions that will configure each variant:

```python
import lamarkdown as la

def light_mode():
    # Apply to variant #1
    la.css('body { color: black; background: white; }')

def dark_mode()
    # Apply to variant #2
    la.css('body { color: white; background: black; }')

la.variants(light_mode, dark_mode)

# Apply to all variants
la.css('body { font-family: sans-serif; }')
```

You can create nested variants by calling `variants()` _within_ a variant function, though be careful to avoid infinite recursion.

Two variants may specify any arbitrarily-different options, including different Markdown extensions, and/or extension options. In such a case, Lamarkdown will invoke Python-Markdown separately for each distinct extension configuration (possibly resulting in multiple different interpretations of the same Markdown syntax, depending on the options chosen).

By default, the output filenames will have the function name appended. In the above example, if the Markdown file is `example.md`, then Lamarkdown will generate `example_light_mode.html` and `example_dark_mode.html`. If you prefer one variant to take on the "original" (unmodified) filename, call [`la.basename()`][basename] (no arguments) in the appropriate variant function.


## The `allow_exec` Option {#allow_exec}

It's currently not recommended to run Lamarkdown on untrusted documents, unless your entire execution environment is sandboxed.

Nevertheless, the `allow_exec` flag _attempts_ to provide some measure of safety in such situations. By default, `allow_exec == False`, in which case certain actions will not be permitted:

* Use of the [`la.eval`][eval] extension will be restricted to text substitutions (not code execution);
* Use of the [`la.markdown_demo`][markdown_demo] extension will be prohibited;
* Use of Matplotlib and R-plotting, by means of `m.plots()`, will be prohibited.

In general, these restrictions rely on the cooperation of relevant Markdown extensions. Thus, if you rely on `allow_exec` being `False`, you are _also_ relying on each individual extension to prohibit executable code. Non-Lamarkdown extensions won't generally even be aware of the `allow_exec` flag, so you must exercise care.

If you're just compiling your own documents, it's perfectly fine and useful to set `allow_exec == True`. There are two ways:

* Add the `-e` / `--allow-exec` command-line option; and/or
* Assign to the `allow_exec` property:

    ```python
    import lamarkdown as la

    la.allow_exec = True
    ...
    ```


## Resource Processing {#resources}

Lamarkdown performs certain transformations on parts of the HTML document _after_ Python-Markdown has finished.

!!! note "Design Notes"

    One might ask why embedding, hashing and scaling are part of Lamarkdown's core behaviour, rather than implemented as extensions.

    There are problems with designing extensions to perform these actions:

    1. They rely on identifying and modifying specific HTML elements, which requires a document tree. Python-Markdown makes such trees available during the "tree processing" stage, but some of the kinds of resources don't appear until the later "postprocessing" stage (having been represented only with special placeholder text, and otherwise kept isolated up until then).

    2. They involve styles and scripts, which are essentially outside the scope of Python-Markdown's operation altogether.


### Embedding {#embedding}

By default, Lamarkdown will embed external resources in the output HTML file (with some default exclusions). The goal is to create a _standalone_ output file, though it may be comparatively large for an HTML file.

In most cases, the resources being embedded will be CSS styles, fonts, scripts, and images. Embedding is performed automatically, by either:

* Moving the contents of directly-referenced `.css` and `.js` files into `<style>` and `<script>` elements, as appropriate, within the HTML document; or
* In other cases, converting the resource into a [data URL](https://developer.mozilla.org/en-US/docs/web/http/basics_of_http/data_urls).

Font files will be subsetted (unused characters removed) before being embedded. Styles will be _recursively_ embedded, since CSS files can reference other resources, including other CSS files. Lamarkdown will not currently attempt to resolve resources referenced by scripts, though.

Ordinary hypertext links are _not_ embedded (and not considered embeddable).

By default, Lamarkdown will also exclude audio and video files, and the contents of any `<iframe>` elements, since these could make the output unmanageably large. However, the option is open to embed these anyway if you wish.

You can provide an "embed [rule](#rules)" to override the default behaviour, if needed:

<!--```python
import lamarkdown as la

def embed_rule(url: str | None,
               tag: str | None,
               mime: str | None,
               attr: dict[str, str] | None,
               **kwargs) -> bool:
    ...


```-->

```python
import lamarkdown as la

def embed_rule(url: str | None,
               tag: str | None,
               mime: str | None,
               attr: dict[str, str] | None,
               **kwargs) -> bool:
    return ...

la.embed(embed_rule)
```

This function will be called whenever Lamarkdown encounters an embeddable resource, and must return `True` or `False`. See [Resource Rules](#rules) below for more details.

!!! note "Efficiency Notes"

    Data URLs use Base-64 encoding, which increases the size of the data by one third, rounding up, since it uses 8 bits to represent only 6 bits. This effect compounds with nested embedding.

    While a single CSS file is embedded directly in a `<style>` element, any further CSS files it imports itself will be represented as data URLs, and these in turn may have other data URLs nested inside. Lamarkdown does not (currently) try to "flatten out" CSS imports, because it cannot guarantee that this would be functionally equivalent to the original arrangement, because of certain ordering semantics defined in CSS.

    Thus, if you have several levels of indirection in your CSS imports, the resulting embedded content will be stored in a highly inefficient manner. It may be worth avoiding such arrangements.


### Hashing {#hashing}

Lamarkdown can arrange for the output document to contain a hash (SHA-256, SHA-384 or SHA-512) for each of its external resources, so the browser can [verify their integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity). This applies specifically to _non_-[embedded](#embedding) resources.

Lamarkdown does _not_ perform hashing by default. To make it do so, define a "resource hash [rule](#rules)":

```python
import lamarkdown as la

def hash_rule(url: str | None,
              tag: str | None,
              mime: str | None,
              attr: dict[str, str] | None,
              **kwargs) -> str | None:
    return ...

la.resource_hash_rule(hash_rule)
```

This function will be called whenever Lamarkdown needs to know whether and how to compute a resource hash. It must return either `None` (for no hashing) or one of the strings `'sha256'`, `'sha384'` or `'sha512'`, representing corresponding hashing algorithms. See [Resource Rules](#rules) below for more details.

Where a hash is required, Lamarkdown will _assume_ that the currently-available version of the resource is the one you want, and will compute a hash based on it. The hash will appear as the value of the `integrity` HTML attribute in the output document. Lamarkdown will not compare the hash to anything; this will be left up to the browser, when the document is loaded by readers in the future.

<!--{.note}
Hashing is not available for embedded resources. Any adversary able to modify an embedded resource in the output document could simply also modify the hash.-->

Hashing is a compromise between the control afforded by embedding, and the smaller file sizes offered by not embedding. Embedding may (depending on the particular files) significantly increase the file size of the output document. But with non-embedded, non-hashed resources, you must _trust_ the external source(s), because you are ceding control over aspects of the document. For instance, if your document links to `http://example.com/image.jpg`, then your document will show _whatever_ that image is at the time. If/when the image is replaced on the server, your document will show the new version, and for a reader, there won't be any sign that it's not the original.

The same and worse could happen for stylesheets and scripts. An external entity with control over a stylesheet or script in your document could choose to disable or arbitrarily modify your entire document remotely, for anyone reading it. With embedded or hashed resources, these are no longer possibilities.

However, resource hashing lacks other advantages of embedded resources:

* Readers require an internet connection to view hashed resources, and must wait a moment for them to load, while embedded resources will be available offline and practically instantaneously.
* An external entity (controlling a hashed resource) might be able to track readers of the document, by recording requests for the document's external resource(s) and mapping them to readers' IP addresses.
* Hashing won't protect the document against its resources being moved or deleted.

There's also a chance that you may _want_ the external source to be able to change the resource arbitrarily. In this case, a non-embedded, non-hashed resource would be appropriate.


### Scaling {#scaling}

Lamarkdown can adjust the size of images in a document by a linear scaling factor. This applies to any mechanism for generating or inserting images; e.g.:

* The standard Markdown notation: `![Alt text](http://example.com/image.jpg)`.
* Latex code compiled into SVG using the [`la.latex`][latex] extension.
* SVGs produced by Graphviz, matplotlib, etc., via the [`m.plots`][m.plots] build module.
* Anything else that creates `<svg>` or `<img>` elements.

For any given image, there are (potentially) two different scaling factors:

* You can give a per-image scaling factor using the `-scale=...` directive; e.g.:

    ```markdown
    ![Alt text](http://example.com/image.jpg){-scale="2.5"}
    ```

* You can define a "scale [rule](#rules)":

    ```python
    import lamarkdown as la

    def scale_rule(url: str | None,
                   tag: str | None,
                   mime: str | None,
                   attr: dict[str, str] | None,
                   **kwargs) -> float | int:
        return ...

    la.scale_rule(scale_rule)
    ```

    This function is called for each image in the document (or at least the body of the document). It must return a `float` or `int` representing a scaling factor. See [Resource Rules](#rules) below for more details.

These two numbers (both 1 by default) are _multiplied_ to get the actual scaling factor for a given image. So, if an image has `{-scale="2"}`, and the scale rule returns 3, then the image will be scaled by a factor of 6. That is, _unless_ the `-abs-scale` directive is given. This will cause the scale rule to be ignored, so that:

* For `{-scale="2" -abs-scale}`, the image will be scaled by a factor of 2, irrespective of the scale rule; and
* For `{-abs-scale}`, the image won't be scaled at all.

Scaling only alters the size information present in the HTML document. It _doesn't_ affect the actual image content, and so it applies equally to embedded and linked images, and to (practically) any image format supported by web browsers.

However, Lamarkdown only scales "absolutely"-sized images---those whose sizes are given in units of pixels, points, millimetres, inches, etc. Scaling will not be done to images whose sizes expressed in relative units like, `em` (relative to the font size), `%` (relative to the parent element's size) and similar. We assume that relative units express the user's final preference for how large an image should be. (Relative units are unlikely to be present unless the user, or the author of a build module, has explicitly added them.)

### Resource Rules {#rules}

Resource rule functions are defined within build files and supplied to one of [`embed_rule()`][embed_rule], [`resource_hash_rule()`][resource_hash_rule] or [`scale_rule()`][scale_rule] as appropriate. Lamarkdown will then call the function for each of various resources (images, etc.) that _may_ need to be embedded, hashed, or scaled.

Such functions can accept the following keyword parameters, to help them determine what kind of resource they are dealing with, and so decide what to do with it:

Parameter       | Type              | Description
---------       | -----             | -----------
`url`           | string or `None`  | The location of the resource; e.g., `https://example.com/image.jpg`.
`tag`           | string or `None`  | The HTML tag of the element representing the resource; e.g. `img`, `style`, etc.
`mime`          | string or `None`  | The [MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types) of the resource; e.g., `image/png`, `text/css`, etc. This _may_ be the result of probing the resource's content.
`attr`          | string-to-string dictionary or `None` | Any attributes assigned to the enclosing HTML element.

Each of these may be `None` in certain circumstances, and a rule function must be designed accordingly, with appropriate default behaviour.

A rule function _should_ also accept a `**kwargs` parameter, for future-proofing, should a future version of Lamarkdown provide additional keyword arguments.

A rule function returns a value specific to the type of processing it governs: embed rules return `bool`, hasing rules return `str` or `None`, and scale rules return `float` or `int`.


## Caching {#caching}

To avoid unnecessary delays during compilation, Lamarkdown uses two caches:

* The "build cache" stores results of certain time-consuming processing, particularly the output of external commands like LaTeX (by the [`la.latex` extension][latex]). The build cache is kept in the "build directory", which (by default) is `./build/`. If necessary, you can cause Lamarkdown to delete any pre-existing entries in the build cache with the `--clean` option:

    ```console
    $ lamd --clean mydocument.md
    ```

* The "fetch cache" stores downloaded files, obeying (at a basic level) directives received via the "Cache-Control" HTTP header. That is, cache entries will expire automatically after a period of time determined by the server (24 hours by default).

    Lamarkdown downloads and caches files for several purposes; e.g.:

    * To embed files (stylesheets, fonts, images, etc.);
    * To compute hashes of linked (non-embedded) files, if asked to;
    * To find the original dimensions of linked images, when asked to scale them.

    The fetch cache is _not_ cleared with the `--clean` option. However, it is safe to manually delete, if you wish. You can determine its location using `-v`:

    ```console
    $ lamd -v
    ```

    The fetch cache is stored in the standard location for user-level caches, and so is reused across all Lamarkdown documents for a given user on a given machine.



[attr_prefix]:          extensions/attr_prefix.md
[captions]:             extensions/captions.md
[cite]:                 extensions/cite.md
[eval]:                 extensions/eval.md
[labels]:               extentions/labels.md
[latex]:                extentions/latex.md
[list_tables]:          extentions/list_tables.md
[markdown_demo]:        extentions/markdown_demo.md
[sections]:             extentions/sections.md

[lamarkdown_call]:      api.md#lamarkdown_call
[basename]:             api.md#basename
[css]:                  api.md#css
[css_files]:            api.md#css_files
[embed_rule]:           api.md#embed_rule
[resource_hash_rule]:   api.md#resource_hash_rule
[scale_rule]:           api.md#scale_rule
[variants_call]:        api.md#variants

[m.doc]:                modules/doc.md
[m.plots]:              modules/plots.md

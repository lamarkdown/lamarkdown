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


<!--(Built-in [output directives](directives.md) always remain available in principle, though the basic version of markdown syntax only provides one way to use them: as attributes on inline HTML elements.)-->

<!--In summary, with a build file, you can:

* Define which markdown extensions are to be applied, and provide configuration options to them.

* Define CSS and JavaScript code (and/or external .css/.js files) to be applied to the HTML.

* Define a set of [variants](variants.md) (multiple output documents) to be built from a single source .md file.

* Structurally modify and query the document via CSS selectors and XPath expressions (useful when combined with multiple variants).

{: .note}
[Extensions](extensions/index.md) are the extensibility mechanism provided by Python-Markdown, which extend or alter the syntax of the `.md` files. By contrast, "build files" control the entire build process.-->

The following command-line options affect how build-files are loaded:

{ :list-table }
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

These attributes are called _directives_. Their names begin with `:` (e.g., `:labels`), to distinguish them from genuine HTML attributes. Directives are (if validly specified) deleted before the final output is generated.

This approach relies on the `attr_list` or [`la.attr_prefix`][attr_prefix] extensions (designed to let authors add HTML attributes to elements). Thus, all directive processing must happen _after_ these extensions have run.

Specific directives include the following:

Directive | Description
--------- | -----------
`:caption` | With the [`la.captions`][captions] extension, this identifies the caption for a figure or table, and causes both to be wrapped (if appropriate) within a `<figure>` element.
`:list-table`{.nowrap} | With the [`la.list_tables`][list_tables] extension, and when applied to a list (containing nested lists), this converts it into a table
`:labels=...`{.nowrap} | With the [`la.labels`][labels] extension, and when applied to a heading, list, figure or table, this specifies a template for the numbering of that element.
`:no-label`{.nowrap} | With the `la.labels` extension, when applied to an element, causes any labelling to be omitted.
[`:scale=...`{.nowrap}](#scaling) | When applied to an image, this scales both dimensions of the image by a linear factor.
[`:abs-scale`{.nowrap}](#scaling) | When applied to an image, this disregards any global scaling rule.


!!! warning

    When a directive is the first or only part of an attribute list, you must insert a space or an extra `:` before the directive name; e.g., `{ :directive=...}` or `{::directive=...}`.

    If you write `{:directive=...}`, the `:` will be interpreted as part of the enclosing list syntax. Markdown attribute lists start with `{` or `{:`.

    !!! note "Design Notes"

        Despite the above warning, the use of `:` as a directive prefix is intended to minimise confusion relative to other possible syntactic choices, while requiring no extra parsing code beyond the existing `attr_list` extension.

        To address other possible designs:

        * Using a different special character (e.g., `!directive=...`) might work, but almost all special characters (including `!`) are converted to `_`, so we wouldn't be able to narrowly define which character we're actually using.
        * Using `_` itself would also seem to imply "private/internal use", especially in connection with Python.
        * Using `-` is possible, but may not convey the idea of a directive.
        * A _trailing_ `:` could be used, but would result in the syntax `directive:=...`, in which `:=` has the appearance of a special operator, and doesn't necessarily convey the idea of a directive either.
        * A XML-like "namespace" could be used (e.g., `x:directive=...`), but this creates extra clutter.
        * HTML attributes are case-insensitive, so a convention based on casing (e.g., `Directive=...`) may not be technically workable.
        * Anything more elaborate is unlikely to be recognised by `attr_list`, and would require separate parsing.

        It is possible that a future version of Lamarkdown will add an alternate way of specifying directives.

<!--

FIXME:

Actually starting with '-' makes more sense than ':', because it avoids the clash with the list syntax. Let's change this in the code.

There is still a minor theoretical issue, in that neither '-' nor ':' are technically valid as starting characters in XML attributes, and so _theoretically_ might also be disallowed inside a Document Object Model. But Python's xml.etree seems to allow it, and I can't see them changing the API without providing backwards compatibility. Even if it was changed in the future, we could choose that moment to add additional parsing logic to compensate.

So, we'll have:

-caption
-list-table
-label=...
-no-label
-scale=...
-abs-scale

And thus we can have... {-caption}, for instance.


-->


## Variants {#variants}

Lamarkdown can generate multiple output files, each with different build configuration, given a single input file.

To arrange this, call `variants()` and pass in one or more functions that will configure each variant:

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

You can create nested variants by calling [`variants()`][variants-call] _within_ a variant function, though be careful to avoid infinite recursion.

Two variants may specify any arbitrarily-different options, including different Markdown extensions, and/or extension options. In such a case, Lamarkdown will invoke Python-Markdown separately for each distinct extension configuration (possibly resulting in multiple different interpretations of the same Markdown syntax, depending on the options chosen).

By default, the output filenames will have the function name appended. In the above example, if the Markdown file is `example.md`, then Lamarkdown will generate `example_light_mode.html` and `example_dark_mode.html`. If you prefer one variant to take on the "original" (unmodified) filename, call [`la.basename()`][basename] (no arguments) in the appropriate variant function.


## The `allow_exec` Option {#allow_exec}

It's currently not recommended to run Lamarkdown on untrusted documents, unless your entire execution environment is sandboxed.

Nevertheless, the `allow_exec` flag exists to provide some measure of safety in such situations. By default, `allow_exec == False`, in which case certain actions will not be permitted:

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


## Embedding {#embedding}

By default, Lamarkdown will embed external resources in the output HTML file (with some default exclusions). The goal is to create a _standalone_ output file, though it may be comparatively large for an HTML file.

In most cases, the resources being embedded will be CSS styles, fonts, scripts, and images. Embedding is performed automatically, by either:

* Moving the contents of `.css` and `.js` files into `<style>` and `<script>` elements, as appropriate, within the HTML document; or
* In other cases, converting the resource into a [data URL](https://developer.mozilla.org/en-US/docs/web/http/basics_of_http/data_urls).

Font files will be subsetted (unused characters removed) before being embedded. Styles will be _recursively_ embedded, since CSS files can reference other resources, including other CSS files. Lamarkdown will not currently attempt to resolve resources referenced by scripts, though.

Ordinary hypertext links are _not_ embedded. By default, Lamarkdown will also exclude audio or video files (since they could make the output unmanageably large), and the contents of any `<iframe>` elements.

You can provide an "embed rule" to override the default behaviour, if desired:

```python
import lamarkdown as la

def embed_rule(...)
```

## Hashing {#hashing}


## Scaling {#scaling}



## Caching {#caching}

To avoid unnecessary delays during compilation, Lamarkdown uses two caches:

* The "build cache" stores results of certain time-consuming processing, particularly the output of external commands like LaTeX (by the [`la.latex` extension](extensions/latex.md)). The build cache is kept in the "build directory", which (by default) is `./build/`. If necessary, you can cause Lamarkdown to delete any pre-existing entries in the build cache with the `--clean` option:

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



[attr_prefix]:      extensions/attr_prefix.md
[captions]:         extensions/captions.md
[cite]:             extensions/cite.md
[eval]:             extensions/eval.md
[labels]:           extentions/labels.md
[latex]:            extentions/latex.md
[list_tables]:      extentions/list_tables.md
[markdown_demo]:    extentions/markdown_demo.md
[sections]:         extentions/sections.md

[lamarkdown_call]:  api.md#lamarkdown_call
[basename]:         api.md#basename
[css]:              api.md#css
[css_files]:        api.md#css_files
[variants_call]:    api.md#variants

[m.doc]:            modules/doc.md
[m.plots]:          modules/plots.md

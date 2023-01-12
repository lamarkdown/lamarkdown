# Build Files

Lamarkdown uses "build files" to customise the build process. Normally these are `md_build.py`, and/or a `.py` file with the same base name as the `.md` document being compiled.

Build files are able to:

* Define which markdown extensions are to be applied, and provide configuration options to them. (It is assumed that the user will have installed any desired extensions already, though Python-Markdown comes with various standard extensions, and Lamarkdown provides a few of its own.)

* Define CSS and JavaScript code (and/or external .css/.js files) to be applied to the HTML.

* Define a set of _variants_ (multiple output documents) to be built from a single source .md file.

* Structurally modify and query the document via CSS selectors and XPath expressions (useful when combined with multiple variants).

(Note: "extensions" are the extensibility mechanism provided by Python-Markdown, which extend or alter the syntax of the `.md` files. By contrast, "build files" control the entire build process.)

## Loading

You do not strictly need to write any build files. If none are found, Lamarkdown will substitute a set of opinionated default options. (These defaults _only_ apply if no build files are loaded, though.)

Lamarkdown will automatically try to load two build files, if they exist:

* `md_build.py`, in the same directory as the source .md file (the "directory build file").
* A `.py` file with the same base name (i.e., minus the `.md` extension) as the source .md file (the "document build file").

For instance, when compiling `/path/to/mydocument.md`, Lamarkdown will try to load `/path/to/md_build.py` and `/path/to/mydocument.py`. If both these .py files exist, both will be loaded, `md_build.py` first. The intention is that `md_build.py` represents a set of common options shared amongst several markdown documents in the same directory.

You can specify zero or more additional build files on the command-line using the `-b`/`--build` option:

`$ lamd -b extra_build.py mydocument.md`

And you can disable loading of the two normally-automatic build files using `-B`/`--no-auto-build-files`. You can also disable the opinionated default options using `-D`/`--no-build-defaults`. In the absence of any build files, this causes Lamarkdown to not load any Python-Markdown extensions, and produce a raw, unstyled (though still complete) HTML output document.

## Basic Contents

A simple build file may look like this:

```python
import lamarkdown as la
la.doc()
la.css(r'''
    p {
        color: blue;
    }
''')
```

That is, build files contain Python code. The `lamarkdown` package provides a series of functions for specifying compilation options. In this case:

* "`doc()`" invokes a pre-defined bundle of settings intended to create something recognisable as a document.
* "`css(...)`" adds a css rule (or collection of rules) to the output document.

The complete set of available functions are described below under "Build API".


## Predefined Settings

As mentioned above, the `doc()` function adds CSS styling to produce professional document-like output. It also loads a range of standard Python-Markdown extensions, a couple of [PyMdown-Extensions](https://facelessuser.github.io/pymdown-extensions/), and several extensions that come with Lamarkdown itself.

Among other things, `doc()` loads the Python Markdown [`toc`](https://python-markdown.github.io/extensions/toc/) (table-of-contents) extension. _If_ the `.md` file contains the placeholder `[TOC]`, then `toc` generates a table-of-contents, and `doc()` will cause it to appear as a separately-scrolling sidebar (or in-place if the document is printed).

There are a few more high-level bundles of settings:

* `cmd()`: Adds CSS styling for example UNIX/Windows/other command-lines.

    ```python
    import lamarkdown as la
    la.cmd()
    ```
    ```markdown
    # Markdown Document
    
    `./gradlew run`
    {.wincmd}

    `./configure`
    `make`
    `make install`
    {.unixcmd}
    ```

* `code()`: Adds CSS styling for syntax-highlighted code (as produced by [Pygments](https://pygments.org/), which is invoked through either the [`codehilite`](https://python-markdown.github.io/extensions/code_hilite/) or [`pymdownx.superfences`](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/) extensions).

    (This is essentially a single fixed syntax highlighting theme. You can use any other colour scheme via the `css()` or `css_files()` functions below, perhaps generated from the [`pygmentize` command](https://pygments.org/docs/cmdline/) with the `-S` switch.)

* `page_numbers(pageHeight = 1200)`: Adds pseudo-page numbers to the output document. This is essentially just a kind of ruler down the right-hand-side of the document, with "page numbers" marked at regular intervals (`pageHeight` pixels).

* `heading_numbers(from_level = 2, to_level = 6)`: Adds decimal numbering (through CSS styling) to a range of heading levels, by default 2--6. That is, <h2\> elements (or whichever level is given by `from_level`) will be numbered 1, 2, 3, etc., while <h3\> elements will be numbered 1.1, 1.2, etc.

* `teaching()`: Adds styles relevant to tests or other assessments, particularly for showing mark allocations via the `nmarks` attribute), and answers.


## Build API

The `lamarkdown` package also provides the following lower-level functions, for greater control:


### Markdown extensions

* `extensions(*ext)`:
    Applies one or more markdown extensions, either by name (e.g., `lamarkdown.ext.latex`) or by object reference (if you have instantiated the extension yourself).

* `extension(name, **config)`:
    Applies a single markdown extension by name (if not already applied) and also sets its configuration options using keyword parameters. Moreover, this function _returns_ a live `dict` containing the configuration options, so that existing ones can be queried and/or amended asynchronously.

    (Note that this function does not accept already-instantiated extensions, only names.)


### Styling and scripting (resources)

* `css(value, if_xpaths = [], if_selectors = [])`:

    Adds a snippet of CSS code (assumed to be one or more CSS rules) to the output document, within `<style>` tags.

    If `if_xpaths` or `if_selectors` are non-empty, then these are first matched against the output HTML to determine whether or not to include the CSS. `if_xpaths` must be a list of XPath expressions, and `if_selectors` must be a list of CSS selectors. The CSS code will be included if _any_ of the XPath expressions or CSS selectors match (or if none are specified), and omitted otherwise. This feature is intended for the development of reusable build modules.

    For instance, calling `css('li { color: blue; }', if_selectors=['li'])` will include "`li { color: blue; }`" in the output document style, but only if the `li` selector matches something (i.e., if there are any `<li>` elements).

    (It's important to distinguish what's happening here from what the web browser itself will do. The browser will execute all the CSS rules it receives as part of the HTML document. However, the processing described here happens at "compile-time", and determines which CSS rules will _exist_ in the HTML document to begin with.)

    `value` is generally a string representing the CSS code. However, it can alternatively be a function returning a string, taking as a parameter the subset of XPath expressions that matched the document. If so, it will be called unconditionally and its return value used if not `None`.

* `css_rule(selectors, properties)`:

    A convenience function that takes a list of CSS `selectors`, and a string containing one or more CSS property declarations, and builds a single CSS rule, which will adapt to the output document. The set of selectors _actually present_ in the output will be the subset of `selectors` that match the document. If none of them match, the rule will be omitted altogether.

* `css_files(*values, if_xpaths = [], if_selectors = [])`:
    Adds one or more external `.css` style files at specified URLs. Only the URLs will be inserted into the output document (using `<link href="...">` tags).

    The `if_xpaths` and `if_selectors` parameters have the same meaning as for the `css()` function. Each of the `values` is either a string, or a function returning a string.

* `js(value, if_xpaths = [], if_selectors = [])`:
    Adds a snippet of JavaScript code to the end of the output document, within `<script>` tags. The `if_xpaths` and `if_selectors` parameters have the same meaning as for the `css()` function. `value` can be either string, or a function returning a string.

* `js_files(*values, if_xpaths = [], if_selectors = [])`:
    Adds one or more external `.js` script files at specified URLs. Only the URLs will be inserted into the output document (using `<script src="...">` tags).

    The `if_xpaths` and `if_selectors` parameters have the same meaning as for the `css()` function. Each of the `values` is either a string, or a function returning a string.

* `embed_resources(embed = True)`:
    If `embed` is `True`, local files specified with `css_files()` and `js_files()` will be read at compile time and their contents (rather than just links to them) will be written into the output file. This can also be achieved on a case-by-case basis by providing an `embed` keyword parameter to `css_files()` or `js_files()`.

    The allowable values of `embed` (both globally and locally) are `True`, `False` and `None`. Embedding will take place if at least _one_ of the global or local settings is `True`, and _neither_ of them is `False`.

    Note: remote resources (those specifying a full URL) _will not_ be embedded even if this option is turned on. Also, no attempt is made to embed transitive resources, such as those loaded by a CSS `@import` rule, or a JavaScript `fetch()` function. These are left as-is (and a general-purpose way of embedding these may not necessarily be feasible).


### Variants

* `variants(*variant_fns)`:
    Defines a set of [variants](variants). The parameters must be functions (or callable objects), each of which, when called, should make further API calls. Each of these functions thus defines a "variant", and Lamarkdown will compile a separate output file for each variant according to its particular configuration.

    Variants will all share the common settings defined globally. Nested variants are permitted too; one can call `variants()` from within a variant function, and those sub-variants will share the settings of their "parent".

    Generally you will want to specify at least two variants whenever calling `variants()`. Specifying only one is permitted, but is essentially no different to not using the facility at all.

* `target(fn)`:
    Specifies a function for determining the output name. Without any variants, the default output file is simply the input file with `.md` replaced by `.html`. _With_ variants, the default is to add the variant name to each output file, with a separator, just before the extension. Thus, compiling `mydoc.md` with `variantA` and `variantB` will (by default) result in `mydoc_variantA.html` and `mydoc_variantB.html`.

    Calling `target()` can change this behaviour arbitrarily. The function `fn` must accept the originally conceived output filename (generally ending in `.html`) and return the name to be used by this variant.

    Keep in mind that the same build logic might be used across several different input documents; hence why `target()` accepts a function and not just a string.

* `base_name()`:
    Equivalent to calling `target(lambda t: t)`. That is, this causes a particular variant to have the original default output name. Obviously only one variant should call `base_name()`; it should not be used at the global level.

Also see the functions below for ways to create structural differences between variant documents.


### Document modification and querying

* `prune(selector = None, xpath = None)`:
    Delete parts of the document tree that match either a CSS selector or an XPath expression.

    This is especially intended to help create structurally different variants of the document. For instance, one variant could call `prune('.answers')` to delete all HTML elements with `class="answers"`, while another one could retain it. This would allow you to build both a question paper and answer guide from the same input, provided you attach `class="answers"` to the right parts of the document (e.g., via the [`attr_list`](https://python-markdown.github.io/extensions/attr_list/) or [`admonition`](https://python-markdown.github.io/extensions/admonition/) extensions.).

* `with_selector(selector, fn)`:
    Runs function `fn` on each element of the document tree matching the given CSS selector. The function may query or arbitrarily modify the tree.

    (Lamarkdown uses the [`lxml` API](https://lxml.de/) for this, which is an extension of the standard `xml.etree.ElementTree` interface.)

* `with_xpath(xpath, fn)`:
    Like `with_selector()`, but accepts XPath expressions in place of CSS selectors.

* `with_tree(fn)`:
    Runs function `fn` on the root of the document tree.

* `wrap_content(start, end)`:
    Adds arbitrary HTML code on either end of the output generated by Python Markdown. This may be necessary to support certain JavaScript frameworks like RevealJS.

    Multiple calls will accumulate additional HTML code around the outside of what has already been specified.

* `wrap_content_inner(start, end)`:
    The same as `wrap_content()`, except that multiple calls will place new HTML _inside_ previously-specified wrapping code, immediately around the Python Markdown output.


### Other queries

* `get_build_dir()`:
    Returns the directory that Lamarkdown uses for temporary build-related files.

* `get_env()`:
    Returns the dictionary that (for the moment) is used by the `lamarkdown.ext.eval` extension to permit the embedding and execution of Python expressions directly within `.md` files.

* `get_params()`:
    Returns the `BuildParams` object encapsulating the complete set of arguments to the build process (apart from the actual markdown code).

# Build File API Reference

The `lamarkdown` package provides the following functionality, to be accessed from [build files][] and [build modules][]:


## Extension Loading and Configuration



### `lamarkdown.__call__(*extensions, **config)`  { #lamarkdown_call }
    
Applies one or more markdown extensions. You may either:

1. Provide one or more extension names and/or `markdown.extensions.Extension` objects _without_ config options:

    ```python
    import lamarkdown as la
    la('attr_list', 'nl2br', 'toc', 'la.cite', 'pymdownx.extra')
    ```


2. Provide one extension name with associated config options.

    ```python
    import lamarkdown as la
    la('la.latex', tex = 'pdflatex', pdf_svg_converter = 'inkscape')
    ```
    
You can specify a given extension multiple times (by name). It will only be loaded once, but its config options will accumulate.
    
To provide config options to multiple extensions, you must call them all individually. To provide config options to a `markdown.extensions.Extension` object (which you may have if you create your own extensions), you must pass them directly to the extension's constructor.

`__call__()` also returns a live `dict` containing the configuration options, so that existing options can be queried and/or amended separately.


### `lamarkdown.extendable(value, join = '')`

Wraps a configuration value, causing it to be extended, rather than overwritten, if/when another value is given later (for the same option).

Normally, re-specifying a given config option will cause it to be overwritten:

```python
import lamarkdown as la
la('the.extension', opt1 = 'hello', opt2 = [1, 2, 3])
la('the.extension', opt1 = 'world', opt2 = [4, 5, 6])
# 'opt1' will be 'world', opt2 will be [4, 5, 6]
```

If you wrap a value using `extendable()`, then:

* If it's a string, successive values will concatenate, separated by the value of `join`;
* If it's a `list`, `set` or `dict`, any existing value will be extended/updated by a new value (using the container's `extend()` or `update()` method as appropriate).

Thus:
```python
import lamarkdown as la
la('the.extension', opt1 = la.extendable('hello', join = ' '), 
                    opt2 = la.extendable([1, 2, 3]))
la('the.extension', opt1 = 'world', opt2 = [4, 5, 6])
# 'opt1' will be 'hello world', opt2 will be [1, 2, 3, 4, 5, 6]
```

Moreover, providing an `extendable` value will preserve any existing non-wrapped value:
```python
import lamarkdown as la
la('the.extension', opt1 = 'hello', opt2 = [1, 2, 3])
la('the.extension', opt1 = la.extendable('world', join = ' '), 
                    opt2 = la.extendable([4, 5, 6]))
# 'opt1' will be 'hello world', opt2 will be [1, 2, 3, 4, 5, 6]
```

It is safe (if unnecessary) to provide `extendable` multiple times for a single config option.

To override the effects of `extendable`, you can directly manipulate the `dict` returned by `__call__()`:
```python
import lamarkdown as la
la('the.extension', opt1 = la.extendable('hello'), 
                    opt2 = la.extendable([1, 2, 3]))

opts = la('the.extension')
opts['opt1'] = 'hello' # non-extendable
del opts['opt2']

la('the.extension', opt1 = 'world', opt2 = [4, 5, 6])
# 'opt1' will be 'world', opt2 will be [4, 5, 6]
```


### `lamarkdown.late(value_callback)`

Lets you provide a callback returning a value, rather than a direct value, for an extension config option. The callback will be invoked at the last opportunity, after all build files have been processed, and right before Lamarkdown invokes Python Markdown.

```python
import lamarkdown as la
la('the.extension', opt = la.late(lambda: 'hello'))
```

This may be useful when writing a build module, to make a particular config option refer to other parts of the configuration.

`late` values are compatible with `extendable` values:
```python
import lamarkdown as la
la('the.extension', opt = la.extendable(la.late(lambda: 'hello'), join = ' '))
la('the.extension', opt = 'world'))
# opt will be 'hello world'
```

{: .note}
Some extensions accept functions as config values. So, for extension config purposes, Lamarkdown will _only_ call functions wrapped using `late()`.


## Styling and Scripting (Resources)

### `lamarkdown.css(value, if_xpaths = [], if_selectors = [])`

Adds a snippet of CSS code (assumed to be one or more CSS rules) to the output document, within `<style>` tags.

If `if_xpaths` or `if_selectors` are non-empty, then these are first matched against the output HTML to determine whether or not to include the CSS. `if_xpaths` must be a list of XPath expressions, and `if_selectors` must be a list of CSS selectors. The CSS code will be included if _any_ of the XPath expressions or CSS selectors match (or if none are specified), and omitted otherwise. This feature is intended for the development of reusable build modules.

For instance, calling `css('li { color: blue; }', if_selectors=['li'])` will include "`li { color: blue; }`" in the output document style, but only if the `li` selector matches something (i.e., if there are any `<li>` elements).

{: .note}
It's important to distinguish what's happening here from what the web browser itself will do. The browser will execute all the CSS rules it receives as part of the HTML document. However, the processing described here happens at "compile-time", and determines which CSS rules will _exist_ in the HTML document to begin with.

`value` is generally a string representing the CSS code. However, it can alternatively be a function returning a string, taking as a parameter the subset of XPath expressions that matched the document. If so, it will be called unconditionally and its return value used if not `None`.

### `lamarkdown.css_rule(selectors, properties)`

A convenience function that takes a list of CSS `selectors`, and a string containing one or more CSS property declarations, and builds a single CSS rule, which will adapt to the output document. The set of selectors _actually present_ in the output will be the subset of `selectors` that match the document. If none of them match, the rule will be omitted altogether.

### `lamarkdown.css_files(*values, if_xpaths = [], if_selectors = [])`
    
Adds one or more external `.css` style files at specified URLs. Only the URLs will be inserted into the output document (using `<link href="...">` tags).

The `if_xpaths` and `if_selectors` parameters have the same meaning as for the `css()` function. Each of the `values` is either a string, or a function returning a string.

### `lamarkdown.js(value, if_xpaths = [], if_selectors = [])`
    
Adds a snippet of JavaScript code to the end of the output document, within `<script>` tags. The `if_xpaths` and `if_selectors` parameters have the same meaning as for the `css()` function. `value` can be either string, or a function returning a string.

### `lamarkdown.js_files(*values, if_xpaths = [], if_selectors = [])`

Adds one or more external `.js` script files at specified URLs. Only the URLs will be inserted into the output document (using `<script src="...">` tags).

The `if_xpaths` and `if_selectors` parameters have the same meaning as for the `css()` function. Each of the `values` is either a string, or a function returning a string.


<!--## Media

Lamarkdown performs certain operations on font, images and other embedded or linked files. See [Fonts and Media](fonts_and_media.md) for a general discussion of how this works. 

In the following sections, we refer to "rules". A rule is a callback function that returns an operation-specific value, and takes (some of) the following keyword parameters:

`url`
: the URL of the external resource (`str`); e.g., `OpenSans.ttf`, `http://example.com/image.png`.

`type`
: the media (MIME) type (`str`); e.g., `font/ttf`, `image/gif`.

`tag`
: the name of the enclosing HTML element (`str`); e.g., `img`, `style`.

`attr`
: the HTML attributes of the enclosing element (`dict`).

A rule callback _must_ provide its own default value for each parameter, because the caller will omit a parameter when its value is not available. The callback should also define `**kwargs`, for forward compatibility.-->



### `lamarkdown.embed(embed_rule)`

Specifies which external resources to embed in the output document (of those not already embedded by some other mechanism).

If `embed_rule` is simply `True` or `False`, then Lamarkdown will embed everything, or nothing, respectively. For more fine-grained control, `embed_rule` can be a rule callback returning `True` or `False`. 

For example, to embed only JPEG images:
```python
import lamarkdown as la
la.embed(lambda url = '', type = '', **kwargs: url.endswith('.jpg') or type == 'image/jpeg')
```


### `lamarkdown.scale(scale_rule)`

Specifies a scaling factor to use across all `<img>` and `<svg>` elements in the document.

If `scale_rule` is simply a number, then Lamarkdown will uniformly scale all images by that amount. For more fine-grained control, `scale_rule` can be a rule callback returning a scaling factor.


### `lamarkdown.resource_hash_type(hash_rule)`

Specifies either a hashing algorithm (or `None`) to use for remotely-linked files, to verify that such files haven't been manipulated when opening the document.

If `hash_rule` is `'sha256'`, `'sha384'` or `'sha512'`, then that algorithm is used across all remotely-linked files. If `hash_rule` is None, then such hashing is globally disabled. For more fine-grained control, `hash_rule` can be a rule callback that returns `'sha256'`, `'sha384'`, `'sha512'` or `None`.

{: .warning}
There's no way to automatically check the integrity of remote files during compilation, when the hashes are first computed.


## Variants

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


## Document Modification and Querying

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


## Other Queries

* `get_build_dir()`:
    Returns the directory that Lamarkdown uses for temporary build-related files.

* `get_env()`:
    Returns the dictionary that (for the moment) is used by the `lamarkdown.ext.eval` extension to permit the embedding and execution of Python expressions directly within `.md` files.

* `get_params()`:
    Returns the `BuildParams` object encapsulating the complete set of arguments to the build process (apart from the actual markdown code).


[build files]: core.md#build_files
[build modules]: modules/index.md

---
title: Output Processing
nav_order: 30
has_children: true
---

# Output Processing

Lamarkdown contains several mechanisms to affect the style and structure of the output document. These help close the gap between the raw HTML output of the core Python-Markdown engine, and a fully-styled, standalone document (as one expects from Latex, for instance).

Output processing is controlled by _output directives_ and _output rules_. Directives are embedded within a `.md` file, and apply to specific elements of the document. Rules are given within a [build file](../build_files), and specify a general logic (written in Python code) that applies in all cases. Directives _generally_ override rules, though they may also interact (as in the case of image scaling).


## Output Directives

These are temporary HTML attributes embedded within a markdown document, which specify certain output characteristics. They have names starting with "`:`", and can be set (on specific parts of a document) using any existing means of setting HTML attributes; e.g.:

* Using [`attr_list`](https://python-markdown.github.io/extensions/attr_list/) (a standard Python-Markdown extension):

    ```markdown
    An example paragraph.
    {::exampledirective1="value1" :exampledirective2="value2"}
    ```
    
* Using [`attr_prefix`](extensions/attr_prefix.md) (a Lamarkdown extension):

    ```markdown
    {::exampledirective1="value1" :exampledirective2="value2"}
    An example paragraph.
    ```

{:.note}
> The double-colon "`::`" above comprises one colon to begin the attribute list (`{:`...`}`) and one colon to begin the directive name (`:exampledirective1`).
> 
> Lamarkdown's directives do not alter the Markdown language on their own, though they do require an extension like `attr_list` or `attr_prefix` to provide the syntax for setting them. Real HTML attributes cannot legally begin with a colon "`:`".

Some directives are built-in (such as `:label`, `:scale`, `:abs-scale`, `:embed` and `:hash`), and are available regardless of which extensions are loaded. Other directives may be provided by extensions or build modules, for their own purposes.


## Output Rules

Rules are Python callback functions (or callable objects), defined in build files (or modules), that specify certain output characteristics _generally_. Rules can be set using the `ol_label()`, `ul_label()`, `scale()`, `embed()` and `hash()` [API functions](../api_reference.md), passing the rule function as a parameter.

Rules are applied to (called for) relevant elements in the output document. For each call, the rule function will receive information about the element, and must return a value indicating what approach to take.

For a given output document, there is only _one_ label rule, _one_ scaling rule, etc., but each rule may contain arbitrary logic, based on various pieces of information. For instance, consider the following build logic:

```python
import lamarkdown as la
la.ol_label(lambda **k: 'A.')
la.embed(lambda url = '', **k: url.lower().endswith('.jpg'))
```

The above will set all ordered list labels to uppercase-alphabetic ("A.", "B.", "C.", etc.), and will embed all files whose names ending in `.jpg` (except where overridden by a directive).

The parameters and return type differ somewhat for each type of rule. However, _all_ rule functions should adhere to two practices:

1. Provide a `**kwargs` parameter. Future versions of Lamarkdown may choose to provide additional information.
2. Provide a default value for all other parameters. Lamarkdown will omit a particular argument if the value is unavailable for any reason, and generally Lamarkdown doesn't guarantee that any particular information will be available.






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

A rule callback _must_ provide its own default value for each parameter, because the caller will omit a parameter when its value is not available. The callback should also define `**kwargs`, for forward compatibility.


---
title: Build Modules
nav_order: 50
has_children: true
---

# Build Modules

Build modules are high-level bundles of settings, with various built-in ones available via `lamarkdown.m.<modulename>()`; e.g.:

```python
import lamarkdown as la
la.m.plots() # Invoke the m.plots build module
```

Here are the standard build modules:

Build Module            | Description                                                                                                  
------------            | -----------
[`m.doc()`][]           | Styles output as a professional-looking document, and invokes various extensions. Acts as the set of defaults when no build files exist.
[`m.plots()`][]         | Adds support for several text-based graphics tools.
[`m.code()`][]          | Adds styling for syntax-highlighted code, as produced by [Pygments](https://pygments.org/).
[`m.page_numbers()`][]  | Adds pseudo-page numbers to the output document.
[`m.teaching()`][]      | Adds styling relevant to an educational environment, for tests or other assessments.


[`m.doc()`]: doc.md
[`m.plots()`]: plots.md
[`m.code()`]: code.md
[`m.page_numbers()`]: page_numbers.md
[`m.teaching()`]: teaching.md

You can create your own build module as a standard Python module. Within the module, place all Lamarkdown API calls inside a function, and invoke a function from your build file:

```python
# my_build_mod.py (custom build module)
from lamarkdown import la
def apply(): # Choose any function name you like
    la.css('p { background: black; color: white; }')
```
```python
# md_build.py (build file)
import my_build_mod
my_build_mod.apply() # Invoke your custom build module
```

{: .note}
> The function is required, because putting Lamarkdown API calls into the top-level scope of your custom build module won't work reliably, especially in [live update](live_updating.md) mode. Code in this scope only runs _once_, when the module is first loaded, whereas we want it to run whenever the document is recompiled.
>
> By contrast, build files (e.g., `md_build.py`) _do_ have code in their top-level scope, because they are loaded/re-loaded via a customised mechanism, not a standard `import` statement. 


<!--* `m.code()`: Adds CSS styling for syntax-highlighted code (as produced by [Pygments](https://pygments.org/), which is invoked through either the [`codehilite`](https://python-markdown.github.io/extensions/code_hilite/) or [`pymdownx.superfences`](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/) extensions).

    (This is essentially a single fixed syntax highlighting theme. You can use any other colour scheme via the `css()` or `css_files()` functions below, perhaps generated from the [`pygmentize` command](https://pygments.org/docs/cmdline/) with the `-S` switch.)

* `m.page_numbers(pageHeight = 1200)`: Adds pseudo-page numbers to the output document. This is essentially just a kind of ruler down the right-hand-side of the document, with "page numbers" marked at regular intervals (`pageHeight` pixels).

* `m.heading_numbers(from_level = 2, to_level = 6)`: Adds decimal numbering (through CSS styling) to a range of heading levels, by default 2--6. That is, <h2\> elements (or whichever level is given by `from_level`) will be numbered 1, 2, 3, etc., while <h3\> elements will be numbered 1.1, 1.2, etc.

* `m.teaching()`: Adds styles relevant to tests or other assessments, particularly for showing mark allocations via the `nmarks` attribute), and answers.-->

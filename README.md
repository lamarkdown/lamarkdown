# Lamarkdown

Command-line markdown document compiler based on Python-Markdown.

The intent is to provide a tool comparable to Latex, but with the Markdown and HTML formats in
place of Latex and PDF. Lamarkdown is _not_ a drop-in replacement for Latex, but it attempts to
address the same document-preparation use case. To this end, Lamarkdown:

* Is a locally-run, command-line tool.
* Builds a complete HTML document, where the author has complete control over the appearance
    (though making it easy to produce something that _looks_ more like a document than a webpage).
* Build an entirely _self-contained_ HTML document (except where you insert external references
    yourself), which can be stored and distributed as a standalone file.
    * (Also currently with the exception of fonts, which are, for now, declared as links to `fonts.googleapis.com`.)
* Allows embedding of Latex environments (or entire Latex documents), with the resulting output converted
    to SVG format and embedded within the HTML.

Further goals of the project (sometimes also associated with Latex document preparation) are to:

* Provide a live-updating feature to improve editing productivity. When enabled, the markdown file
    is automatically re-compiled, and the HTML document auto-reloaded, when changes are detected.
* Provide a scheme for compiling multiple variants of a single source document.


## Requirements

Lamarkdown depends on Python 3.7+, and the "markdown", "pymdown-extensions" and "watchdog" packages
(the latter needed for live-updating).

Additionally, to embed Latex code, you need an existing Latex distribution (e.g., Texlive). The
actual commands are configurable, but by default the Lamarkdown latex extension runs 'xelatex' and
'dvisvgm'.


## Basic Usage


To compile `mydoc.md` into `mydoc.html`, just run:

`lamd mydoc.md`

You can enable the live-update mode using `-l`/`--live`:

`lamd -l mydoc.md`

This will launch a local web-server and a web-browser, and will keep `mydoc.html` in sync with any
changes made to `mydoc.md`, until you press Ctrl+C. The browser will actually load a slightly
modified version of the HTML output (from `http://localhost:<port>`), containing JavaScript code
that reloads the page when necessary).


## Extensions and Build Modules


Lamarkdown inherits the extension mechanism of Python-Markdown, which permits modifications to the
markdown dialect itself.

Lamarkdown also has a broader system of "build modules" that setup the overall build process. Build
modules are able to:

* Define which Python-Markdown extensions are to be applied, and provide configuration options to
them.

* Define a set of _variants_ (multiple output documents) to be built from a single source .md file.

* Define CSS and Javascript code (and/or external .css/.js files) to be applied to the HTML.

* Add additional HTML elements before/after the output produced by Python-Markdown.

Lamarkdown will first try to load `md_build.py` in the same directory as the source .md file. It
will also try to load `\<name>.py`; i.e., a .py file with the same base name as the source .md
file. If both .py files exist, both will be loaded, `md_build.py` first. You can specify another
build file explicitly on the command-line with the `--build` option.

A minimal build file should typically include the following:

```{.python}
import lamarkdown as md
md.include('doc')
```

The `lamarkdown` package provides a simple API for setting build options. In this case,
"`md.include('doc')`" invokes the "`doc`" re-usable build module, which itself applies various
Python-Markdown extensions, and supplies CSS code to produce a document style.


## Built-In Extensions and Reusable Build Modules

It's recommended to be browse Python-Markdown's standard [extensions](https://python-markdown.github.io/extensions/), as well as the [PyMdown Extensions project](https://facelessuser.github.io/pymdown-extensions/).

Lamarkdown provides several extensions of its own:




## Build Modules API



A build module (being a Python script) will need to "`import lamarkdown`" (or "`from lamarkdown import *`", etc.) to access the small, simple API for setting build options. Specifically, it can call the following functions:

* `lamarkdown.include(include_name, ...)`

    Applies an additional build module (or modules). There are several "built-in", includable build modules:

    * "`doc`" -- adds several extensions and defines a range of CSS to help generate reasonably well-formatted documents. (If you _don't_ include this, you will almost certainly need some alternate CSS code.)

    * "`doc_toc`" -- adds the Python-Markdown "toc" (table of contents) extension, and define CSS to display this in a fixed panel to the side of the document itself.

    * "`code`" -- defines a CSS colour scheme for code highlighting (based on parsing done by the Pygments library, as used by Python-Markdown and Pymdown extensions).

    * "`cmd`" -- defines some simple CSS styles to render example command-lines within documents.

    * "`page_numbers`" -- adds a series of pseudo-page-numbers to the side of a document. These are placed in the margin, at 1200px intervals, to approximate the distance between page breaks were the document to be printed. (There is no explicit need for pagination in HTML documents, but some sort of numbering scheme may help the reader identify their progress.)

    * "`teaching`" -- adds some CSS styles to render educational material.

* `lamarkdown.get_build_dir()`

    Should it be necessary, this retrieves the "build directory", a temporary location that can be used to store temporary byproducts of the build process. (This is used, for instance, by the latex extension.)

* `get_env()`

    Should it be necessary, this retrieves the "build environment", a Python dict containing arbitrary variables and functions that will be made available during Markdown compilation. Currently, the only use of this is in conjunction with the `eval` extension, where Python expressions can be evaluated and their results inserted into the compiled document.

* `get_params()`

    Should it be necessary, this retrieves the complete `BuildParms` object, containing all options used in the build process.

* variant(name: str, classes: Union[str, list[str], None]):
    if classes is None:
        classes = []
    elif isinstance(classes, str):
        classes = [classes]
    else:
        classes = list(classes)
    _params().variants[name] = classes

def base_variant(classes: Union[str, list[str], None]):
    variant('', classes)

def variants(variant_dict = {}, **variant_kwargs):
    for name, classes in variant_dict.items():
        variant(name, classes)
    for name, classes in variant_kwargs.items():
        variant(name, classes)

def extensions(*extensions: list[Union[str,markdown.extensions.Extension]]):
    _params().extensions.extend(extensions)

def config(configs: dict[str,dict[str,Any]]):
    p = _params()
    exts = set(p.extensions)
    for key in configs.keys():
        if key not in exts:
            raise BuildParamsException(f'config(): "{key}" is not an applied markdown extension.')

    p.extension_configs.update(configs)

def css(css: str):
    _params().css += css + '\n'

def css_files(*css_files: list[str]):
    _params().css_files.extend(css_files)

def js(js: str):
    _params().js += js + '\n'

def js_files(*js_files: list[str]):
    _params().js_files.extend(js_files)

def wrap_content(start: str, end: str):
    p = _params()
    p.content_start = start + p.content_start
    p.content_end += end

def wrap_content_inner(start: str, end: str):
    p = _params()
    p.content_start += start
    p.content_end = end + p.content_end




A build file is a Python module that defines one or more of the following:

* `md_extensions` -- a `list` of Python Markdown extensions. These are passed directly to Python Markdown. See the [list of standard extensions](https://python-markdown.github.io/extensions/) and the [list of Pymdown extensions](https://facelessuser.github.io/pymdown-extensions/). You can also [create your own extensions](https://python-markdown.github.io/extensions/api/).

* `md_extension_configs` -- a `dict` containing [configuration options for Python Markdown extensions](https://python-markdown.github.io/reference/#extension_configs).

* `md_css` -- a string containing CSS code for displaying the output HTML file.

* `md_variants` -- a dictionary indicating how to compile multiple versions of the document. Specific parts of the document tree are retained in some variants, and removed in others.

    The dictionary keys are the unique 'names' of the variants, inserted into the target filename to produce multiple output files. One name is allowed to be the empty string '', which is loosely considered the 'default' variant. For each key, the corresponding value must be either None, a string, or an iterable of strings. These indicate which class(es) (in the HTML sense) are to be retained by this variant and discarded in the others.

    For example, say we have:

    ```
    md_variants = {
        '': 'class1',
        'vari1': ['class1', 'class2'],
        'vari2': None
    }
    ```

    If the target output name is `file.html`, then we will actually get three output documents: `file.html`, `filevari1.html` and `filevari2.html`. Only `filevari1.html` will retain the complete document. For `file.html`, all `class2` elements will be removed. And for `filevari2.html`, all `class1` and `class2` elements will be removed.

    Note: if there is no '' variant, then the specified target file won't be one of the actual output files.

* `md_init(build_params)` -- a function for performing more complex setting up, if needed.


Successive build files will simply add-on extra details to the `extensions` list, `extension_config` dict and `css` string. However, the `init()` function (if it exists) can arbitrarily examine and modify the `build_params`, which is an object containing the fields `extensions`, `extension_config`, `css`, which are the aggregated versions, built up from previous build files. It also contains various effectively-read-only details:

* `build_params.src_file` -- the name and path of the input .md file.
* `build_params.target_file` -- the name and path of the output .html file.
* `build_params.build_files` -- a list of all the build files currently being used.
* `build_params.build_dir` -- a path for storing intermediate files, if needed.


## Extra Markdown Extensions

### Tikz

You can embed Latex/Tikz code directly in an .md file.

It must start with either \begin{tikzpicture} or \usetikzlibrary. In the latter case, it must also _contain_ \begin{tikzpicture}, and you can also insert preamble declarations in between (such as \usepackage, \newcommand, etc.)

It must end with \end{tikzpicture}, except that it can also contain an attribute list (in the manner of the attr_list extension) in braces on the line after this.

The Latex/Tikz code will be compiled (using xelatex), the output converted to SVG (using pdf2svg), encoded in base 64, and embedded in the HTML as a \<img> element. Any attributes listed at the end will apply to the \<img> element. It is recommended to add `{alt="..."}` for accessibility reasons.

For instance:

```
\usetikzlibrary{positioning}
\usepackage{...}
\begin{tikzpicture}
...
\end{tikzpicture}
{alt="Important Tikz Diagram"}
```


### Eval

You can insert the result of a Python expression using `` $‌`...` ``. That is, surround the expression with backticks, and put a dollar-sign in front.

The expression will be evaluated in the (combined) scope of the build files, so to make use of library calls or custom functions, you can import/define those there.

For instance, if your build file contains "`from datetime import date`", then the expression `` $‌`date.today()` `` will cause the date of compilation to appear in the document at that point.

If there is an error in the expression, the error message will instead appear in the document, highlighted in red.

!!! warning

    This has security implications! This extension should not be enabled if there is any question about whether to trust the author of the markdown.

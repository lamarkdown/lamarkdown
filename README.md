# Python Markdown Compiler

Pymdc compiles .md (markdown) files to .html using the Python Markdown library.


## Requirements

* You will need to install the Python packages "Markdown" and "pymdown-extensions". 
* To use `--live`, you also need the Python "watchdog" package. 
* To use embedded `\begin{tikzpicture}...\end{tikzpicture}` code (TikZ/PGF/LaTeX), you need both "xelatex" and "pdf2svg".


## Build Files

Pymdc will load the following build files, in the following order, as part of the compilation process:

* {PYMDC-DIR}/default_md_build.py
* ./md_build.py
* ./{INPUT-FILE-WITHOUT-EXTENSION}.py

If one of these doesn't exist, it is skipped. In addition, you can specify a build file explicitly on the command-line with the `--build` option.

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

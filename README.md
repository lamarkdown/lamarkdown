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

* `extensions` -- a `list` of Python Markdown extensions. These are passed directly to Python Markdown. See the [list of standard extensions](https://python-markdown.github.io/extensions/) and the [list of Pymdown extensions](https://facelessuser.github.io/pymdown-extensions/). You can also [create your own extensions](https://python-markdown.github.io/extensions/api/).

* `extension_configs` -- a `dict` containing [configuration options for Python Markdown extensions](https://python-markdown.github.io/reference/#extension_configs).

* `css` -- a string containing CSS code for displaying the output HTML file.

* `init(build_params)` -- a function for performing more complex setting up, if needed.

Successive build files will simply add-on extra details to the `extensions` list, `extension_config` dict and `css` string. However, the `init()` function (if it exists) can arbitrarily examine and modify the `build_params`, which is an object containing the fields `extensions`, `extension_config`, `css`, which are the aggregated versions, built up from previous build files. It also contains various effectively-read-only details:

* `build_params.src_file` -- the name and path of the input .md file.
* `build_params.target_file` -- the name and path of the output .html file.
* `build_params.build_files` -- a list of all the build files currently being used.
* `build_params.build_dir` -- a path for storing intermediate files, if needed.


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
* Allows embedding of Latex environments (or entire Latex documents), with the resulting output converted
    to SVG format and embedded within the HTML.

Further goals of the project (sometimes also associated with Latex document preparation) are to:

* Provide a live-updating feature to improve editing productivity. When enabled, the markdown file
    is automatically re-compiled, and the HTML document auto-reloaded, when changes are detected.
* Provide a scheme for compiling multiple variants of a single source document.


## Requirements

Lamarkdown depends on Python 3.7+, and the "markdown", "lxml", "cssselect", "pymdown-extensions",
"watchdog" packages (the latter needed for live-updating).

Additionally, to embed Latex code, you need an existing Latex distribution (e.g., Texlive). The
actual commands are configurable, but by default the Lamarkdown latex extension runs 'xelatex' and
'dvisvgm'.


## Installation

First, download this repository. Then, if you have `pip`, you can use it to install lamarkdown as follows:

* In the terminal, navigate to the lamarkdown directory (containing `setup.cfg`).

* Run this command:

    `$ pip install .`

You should now be able to run `lamd`.

Alternately (on Linux/MacOS), you can place the contents of the repository wherever you like, and set your `PATH` environment variable to point to it, such that you can run `lamd.py`.

## Basic usage

To compile `mydocument.md` into `mydocument.html`, just run:

`$ lamd mydocument.md`

(Or `lamd.py` if appropriate.)

You can enable the live-update mode using `-l`/`--live`:

`$ lamd -l mydoc.md`

This will launch a local web-server and a web-browser, and will keep `mydoc.html` in sync with any
changes made to `mydoc.md`, until you press Ctrl+C in the terminal.

## Wiki

For detailed documentation, see [the wiki](https://bitbucket.org/cooperdja/lamarkdown/wiki/).

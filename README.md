# Lamarkdown

Command-line markdown document compiler based on Python-Markdown.

The intent is to provide a tool comparable to Latex, but with the Markdown and HTML formats in
place of Latex and PDF. Lamarkdown is _not_ a drop-in replacement for Latex, but it attempts to
address the same document-preparation use case. To this end, Lamarkdown:

* Is a locally-run, command-line tool.
* Builds a complete HTML document, where the author has complete control over the appearance
    (though making it easy to produce something that _looks_ more like a document than a webpage).
* Builds an entirely _self-contained_ HTML document (except where you insert external references
    yourself), which can be stored and distributed as a standalone file.
    * (Also currently with the exception of fonts, which are, for now, declared as links to `fonts.googleapis.com`.)
* Allows embedding of Latex environments (or entire Latex documents), with the resulting output converted
    to SVG format and embedded within the HTML.

Further goals of the project are to:

* Provide a live-updating feature to improve editing productivity. When enabled, the markdown file
    is automatically re-compiled, and the HTML document auto-reloaded, when changes are detected.
* Provide a scheme for compiling multiple variants of a single source document.


## Requirements and Installation

Lamarkdown depends on Python 3.7+. To install via pip:

`$ pip install lamarkdown`

However, to embed Latex code, you need a Latex distribution (e.g., [Texlive](https://tug.org/texlive/)), 
which must be installed separately. The actual commands are configurable. By default, Lamarkdown's 
Latex extension runs 'xelatex' and 'dvisvgm'.


## Basic Usage

To compile `mydocument.md` into `mydocument.html`, just run:

`$ lamd mydocument.md`

You can enable the live-update mode using `-l`/`--live`:

`$ lamd -l mydocument.md`

This will launch a local web-server and a web-browser, and will keep `mydocument.html` in sync with 
any changes made to `mydocument.md`, until you press Ctrl+C in the terminal.


## Full Documentation

See the full documentation at [lamarkdown.github.io](https://lamarkdown.github.io).

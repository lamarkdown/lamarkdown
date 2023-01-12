# Lamarkdown

Lamarkdown is a command-line markdown document compiler based on [Python-Markdown](https://python-markdown.github.io/).

The intent is to provide a tool comparable to Latex, but with the Markdown and HTML formats in
place of Latex and PDF. Lamarkdown is _not_ a drop-in replacement for Latex, but it attempts to
address the same document-preparation use case.

## Requirements and Installation

Lamarkdown depends on Python 3.7+. To install via pip:

`$ pip install lamarkdown`

To embed Latex code, you need a Latex distribution (e.g., [Texlive](https://tug.org/texlive/)), 
which must be installed separately. The actual commands are configurable. By default, Lamarkdown's 
Latex extension runs 'xelatex' and 'dvisvgm'.

## Basic usage

To compile `mydocument.md` into `mydocument.html`:

`$ lamd mydocument.md`

You can enable the live-update mode using `-l`/`--live`:

`$ lamd -l mydocument.md`

This will launch a local web-server and a web-browser, and will keep `mydocument.html` in sync with any
changes made to `mydocument.md`, until you press Ctrl+C in the terminal.


## Topics

For more advanced usage, see the following:

* [Build Files](build_files.md)
* [Extensions](extensions/index.md)
    * [Eval](extensions/eval.md)
    * [Heading Numbers](extensions/heading_numbers.md)
    * [Latex](extensions/latex.md)
    * [Markers](extensions/latex.md)
    * [Sections](extensions/sections.md)
* [Live Updating](live_updating.md)
* [Variants](variants.md)

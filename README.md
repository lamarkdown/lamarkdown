# Lamarkdown

Lamarkdown is a command-line document preparation system based on [Python-Markdown][]. It attempts to address similar use cases to LaTeX, but using the Markdown and HTML formats. It is _not_ directly intended to build static websites, though its extensions can be reused in [MkDocs][] (or in other applications based on Python-Markdown).

Take the [Lamarkdown tour][] to get a first impression.


## Requirements and Installation

Lamarkdown depends on Python 3.8+. To install via pip:

```console
$ pip install lamarkdown
```


## Basic Usage

To compile `mydocument.md` into `mydocument.html`, run:

```console
$ lamd mydocument.md
```

To enable the live-update mode, use `-l`/`--live`:

```console
$ lamd -l mydocument.md
```

This will launch a local web-server and a web-browser, and will keep `mydocument.html` in sync with any changes made to `mydocument.md`, until you press Ctrl+C in the terminal.


## Full Documentation

See the full documentation at [lamarkdown.github.io](https://lamarkdown.github.io).


[Lamarkdown tour]: https://lamarkdown.github.io/tour
[MkDocs]: https://www.mkdocs.org/
[Python-Markdown]: https://python-markdown.github.io

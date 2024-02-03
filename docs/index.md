<!--# Welcome to MkDocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.-->


# Introduction

Lamarkdown is a command-line markdown document compiler based on [Python-Markdown][].

The goal is to provide a tool comparable to LaTeX, but with the Markdown and HTML formats in
place of TeX and PDF. It is _not_ a goal to build static websites, though Lamarkdown's [extensions](extensions/index.md) can be reused in [MkDocs][] (or in other applications based on Python-Markdown).

Take the [Lamarkdown tour](tour.md) to get a first impression.

[Python-Markdown]: https://python-markdown.github.io
[MkDocs]: https://www.mkdocs.org/


## Requirements and Installation

Lamarkdown depends on Python 3.8+. To install via pip:

```console
$ pip install lamarkdown
```

There are optional dependencies that you'll need to install separately, to make use of certain Lamarkdown features.

* For embedding LaTeX diagramming code, you need a Latex distribution (e.g., [TeX Live][]), and a PDF-to-SVG conversion tool. (Lamarkdown can embed LaTeX mathematical expressions _without_ a LaTeX distribution, and does not require LaTeX for any part of its core operation.)

* Similarly, to embed the output of [Graphviz][], [Matplotlib][], [R (for plotting)][R], or [PlantUML][], you will also need to install these yourself.

[TeX Live]: https://tug.org/texlive/
[Graphviz]: https://graphviz.org/
[Matplotlib]: https://matplotlib.org/
[R]: https://www.r-project.org/
[PlantUML]: https://plantuml.com/


## Basic Usage

To compile `mydocument.md` into `mydocument.html`:

```console
$ lamd mydocument.md
```

You can enable the live-update mode using `-l`/`--live`:

```console
$ lamd -l mydocument.md
```

This will launch a local web-server and a web-browser, and will keep `mydocument.html` in sync with any changes made to `mydocument.md`, until you press Ctrl+C in the terminal.


## Concepts

To use Lamarkdown effectively, it's helpful to understand the following:

* [Extensions](extensions/index.md). These are plugins for the core Python-Markdown engine, and they can alter the Markdown language in arbitrary ways, generally by adding or modifying certain syntactical constructs. To create an extension, you must be familiar with the Python-Markdown API for doing so, but there are many pre-existing extensions available.

* [Build Files](build_files.md). These are `.py` scripts that configure options for an individual markdown document, or group of documents. These would generally be written by the author of the document(s), using the [Lamarkdown API](api_reference.md). A build file can cause certain extensions to be loaded (with certain options), specify CSS styles and JS scripts for the document generated, query or alter the output document structure, and define [Variants](variants.md). (Variants are multiple output documents produced from a single input `.md` file, using different build options.)

* [Build Modules](build_modules/index.md) -- reusable bundles of configuration, to be invoked by build files.

* [Output Directives](output_processing/index.md) -- temporary HTML attributes (not part of the actual HTML output) that specify certain output characteristics. They can be used to specify list labels, image scales, and media embedding, for instance. Directive names begin with "`:`", to distinguish them from real HTML attributes.


## Why Lamarkdown?

Lamarkdown addresses a need for creating accessible, portable (and optionally scriptable) documents, using a maximally-readable plain-text source format, and a programmable build process.

### Word Processors, LaTeX and PDFs

WYSIWYG word processors (Word, LibreOffice, Google Docs and others) are perhaps the most-used document-preparation systems. These are highly successful applications, but the endurance of LaTeX, despite its learning curve, demonstrates a long-standing demand for plain-text document creation as well.

LaTeX (and TeX in general) offers transparency. The PDF files it generates depend only on the text you explicitly write. There are no invisible elements or hidden dimensions to a LaTeX document; all factors affecting the output are plainly visible as text. You can edit a LaTeX document with any of hundreds of different editors, and have no concern that some hidden property might change beyond your control (leaving the document unpredictably reformatted or corrupted). LaTeX also encourages greater focus on pure content, while the compiler makes sensible stylistic decisions automatically. Both these things promote consistency and (subject to a learning curve) productivity.

TeX/LaTeX is extensible, but also has distinct weaknesses:

* It was designed to produce static, paginated, printable documents, whereas documents today are rarely printed. It was not designed to produce re-flowable documents that can be presented at different sizes, or documents accessible to vision-impared people. The Portable Document Format (PDF) struggles to address these issues itself, and is difficult to work with programmatically.

* LaTeX code is relatively verbose, which can limit its productivity benefits.

<!--* For developers seeking programmatic features---variables/functions (macros), conditionality, looping, etc.---the Tex/LaTeX implementation of these features seems esoteric compared with modern programming languages.-->


### Markdown and HTML

The Markdown format shares many of LaTeX's advantages, but was designed for purely electronic communication. It is conventionally compiled into HTML, a universally-supported, re-flowable format that retains structural semantics needed for screen readers. Markdown is one of a number of plain-text formats to do this, but is notable for its minimalistic syntax and widespread use. (HTML itself can be written manually, but being even more verbose than LaTeX, this is difficult to do productively.)

<!-- Insert some basic Markdown as an example? -->

Markdown is commonly used to build static websites. Various tools exist to convert a collection of `.md` (Markdown) files into a collection of `.html` files, to be uploaded to a webserver. For instance, _this site_ was generated from Markdown files using [MkDocs][], which uses the [Python-Markdown][] library.

<!-- Python-Markdown and other engines have extension mechanisms, through which additional capabilities have been added to the original language. -->

However, this is a different use case from the preparation of individual, standalone documents, as done through LaTeX.

<!--The latter requires webserver infrastructure, which is not feasible for every document an organisation or individual may wish to write.-->

Markdown, as a format, is an attractive choice for _both_ use cases, but standalone document preparation depends on various capabilities not necessarily present in static site generators:

* Citation and reference formatting;
* Automatic numbering of sections, figures, tables, etc., and cross-referencing using such numbers;
* Captioning of figures, tables, etc.;
* Formatting of mathematical equations;
* Creation of graphical content within the document;
* Creation of arbitrarily-complex tables;
* Creation of alternate document versions from the same source;
* Embedding of fonts, styles and images within the HTML files.

We expect individual document files to be storable and viewable from anywhere; they should not require webserver infrastructure.

<!-- Learnability, high-functioning defaults -->


<!--    (Any

    Directives are not really part of the markdown syntax itself; they are implicitly available through existing -->


<!--## Topics

For more advanced usage, see the following:

* [Live Updating](live_updating.md)
* [Build Files](index.md)
* [Variants](variants.md)
* [Build Modules](build_modules/index.md)
* [Extensions](extensions/index.md)
    * [Eval](extensions/eval.md)
    * [Heading Numbers](extensions/heading_numbers.md)
    * [Latex](extensions/latex.md)
    * [Markers](extensions/latex.md)
    * [Sections](extensions/sections.md)
* [API Reference](api_reference.md)-->
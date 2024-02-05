# `la.latex`

This extension lets you embed LaTeX code in Markdown documents. The intention is to support LaTeX-based diagrams, as well as LaTeX mathematical code, and there is a different syntactical approach for each.

<!-- It invokes external commands to compile LaTeX to PDF, and to convert the PDF to SVG. It then embeds the SVG into the output HTML. -->

<!--The extension (and hence the LaTeX syntax) is enabled in the following cases:

* By default if you have no build files;

* If any of your build files specify `m.doc()`:
    ```python
    import lamarkdown as la
    la.m.doc()
    ```

* If any of your build files specify this extension directly:
    ```python
    import lamarkdown as la
    la('la.latex')
    ```-->

<!--{: .note}
Some may argue that embedding LaTeX within markdown pollutes a simple and readable format with less-readable, esoteric symbols. Nonetheless, this approach does allow you to create diagrams, and other visual elements, all within a single file, without having to manage a collection of external resources.-->


## Diagrammatic (or Textual) LaTeX Code {#whole}

You can write either an entire LaTeX document, or a single LaTeX environment, directly within an `.md` file. This is intended for diagram-generating code, though you can in theory embed any arbitrary LaTeX output.

The extension will:

1. Pass the LaTeX code to an external LaTeX compiler, retrieving output in PDF form;
2. Pass the PDF file to another external command to convert it to SVG; and
3. Embed the SVG in the output HTML.

The LaTeX code must begin on a new line (though not necessarily a new paragraph).

Immediately underneath the LaTeX code, on a new line, you may write an [attribute list](https://python-markdown.github.io/extensions/attr_list/). This will attach HTML attributes to the resulting HTML output element, and may be important for accessibility (among other things). For instance, you could write `{ alt="A diagram showing ..." }` at the bottom.


!!! note "Design Notes"

    We choose to allow direct embedding of LaTeX code (for non-mathematical purposes), without any extra delimiter syntax. This results in some additional internal design complexity within Lamarkdown, considering it could have used [PyMdown's blocks mechanism](https://facelessuser.github.io/pymdown-extensions/extensions/blocks/), or its [superfences extension](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/).

    However, LaTeX effectively comes with its own delimiter syntax, and its direct inclusion seems unambiguous, given the requirements above. Thus, any extra syntax might feel like clutter to readers and authors.

    There is also a precedent, in a sense. Markdown already permits embedded HTML without any delimiters, because it too is unambiguous.


### Whole Document

If you embed an entire LaTeX document, it is expected to begin with `\documentclass` and end with `\end{document}`. For instance:

```markdown
# Embedding a Whole LaTeX Document

\documentclass{article}
\usepackage{ulem}
\begin{document}
    \emph{Compiled with LaTeX.}
\end{document}
{ alt="Textual explanation" }

Resuming the markdown syntax here.
```

### Single Environment

To embed just a single environment (with optional preamble), your LaTeX code must:

* Start with one of `\usepackage`, `\usetikzlibrary` or `\begin{`_name_`}` (where _name_ is any LaTeX environment);
* Contain `\begin{`_name_`}` (if it didn't start with it); and
* End with `\end{`_name_`}`.

For instance:

```markdown
# Embedding a LaTeX Environment

Important diagram:

\begin{tikzpicture}
    \path (0,0) node(a) {Start} -- (2,0) node(b) {End};
    \draw[->] (a) -- (b);
\end{tikzpicture}
{ alt="Textual explanation" }

Please contact us for details.
```

The extension fills in the remaining syntax (`\documentclass` and `\begin{document}...\end{document}`, as needed) to form a valid LaTeX document.




## Mathematics

You can also embed LaTeX mathematical code within `$...$` (for inline maths) or `$$...$$` (for block-form equations).

By default (or if `math="mathml"`), the extension uses [latex2mathml](https://github.com/roniemartinez/latex2mathml) to produce MathML code, which is included directly in the output document.

If `math="latex"`, then mathematical code will instead be compiled and converted using the same external commands as in [section ##](#whole), just in math mode.

Processing of math code can also be turned off with `math="ignore"` (either to restore the literal meaning of `$`, or to use an alternate math code processor like `pymdownx.arithmatex`).


## Options

Here's a full list of supported config options:

{-list-table}
* #
    - Option
    - Description

*   - `build_dir`
    - The location to write LaTeX's various temporary/intermediate files. By default, the extension uses Lamarkdown's own build directory (by default, `build/`).

*   - `cache`
    - A dictionary-like object for caching the output of the LaTeX compiler and PDF-to-SVG converter. Invoking these programs can take significant time, so they are only invoked when the contents of a given LaTeX section changes, _or_ when a file included by the LaTeX code changes.

        By default, the extension uses Lamarkdown's [build cache](../core.md#caching).

*   - `doc_class`
    - The `documentclass` to use when not explicitly given. By default, this is `standalone`.

*   - `doc_class_options`
    - Options to be passed to the `documentclass`, as a single string (comma-separated, as per LaTeX syntax). By default, this is empty.

*   - `embedding`
    - Either `data_uri` or `svg_element`. If `data_uri` is chosen, the output is embedded using an `<img>` element with a `data:` URI. Otherwise, it is included as an `<svg>` element.

        This is separate from Lamarkdown's core [resource embedding](../core.md#embedding) functionality; LaTeX output is _always_ embedded, but there is a choice of mechanism.

*   - `live_update_deps`
    - A set-like object into which the extension records the names of any files that the given TeX code depends on, such as images or other included TeX code (but not including the TeX installation itself). By default, if available, the extension will use Lamarkdown's "current" set of such dependencies.

        This has no effect on the output produced, but assists Lamarkdown in understanding when it should recompile the `.md` document.

*   - `math`
    - Specifies how to handle `$...$` and `$$...$$` sequences. The options are:

        * `mathml` (the default), where mathematical code is converted to MathML `<math>` elements, to be rendered by the browser;
        * `latex`, where mathematical code is compiled in essentially the same way as for `\begin{}...\end{}` blocks, but in LaTeX math mode; and
        * `ignore`, where mathematical code is left untouched by this extension, which may be needed if you're using another extension (like `pymdownx.arithmatex`) to handle it.

*   - `pdf_svg_converter`
    - The command to use to convert LaTeX PDF output to SVG form. This can be either `dvisvgm` (the default), or `pdf2svg`, or `inkscape`, _or_ a complete command that contains the special placeholders `in.pdf` and/or `out.svg`. These will be replaced with the appropriate temporary input/output files.

*   - `prepend`
    - Any common LaTeX code (by default, none) to be added to the front of each LaTeX snippet, immediately after `\documentclass{...}`. You can use this to add common packages, define `\newcommand`s, etc.

        ```python
        import lamarkdown as la
        la('la.latex',
            prepend = r'''
                \usepackage[default]{opensans}
                \newcommand{\mycmd}{xyz}
            '''
        )
        ```

*   - `progress`
    - An object accepting error, warning and progress messages. This should be an instance of `lamarkdown.lib.Progress`, and the extension will reuse Lamarkdown's "current" instance by default, if available.


*   - `strip_html_comments`
    - `True` (the default) to remove HTML-style comments `<!-- ... -->` from within LaTeX code, for consistency with the rest of the `.md` file. If `False`, such comments will be considered ordinary text and passed to the LaTeX compiler, for whatever it will make of them. The normal LaTeX `%` comments are available in either case.

*   - `tex`
    - The command to use to compile LaTeX code. This can be either `xelatex` (the default), or `pdflatex`, _or_ a complete command that contains the special placeholders `in.tex` and/or `out.pdf`. These will be replaced with the appropriate temporary input/output files.

*   - `timeout`
    - The amount of time to wait (in seconds) before the TeX command will be terminated, _after_ it stops outputting messages. This is 3 seconds by default.

*   - `verbose_errors`
    - If `True`, then everything the TeX command writes to standard output will be included in any error messages. If `False` (the default), the extension will try to detect the start of any actual error message, and only output that.


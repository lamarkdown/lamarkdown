# Latex (`lamarkdown.ext.latex`)

This extension allows markdown authors to embed Latex environments, and complete Latex documents. The Latex code is compiled (using an external command) to PDF, which is converted to SVG (scalable vector graphics) and embedded into the output HTML, using either an `<svg>` or `<img>` element.

The extension (and hence the Latex syntax) is enabled in the following cases:

* By default if you have no build files;

* If any of your build files specify `doc()`:
    ```python
    import lamarkdown as la
    la.doc()
    ```

* If any of your build files specify this extension directly:
    ```python
    import lamarkdown as la
    la.extension('lamarkdown.ext.latex')
    ```

(Some may argue that embedding Latex within markdown pollutes a simple and readable format with less-readable, esoteric symbols. Nonetheless, this approach does allow you to create diagrams, and other visual elements, all within a single file, without having to manage a collection of external resources.)


## Syntax

The standard Latex syntax is well beyond the scope of this documentation, but there are two approaches to embedding Latex code using Lamarkdown:

1. You can write a complete Latex document within your `.md` file. It must begin with `\documentclass{...}`, contain `\begin{document}` and end with `\end{document}`.

    ```markdown
    # My Document
   
    \documentclass{article}
    \usepackage{ulem}
    \begin{document}
        \emph{Compiled with Latex.}
    \end{document}
    { alt="Textual explanation" }

    Resuming the markdown syntax here.
    ```

2. You can write an abbreviated form. This must start with one of `\usepackage{...}`, `\usetikzlibrary{...}` or `\begin{...}`, contain `\begin{...}` (if it didn't start that way) and end with a corresponding `\end{...}`.

    In this abbreviated form, Lamarkdown will use `\documentclass{standalone}`, and insert `\begin{document}` and `\end{document}` if not already present. The `tikz` package will be included automatically.

    ```markdown
    # My Document
   
    Important diagram:

    \begin{tikzpicture}
        \path (0,0) node(a) {Start} -- (2,0) node(b) {End};
        \draw[->] (a) -- (b);
    \end{tikzpicture}
    { alt="Textual explanation" }

    Please contact us for details.
    ```
Both forms must begin on a new line (though not necessarily a new paragraph).

Both forms also accept an [attribute list](https://python-markdown.github.io/extensions/attr_list/), on a new line and enclosed in braces, _after_ the closing `\end{...}`. This will attach HTML attributes to the resulting HTML output element, and may be important for accessibility (among other things). For instance, if your Latex code represents a diagram, you could write `{ alt="My Diagram" }` at the bottom.

Here is a complete example `.md` file with embedded Latex:


## Processing and embedding

Lamarkdown invokes `xelatex` (by default), or `pdflatex`, or any other command of your choosing, to compile each separate Latex snippet:

```python
import lamarkdown as la
la.extension('lamarkdown.ext.latex', tex = 'pdflatex')
```
```python
import lamarkdown as la
la.extension('lamarkdown.ext.latex', tex = 'my-custom-tex in.tex out.pdf') 
# Note: 'in.tex' and 'out.pdf' are placeholders that will be automatically replaced with the actual file names.
```

Compiling Latex can add significantly to the total compilation time of the markdown document. Therefore, if [live updating](./LiveUpdating) is enabled, Lamarkdown caches the output of `xelatex`/`pdflatex`, and only reruns the command if/when there are changes to the Latex code (or various configuration options).

These commands produce PDF output, which cannot be directly embedded in HTML. Therefore, Lamarkdown converts it to scalable vector graphics (SVG) using `dvisvgm` (by default), `pdf2svg`, `inkscape` or (again) another command of your choosing.

```python
import lamarkdown as la
la.extension('lamarkdown.ext.latex', pdf_svg_converter = 'pdf2svg')
```
```python
import lamarkdown as la
la.extension('lamarkdown.ext.latex', pdf_svg_converter = 'my-custom-converter in.pdf out.svg')
# Note: 'in.pdf' and 'out.svg' are placeholders that will be automatically replaced with the actual file names.
```

Lamarkdown also supports two methods of inserting the SVG image into the output HTML:

1. It can insert an `<img>` tag, containing the SVG as a base64 `data:` URI.

    ```python
    import lamarkdown as la
    la.extension('lamarkdown.ext.latex', embedding = 'data_uri') # The default
    ```

2. It can contain an `<svg>` element (and its child elements). 

    ```python
    import lamarkdown as la
    la.extension('lamarkdown.ext.latex', embedding = 'svg_element')
    ```

There may not be much to distinguish these two approaches from a practical point of view.

## Configuration option reference

Here's a full list of supported config options:

* `build_dir`: the location to write Latex's various temporary/intermediate files. By default, Lamarkdown creates a directory called `build` for this purpose.

* `tex`: either `xelatex` (the default), or `pdflatex`, or a complete command containing `in.tex` and/or `out.pdf` (which will be replaced with the appropriate temporary input/output files).

* `pdf_svg_converter`: either `dvisvgm` (the default), or `pdf2svg`, or `inkscape`, or a complete command containing `in.pdf` and/or `out.svg` (which will be replaced with the appropriate temporary input/output files).

* `embedding`: either `data_uri` (to use an `<img>` element with a `data:` URI), or `svg_element`.

* `prepend`: any common Latex code (by default, none) to be added to the front of each Latex snippet, immediately after `\documentclass{...}`. You can use this to add common packages (e.g., `\usepackage[default]{opensans}`), define `\newcommand`s, etc.

    ```python
    import lamarkdown as la
    la.extension('lamarkdown.ext.latex', 
        prepend = r'''
            \usepackage[default]{opensans}
            \newcommand{\mycmd}{xyz}
        '''
    )
    ```

* `doc_class`: the `documentclass` to use when not explicitly given. By default, this is `standalone`.

* `doc_class_options`: options to be passed to the `documentclass`, as a single string (comma-separated, as per Latex syntax). By default, this is empty.

* `strip_html_comments`: `True` (the default) to remove HTML-style comments `<!-- ... -->` from within Latex code, for consistency with the rest of the `.md` file. If `False`, such comments will be considered ordinary text and passed to the Latex compiler, for whatever it will make of them. The normal Latex `%` comments are available in either case.

For example (in your [build file](./BuildFiles)):
```python
import lamarkdown as la
la.extension('lamarkdown.ext.latex',
    tex = 'pdflatex',
    pdf_svg_converter = 'inkscape',
    embedding = 'svg_element',
    prepend = r'\usepackage[default]{opensans}'
)
```

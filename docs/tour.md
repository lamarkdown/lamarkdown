# Lamarkdown Tour

Many Lamarkdown features are available out-of-the-box, without any configuration. You need only write the actual `.md` file, and compile it. However, by providing a [build file](process.md#build_files), even a blank one, these defaults are put aside, and you can more precisely specify the settings you want.

The following examples include a minimal build file (consisting of Python code), to provide context for each feature, even though many features are still available by default if no build file exists.

You may like to read about [conventional Markdown syntax](https://www.markdownguide.org/basic-syntax/), if you're not already familiar with it.


## Using (Non-Lamarkdown) Extensions {#extensions}

Lamarkdown uses the [Python-Markdown](https://python-markdown.github.io/) engine, so it supports existing Python-Markdown [extensions](https://python-markdown.github.io/extensions/), including the [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/).

Here's a couple of examples:

/// markdown-demo

    # md_build.py
    import lamarkdown as la
    la('tables')
    la.css('td { border: 1px solid blue; }')
    ---
    ## Standard [tables][] extension

    Column A  | Column B
    --------- | --------
    Red       | Green
    Blue      | Yellow

    [tables]: https://python-markdown.github.io/extensions/tables/
///

/// markdown-demo

    # md_build.py
    import lamarkdown as la
    la('pymdownx.critic', mode = 'view')
    ---
    ## PyMdown [critic][] extension

    Some text {~~to which~>with~~} insertions and
    deletions{-- can be made--}.

    [critic]: https://facelessuser.github.io/pymdown-extensions/extensions/critic/
///


## Citations and Reference Lists

The [la.cite][cite] extension formats in-text citations and builds a reference list. You provide a BibTeX-formatted file containing reference information, and insert citations of the form `[@refkey]`, or `[@abc, @xyz, p. 5]`, for instance.

(This citation format was inspired by [Pandoc's citation syntax](https://pandoc.org/MANUAL.html#citation-syntax). The extension uses the [Pybtex!](https://pybtex.org/) library to read `.bib` files and construct a bibliography.)


/// markdown-demo
    extra_files:
        - ['references.bib', 'Reference database', 'bibtex']

    import lamarkdown as la
    la('la.cite', file = 'references.bib')
    ---
    # references.bib
    @article{refA,
        author = "An Author",
        title = "A Title",
        journal = "The Journal",
        year = "1990"
    }
    ---
    ## Referencing Example
    Here's a citation [@refA, p. 10].

    ### References
    ///References Go Here///

    (Note: this is unstyled.)
///


## Numbering and Cross-Referencing

The [la.labels][labels] extension can assign automatic numbers to headings, list items, figures and tables. Use the `-label="..."` directive to specify what to number and how.

If you link to another part of the same document using an ID (e.g., `#myid`), the link text may contain `##`, which will be replaced with the label for the linked part of the document (stripped of any fixed prefix/suffix characters).

/// markdown-demo

    import lamarkdown as la
    la('attr_list', 'la.labels')
    ---
    ## Section  {-label="1. ,X.1. "}

    References to subsections [##](#secX) and [##](#secY).

    ### Subsection  {#secX}

    See [Appx-##](#appx) for details.

    ### Subsection  {#secY}

    ## Section

    ## Appendix  { #appx -label="A. " }

    ## Appendix
///

For lists, the [la.attr_prefix][attr_prefix] extension provides a way to attach `-label`{.nobreak} to the list:
/// markdown-demo

    import lamarkdown as la
    la('la.attr_prefix', 'la.labels')
    ---

    A list:

    {-label="(a) ,[i] "}
    1. List item
    2. List item
        1. Sublist item
            {#itemX}
        2. Sublist item

    Reference to [item ##](#itemX).
///


## Embedding LaTeX

The [la.latex][latex] extension lets you write LaTeX code in your Markdown document, and have the results embedded in the HTML output. This supports mathematical equations, as well as LaTeX-based diagramming code (e.g., using [PGF/TikZ](https://tikz.dev/)).

First, you can embed LaTeX mathematical code by enclosing it inside `$...$` (for inline maths) or `$$...$$` (for block-style maths):

/// markdown-demo

    import lamarkdown as la
    la('la.latex')
    ---

    The quadratic formula is:
    $$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

    where $x$ is a root of a quadratic equation,
    and $a$, $b$ and $c$ are coefficients.
///

Second, you can write a LaTeX environment (or an entire LaTeX document) directly inside the Markdown file, where it will be compiled with "pdflatex" (or equivalent), assuming you have it installed:

/// markdown-demo

    import lamarkdown as la
    la('la.latex', pdf_svg_converter = 'pdf2svg')
    ---

    ## LaTeX diagram

    \begin{tikzpicture}[nodes={draw,circle},
                        font=\LARGE\bfseries]
        \node at(0,  0) [red]            (A) {A};
        \node at(3,  0) [blue]           (B) {B};
        \node at(1.5,2) [green!50!black] (C) {C};
        \draw (A) -- (B) -- (C) -- (A);
    \end{tikzpicture}
    { alt="Three circles, A, B and C, with connecting lines." }

    This is a diagram drawn in LaTeX, using PGF/TikZ,
    and embedded in the document as an SVG image.
///


## Captions

The [la.captions][captions] extension lets you specify captions for any block element, which will then be wrapped in an HTML `<figure>` element, if appropriate.

Simply write the caption in a paragraph (or blockquote containing several paragraphs) _above_ the element-to-be-captioned, and attach the `-caption` directive.

/// markdown-demo

    import lamarkdown as la
    la('la.captions', 'tables')
    la.css('td { border: 1px solid blue; }'
           'table > caption { font-style: italic; }')
    ---

    An enigmatic taxonomy of colours.
    {-caption}

    Column A  | Column B
    --------- | --------
    Red       | Green
    Blue      | Yellow
///

In combination with [la.labels][labels], you can number your figures and tables:

/// markdown-demo

    import lamarkdown as la
    la('la.captions')
    la('la.latex', pdf_svg_converter = 'pdf2svg')
    la('la.labels', labels = {'figure': '"Figure" 1. '})
    la.css('figure { background: #ffe0c0; '
           '         padding: 0.5em; }'
           'figcaption { margin-bottom: 0.5em; }'
           'figcaption .la-label { font-weight: bold; }')
    ---

    Some text beforehand.

    A schematic representation of alphabetic distance.
    {-caption}

    \begin{tikzpicture}[nodes={draw,circle},
                        font=\LARGE\bfseries]
        \draw[thick] (0,0) node[left] {A} -> +(5,0) node[right] {B};
    \end{tikzpicture}

    Some text afterwards.
///


## Other Diagramming/Plotting Approaches

Lamarkdown is pre-configured to invoke various other external plotting libraries/tools when requested. (To accomplish this, it uses the PyMdown ["superfences"](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/) extension.)

Each of these libraries/tools must be installed separately.

/// markdown-demo

    import lamarkdown as la
    la.m.plots()
    ---
    ## Graphviz diagram

    ```graphviz-neato
    digraph mygraph {
        A -> B -> C -> D;
        B -> D;
    }
    ```
///

/// markdown-demo

    import lamarkdown as la
    la.m.plots()
    la.allow_exec = True
    ---
    ## Matplotlib

    ```matplotlib
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    fig.set_size_inches(4, 2.5)

    ax.bar(['No', 'Yes'],
           [40, 60],
           color=['tab:red', 'tab:blue'])

    ax.set_ylabel('Percentage')
    ax.set_title('Agreement')
    ```
///

/// markdown-demo

    import lamarkdown as la
    la.m.plots()
    la.allow_exec = True
    ---
    ## R plotting

    ```r-plot
    dev.new(width = 5, height = 2.5)
    par(mar = c(2, 4, 2, 0))
    barplot(
        c(No = 40, Yes = 60),
        ylab = 'Percentage',
        main = 'Agreement',
        col = c('brown2', 'deepskyblue3')
    )
    ```
///

/// markdown-demo

    import lamarkdown as la
    la.m.plots()
    ---
    ## PlantUML

    ```plantuml
    @startuml
    left to right direction
    class Contact {
        name: String
    }
    class Address {}
    Contact o-- "0..*" Address
    @enduml
    ```
///


## List Tables

There are limitations to the simple tables you can create with the [standard "tables" extension](https://python-markdown.github.io/extensions/tables/) (as shown in [section ##](#extensions)). These do not permit arbitrary content in each table cell.

For greater flexibility, the [la.list_tables][list_tables] extension lets you write out the contents of a table as a series of nested lists (inspired by reStructuredText).

/// markdown-demo

    import lamarkdown as la
    la('la.list_tables')
    la.css('td, th { border: 1px solid blue; }')
    ---

    {-list-table}
    * #
        - Heading A
            - Subheading AA
            - Subheading AB
        - Heading B
    *   - Block quote:

            > Something someone famous once said.

        - Actual list:

            * Item 1
            * Item 2

        - Code:

            ```
            print("Hello world")
            ```
///


## Variants

Lamarkdown can generate multiple output HTML files from a single Markdown input file, each with arbitrarily-different configuration options.

In the build file, simply define a function representing each _variant_, make the appropriate API calls in each such function, and pass the functions to [`la.variants()`][variants_call].

To support a common use case, Lamarkdown also provides a [`prune()`][prune] API function, which deletes any parts of the output document matching a given CSS-style selector. If this is done in only one variant, you can keep private notes in your Markdown file, and produce separate HTML files with and without them.

/// markdown-demo

    import lamarkdown as la

    def private():
        la.css('.priv { background: #ff8080 }')

    def public():
        la.prune('.priv')

    la.variants(private, public)
    la('attr_list')

    ---

    ## For _private_{.priv} discussion

    Here's some public information...

    But my readers don't need to know _this_...
    {.priv}
///





[attr_prefix]:      extensions/attr_prefix.md
[captions]:         extensions/captions.md
[cite]:             extensions/cite.md
[eval]:             extensions/eval.md
[labels]:           extentions/labels.md
[latex]:            extentions/latex.md
[list_tables]:      extentions/list_tables.md
[markdown_demo]:    extentions/markdown_demo.md
[sections]:         extentions/sections.md

[lamarkdown_call]:  api.md#lamarkdown_call
[basename]:         api.md#basename
[prune]:            api.md#prune
[variants_call]:    api.md#variants

[m.doc]:            modules/doc.md
[m.plots]:          modules/plots.md

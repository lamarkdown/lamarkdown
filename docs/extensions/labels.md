# `la.labels`

This extension assigns counter-based (or fixed) labels to headings, lists, figures and tables, and lets you use those labels in links to labelled elements.

You can specify where and how labels should appear by:

1. Adding the `-label=...` directive to headings, lists, figures and tables; or
2. Specifying the [`labels` configuration option](#labels-opt).

In both cases, you provide a _label template_.

!!! note

    Remember that, while the following examples all use the `-label` directive, you can just as easily write templates using the `labels` configuration option. In the latter case, you may not need to modify the `.md` file at all in order to produce the labelling systems you want.

## Label Templates {#templates}


A label template has several parts.

### Counter Types

A counter type is a system for counting integers. Given `-label="1"`, the `1` is a counter type representing base-10 Arabic numerals. You can also provide `A` or `a` for upper/lower-case alphabetic numbering, `I` or `i` for upper/lower-case Roman numerals, or one of various longer-form names corresponding to CSS counter styles (e.g., `simp-chinese-informal`, `lower-greek`, `lower-hexadecimal`, etc.).

/// markdown-demo
    show_build_file: False
    output_height: 12em

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('.la-label { color: red; }'
            'li::before { color: blue; }'
            'li > p { display: inline; }')
    ---
    ## Heading {-label="i "}
    ## Heading

    {-label="simp-chinese-formal "}
    1. List item
    2. List item
///

!!! note "Design Notes"

    The available counter types are essentially the same as the values supported by the [`list-style-type` CSS property](https://developer.mozilla.org/en-US/docs/Web/CSS/list-style-type), _except for_:

    * Bullet-points like `disc`, `circle`, `square`, `disclosure-open` and `disclosure-closed` (which would simply duplicate literal Unicode characters);
    * Global CSS values like `inherit`, `initial`, etc.;
    * The value `none`;
    * Custom counter styles.

    The use of CSS belies some internal complexity. _Lists_ are numbered by generating CSS code that itself produces the labels (because this seems the conventional approach to HTML/CSS lists). However, headings (and figures and tables) are labelled _at compile time_, the labels becoming part of the HTML document content.

    This is partly because the `toc` extension will read heading text (at compile time, of course), and reproduce it inside the table-of-contents, and we'd ideally like the table-of-contents to contain the same heading labels that the headings themselves do.

    To support compile-time labelling, `la.labels` must implement much of the same counter logic as browsers do to support [CSS's `@counter-style` construct](https://developer.mozilla.org/en-US/docs/Web/CSS/@counter-style).

    A future version of Lamarkdown may:

    * Provide a configuration option to determine which implementation approach to use for which type of element; and/or
    * Provide a way to define custom counter types, similar to `@counter-style`.


### Literals

Literal strings can appear as the prefix and suffix of a label. In `-label="(1) "`, the `(` is a prefix, and `) ` is a suffix. Literals may contain any number of characters, including zero: e.g.:

/// markdown-demo
    show_build_file: False

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('li { display: table; }'
            'li::before { color: blue; display: table-cell; padding-right: 0.5em}'
            'li > p { display: inline; }')
    ---
    {-label="@@@ A @@@"}
    1. List item
    2. List item
    3. List item
///

Literals can consist of:

* Spaces and all printable symbols _other than_ ASCII digits, letters, quotation marks, `,`, `-` and `*`.

* `-`, when not between alphanumeric characters (where it is considered part of a counter type).

* `*`, when not the final character following `,` (where it has a special meaning, [explained below](#inner)).

* Characters within an additional pair of quotation marks. There will already be a pair of quotation marks around the entire template (whether `-label='...'` or `label="..."`), so the _inner_ quotation marks must be different. For instance:

    /// markdown-demo
        show_build_file: False
        output_height: 16em

        import lamarkdown as la
        la('la.labels', 'la.attr_prefix', 'tables')
        la.css('table { margin: 1em }'
            'td, th { border: 1px solid blue }'
            'li { display: table; }'
            'li::before { color: blue; display: table-cell; padding-right: 0.5em}'
            'li > p { display: inline; }')
        ---

        {-label="'Table' 1."}
        Column A | Column B
        -------- | --------
        One      | Two
        Three    | Four

        Column C | Column D
        -------- | --------
        Five     | Six
        Seven    | Eight
    ///

* Quotation marks, when doubled-up within other quotation marks; e.g., `-label="''''1''''"` produces a base-10 arabic number inside a _single_ set of quotation marks: `'1'`, `'2'`, etc.

    Note: the attribute syntax (the general form `attr="value"`) has its own separate way of escaping characters with `\`, but this is invisible to the template syntax, so cannot be used to designate literal characters.

A label _may_ consist of just a literal string, with no counter type, which can be useful in unordered lists:

/// markdown-demo
    show_build_file: False

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix', 'tables')
    la.css('li { display: table; }'
            'li::before { color: blue; display: table-cell; padding-right: 0.5em}')
    ---

    {-label="$$ "}
    * List item
    * List item
    * List item
///



### Hierarchical Labels {#parents}

A _parent indicator_ (if present) is used to make hierarchical labels. It acts as a placeholder for a higher-level label, which then forms part of the lower-level label, preceeding the lower-level counter. (The higher-level label's own prefix and suffix are removed.)

A template with a parent indicator has a form similar to `-label="(L.1) "`, where `L` is the parent indicator, and `.` is a separator literal (which can be any valid literal). `L` specifically refers to the label of the next higher _list_, if one exists.

For instance:

/// markdown-demo
    show_build_file: False

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('li::before { color: blue; }'
            'li > p { display: inline; }')
    ---
    {-label="L.1. "}
    1. Item
    2. Item

        {-label="[L.A] "}
        1. Item
        2. Item

            {-label="_L_i_ "}
            1. Item
            2. Item

        3. Item

    3. Item
///

In the first label template above, the `L.` part will be ignored, because there is no higher list level.

Similarly, the parent indicator `H` refers to the label of the next higher _heading_ (if one exists):

/// markdown-demo
    show_build_file: False
    output_height: 25em

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('.la-label { color: red; }')
    ---
    {-label="H.1. "}
    ## Heading
    ## Heading

    {-label="[H.A] "}
    ### Heading
    ### Heading

    {-label="_H_i_ "}
    #### Heading
    #### Heading

    ### Heading

    ## Heading
///

Meanwhile, `X` refers to the next label label of _any_ kind. For example, here are some `<h3>` headings, within an `<ol>` list, underneath another `<h2>` heading, where the labels are arranged hierarchically:

/// markdown-demo
    show_build_file: False
    output_height: 18em

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('.la-label { color: red; }'
            'li { display: table; }'
            'li::before { display: table-cell; color: blue; padding-right: 0.5em }')
    ---
    {-label="1. "}
    ## Heading
    ## Heading

    {-label="[X.A] "}
    1. List item
    2. List item

        {-label="_X_i_ "}
        ### Heading
        ### Heading
///



### Inner Templates {#inner}

An inner template is the part of a template after the first (non-quoted) `,`. A full label template consists of a `,`-separated sequence of components (each of which is as described above), optionally ending in `,*`.

Inner label templates help make label specification neater. They apply to nested elements of the same type. For instance, `-label="1. ,(a) ,(i) "` assigns labels `1. `, `2. `, etc. to the current level, `(a) `, `(b) ` to singly-nested elements, and `(i) `, `(ii) ` to doubly-nested elements (all of the same type).

/// markdown-demo
    show_build_file: False

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('li { display: table; }'
            'li::before { display: table-cell; color: blue; padding-right: 0.5em }')
    ---
    {-label="1. ,(a), (i) "}
    1. List item
        1. List item
            1. List item
            2. List item
        2. List item
    2. List item
///

When `,*` occurs after the final template component, it applies that template to _all_ more-deeply nested elements indefinitely (until otherwise overridden).

Together with parent indicators, this lets you produce a typical multilevel decimal numbering system with little overhead:

/// markdown-demo
    show_build_file: False
    output_height: 20em

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('.la-label { color: red; }')
    ---
    {-label="H.1. ,*"}
    ## Heading
    ### Heading
    #### Heading
    #### Heading
    ### Heading
    ## Heading
///


## Cross References

Once elements are labelled, you can create links to them (or parts of them) that include those labels in the link text. Specifically, you must:

* Assign an ID to the target of a link, e.g., by writing `{#myid}` before or after it. The ID _does not_ need to be on precisely the element that actually has the label; it may also be on any element inside it.
* Create a link to that ID, where the link text contains `##`.

For instance:

/// markdown-demo
    show_build_file: False
    output_height: 16em

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('.la-label { color: red; }'
            'li::before { color: blue; }'
            'li > p { display: inline; }')
    ---
    Some references to headings [##](#secX) and
    [##](#secY), and to [list item ##](#itemU) and
    [list item ##](#itemV).

    {-label="1. "}
    ## Heading {#secX}
    ## Heading {#secY}

    {-label="(a) "}
    1. List item
        {#itemU}
    2. List item
        {#itemV}
///

You can be more specific about what _kind_ of label you want to refer to, by appending a [parent indicator](#parents) to the `##`; e.g., `##H` or `##L`. You can also have multiple such placeholders for a single link.

/// markdown-demo
    show_build_file: False
    output_height: 16em

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('.la-label { color: red; }'
            'li::before { color: blue; }'
            'li > p { display: inline; }')
    ---
    A reference to [list item ##L in section ##H](#item).

    {-label="1. "}
    ## Heading
    ## Heading

    {-label="(a) "}
    1. List item
    2. List item
        {#item}
///


!!! note "Design Notes"

    The use of `##` has the advantage that:

    * It is concise, without being too likely to require routine escaping (as a single `#` may);
    * It appears to reflect a number;
    * It also seems visually-related to the element IDs syntax (`#myid`), while not being exactly the same; and
    * Since it only applies inside link text, it does not conflict with heading syntax.

    One might compare the approach to LaTeX, which uses `\label` and `\ref`:

    ```latex
    A reference to Section \ref{xyz}.

    \section{First}
    ...

    \section{Second}
    \label{xyz}
    ...
    ```

    Markdown and HTML have element IDs in place of `\label`. They do not have an exact equivalent of `\ref` (which just grabs a label). But rather than trying to recreate `\ref` exactly, we accept the preeminence of hyperlinks in Markdown and HTML, and work within them.

    One theoretical weakness of the `la.labels` approach is that you cannot make a label reference _outside_ of a hyperlink. There seems little practical drawback to this, though.

    `la.labels` does not replace or directly alter the Markdown link-parsing logic, but rather looks for the text inside `<a>` (anchor) elements once they've already been parsed.


## Suppressing Labels: `-no-label`

The `-no-label` directive will suppress a label in places where one would otherwise occur. The counter will be paused, and carry on at the next applicable element.

/// markdown-demo
    show_build_file: False
    output_height: 20em

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('.la-label { color: red; }'
            'li::before { color: blue; }'
            'li > p { display: inline; }')
    ---
    ## Heading {-label="(i) "}
    ## Heading {-no-label}
    ## Heading

    {-label="(i) "}
    1. List item
    2. List item
        {-no-label}
    3. List item
///


## Changing Labels

The label format may be changed part-way through a sequence of elements, simply by assigning a new `-label` template to one of the elements. For instance:

/// markdown-demo
    show_build_file: False
    output_height: 20em

    import lamarkdown as la
    la('la.labels', 'la.attr_prefix')
    la.css('.la-label { color: red; }'
            'li::before { color: blue; }'
            'li > p { display: inline; }')
    ---
    ## Heading {-label="(i) "}
    ## Heading
    ## Heading {-label="[A] "}
    ## Heading

    {-label="(i) "}
    1. List item
    2. List item
    3. List item
        {-label="[A] "}
    4. List item
///



<!--## Template syntax

Label templates can create complex labelling schemes, with minimal specification. The syntax is
defined as follows:

template := template_part ( ',' template_part )* [ ',' '*' ]
template_part := literal* [ [ ('X' | 'L' | 'H' [level] ) literal+ ] format_spec literal* ]

format_spec := any alphanumeric sequence (including '-', but not at the start or end position)

level := an integer from 1 to 6, inclusive
literal := ( unquoted_literal | quoted_literal )*
unquoted_literal := any single character _other than_ ',', quotation marks, alphanumeric
    characters, or '-' if surrounded by alphanumeric characters
quoted_literal := any sequence of characters surrounded by double or single quotes, and possibly
    including doubled-up quotes to represent literal quotation marks.

Thus, a template consists of one or more comma-separated parts, optionally ending in a '*'. The
first (mandatory) part applies directly to the current list or list element. Subsequent parts apply
to successive levels of child lists, _of the same fundamental type_ (nested lists for lists, and
sub-headings for headings). If present, the '*' causes the final template to apply indefinitely to
any more deeply-nested lists/headings. (If '*' is omitted, then any lists nested more deeply are
outside the scope of this template list.)

The `format_spec` refers to the core numbering system for a given list or list element. It can be:

* `1`, for arabic numerals;
* `a`/`A`, for lower/uppercase English alphabetic numbering;
* `i`/`I`, for lower/uppercase Roman numerals; or
* one of various terms accepted by the list-style-type CSS property; e.g., `lower-greek`,
    `armenian`, etc.

(This extension seeks to support _most_ numbering schemes available in CSS.)

For <ul> elements, there's generally no numbering system required, and `format_spec` can be
omitted, so that the entire template consists just of a literal `prefix`.

(This extension _does not_ directly support the CSS terms 'disc', 'circle', 'square', as these can
be directly represented with literal characters; e.g., '•', '◦', '▪'.)

If `X`, `L` or `H` is given, it refers to the label of the nearest _numbered_ ancestor element.
Specifically, `X` means _any_ such element (though, again, only those with numbering systems, so
generally not <ul> elements), `L` means a list element (almost certainly <ol>), `H` means any
heading element, and `H1`-`H6` mean the corresponding heading level. If such an ancestor element
exists, its core label (minus any prefix/suffix literals) will be inserted prior to the element's
own number, along with an delimiting literal.

If X, L or H is given, but no such element exists, then no ancestor label will be inserted, _and_
the delimiting literal will be omitted too.

Examples:

* -label="(X.1),*"
* -label="1.,(a),(i)"
-->



## Options

The [`labels`](#labels-opt) option is the one key option for influencing document-wide labelling conventions. The remainder of the options below concern the technical implementation details.


{-list-table}
* #
    - Option
    - Description

*   - `css_fn`
    - A function taking a single string parameter, which the extension will call to deliver CSS code, under the assumption that it will be applied to the output document. The extension needs this capability in order to implement CSS-based labels, particularly for ordered/unordered lists.

        By default, and if it's available, this will be [`lamarkdown.css()`][css].

        If `css_fn` is `None`, or if it's left unspecified and `lamarkdown.css()` is _not_ available (because the extension is being run externally), then CSS-based labels will be disabled. In this case, the extension will fall back to hard-coding list labels in the HTML document. This may be visually indistinguishable, though not necessarily semantically equivalent.

*   - `css_rendering`
    - A set containing element types that will receive CSS-based label rendering, if it's available, rather than hard-coded labels. It's not currently recommended to change this, because the underlying implementation only currently supports CSS-based rendering for list labels.

*   - `directives`
    - An object for retrieving directives from HTML tree elements. This should be an instance of `lamarkdown.lib.directives.Directives`, and the extension will reuse Lamarkdown's "current" instance by default, if available.

*   - `label_processors`
    - A list of `LabelProcessor` objects responsible for orchestrating the labelling of different kinds of HTML elements. It's not currently recommended to change this.

*   - `labels`
        {#labels-opt}

    - A dictionary specifying label templates to use in the absence of `-label` directives.

        The dictionary keys are `h` (for headings), "`h`_n_" (for level-_n_ headings specifically), `ol` (for ordered lists), `ul` (for unordered lists), `figure` and `table`.

        The dictionary values are [label templates](#templates). Just as for the `-label` directive, these templates can also include [parent indicators](#parents) and [inner templates](#inner). For instance, you can arrange for a multilevel heading labels, beginning at level-2 headings, with `labels = {'h2': 'H.1. ,*'}`.

        By default, `labels` is `{}`.

*   - `progress`
    - An object accepting error, warning and progress messages. This should be an instance of `lamarkdown.lib.Progress`, and the extension will reuse Lamarkdown's "current" instance by default, if available.


    -

[css]: ../api.md#css

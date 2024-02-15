# `la.list_tables`

This extension ([inspired by reStructuredText](https://pandemic-overview.readthedocs.io/en/latest/myGuides/reStructuredText-Tables-Examples.html#list-table)) provides an alternative to the `tables` extension, and other 3rd-party extensions.

A "list table" comprises a list of lists in Markdown, which are transformed into a proper table in the HTML output. The mechanism permits the creation of arbitrarily complex tables.

Here's a simple example:

/// markdown-demo

    import lamarkdown as la
    la('la.list_tables', 'pymdownx.superfences')
    la.css('table { border-collapse: collapse; width: 100%; }'
           'td    { border: 1px solid blue; padding: 0.5em}')
    ---

    {-list-table}
    *   - # Col Heading A
        - # Col Heading B
        - # Col Heading C
    *   - A paragraph.

            Another paragraph.

        -   * List item A
            * List item B

        - Some important code:

            ```
            print("Hi!")
            ```

    *   - Row 2, Col A
        - Row 2, Col B
        - Row 2, Col C

///

You place the `-list-table` [directive][] prior to a list of lists (using the [`la.attr_prefix`][attr_prefix] extension, which is loaded automatically by `la.list_tables`).

Then, each item in the outer list represents a table row, and each item in each inner list representes a table cell.

The use of `#` at the start of a cell indicates a header `<th>` cell (as opposed to a normal `<td>` cell). The use of `#` at the start of a _row_ makes every cell in that row a header cell (whether or not they individually start with `#`); e.g.:

/// markdown-demo
    show_build_file: False

    import lamarkdown as la
    la('la.list_tables')
    la.css('table { border-collapse: collapse; width: 100%; }'
           'td    { border: 1px solid blue; padding: 0.5em}')
    ---

    {-list-table}
    * #
        - Col Heading A
        - Col Heading B
        - Col Heading C
    *   - Row 1, Col A
        - Row 1, Col B
        - Row 1, Col C
    *   - Row 2, Col A
        - Row 2, Col B
        - Row 2, Col C
///


!!! note "Design Notes"

    Python-Markdown includes a built-in `tables` extension, and there are other 3rd-party extensions that add more flexible/featureful approaches to creating tables. These require that you "draw" a table in plain text, using the `-` and `|` ASCII characters, with essentially the same structure as would appear in the output; e.g.:

    ```markdown
    With the `tables` extension:

    Col A | Col B | Col C
    ----- | ----- | -----
    one   | two   | three
    four  | five  | six
    ```

    This is in keeping with the notion that raw Markdown text should closely resemble the formatted output document, so that the raw text can stand on its own. For tables, this ASCII line-drawing approach works well if the cell contents are small and simple.

    However, it becomes difficult for long or complex table data, where problems include:

    * Readability, since (if using the `tables` extension) an entire table row must fit on a single plain-text line without breaks.

    * Maintainability. Even if (using a different extension) you are permitted to split the contents of cells over multiple lines, an ASCII line-drawing approach requires you to keep cell contents boxed within a rectangular region, with other cells to the right and left sharing the same lines. Text editors rarely (if ever, depending on your perspective) provide a convenient way to edit such regions, without disrupting adjacent regions.

    * Technical workability, for when you wish to put block elements like lists or code blocks inside a table cell, or simply multiple paragraphs.

    Other suggestions for the handling of complex tables include:

    1. Use HTML embedded within Markdown, which is technically workable, but does not solve the readability problem, and has debatable maintainability;
    2. Don't, because Markdown "isn't the right tool for the job".

    List tables represent a less severe compromise. The Markdown text and the output are structurally different, but the raw text appears in a relatively readable form that has few technical limits or maintainability challenges.


## Parsing and Co-opting

This extension does not directly parse anything, and does not technically introduce any new syntax.
Rather, it co-opts existing parsing mechanisms, though this requires some care and understanding
from users. Markdown understands `* - # ...` as being the first item in a nested list, containing a
heading. However, it does _not_ understand `* # - ...` as being a nested list of headings; hence we
must leave the `* #` on a separate line.

The `#` character traditionally represents the `<h1>` heading element, and is parsed as such even inside lists. The extension co-opts and rewrites such elements, while leaving other heading levels (`<h2>`-`<h6>`) alone.

!!! note "Design Notes"

    We use `#` for table heading cells on the grounds that:

    1. We require _some_ way to indicate table headings;
    2. In context, using `#` for this is broadly, conceptually consistent with its use elsewhere;
    3. The use of actual `<h1>` elements inside a table is probably unnecessary (and perhaps questionable); and
    4. If one actually does need `<h1>` inside a table, one can still write it using raw HTML (which the extension cannot see).


## Semantic Table Structure

The extension will seek to separate the table into header, body, and footer sections, as follows:

1. Any unbroken sequence of rows at the start of the table that contain _only_ header cells will form the table header (`<thead>`). (If there are no such rows at the start, then `<thead>` is omitted.)

2. Row(s) immediately following the header form part of the table body (`<tbody>`). The body _may_ contain a mix of header (`<th>`) and data (`<td>`) cells, but _may not_ contain a row of only `<th>` cells. (If there are no such rows, then `<tbody>` is omitted.)

3. The next header-cell-only row (if any), after the start of the table body, marks the start of
   the table footer (`<tfoot>`), and the remainder of the table is assigned here. (If there is no
   such row, or if the table body is omitted, then `<tfoot>` is omitted.)


## Heading Trees

The extension permits another way to specify the table header, designed for tables having a
hierarchy of column headings across several rows.

In such cases, one may provide corresponding nested lists representing the header tree structure:

/// markdown-demo
    show_build_file: False

    import lamarkdown as la
    la('la.list_tables')
    la.css('table { border-collapse: collapse; width: 100%; }'
           'thead { border-bottom: 2px solid black; }'
           'th    { border: 1px solid red; padding: 0.5em}'
           'td    { border: 1px solid blue; padding: 0.5em}')
    ---

    {-list-table}
    * #
        - Major Heading A
            - AA
            - AB
                - ABA
                - ABB
        - Major Heading B
            - BA
            - BB

    *   - Row 1, Col AA
        - Row 1, Col ABA
        - Row 1, Col ABB
        - Row 1, Col BA
        - Row 1, Col BB

    *   - Row 2, Col AA
        - Row 2, Col ABA
        - Row 2, Col ABB
        - Row 2, Col BA
        - Row 2, Col BB
///

This _only_ applies to the table header, and for it to work, there must initially be only a single heading row. This is then expanded into further rows as needed to accommodate the subheadings. The extension inserts HTML `rowspan=...` and `colspan=...` attributes to ensure headings occupy the appropriate amount of space.

The number of data columns (5 in this case) is equal to the number of _leaf_ headings in
the heading tree (not the number of headings overall).


## Options

{-list-table}

* #
    - Option
    - Description

*   - `directives`
    - An object for retrieving directives from HTML tree elements. This should be an instance of `lamarkdown.lib.directives.Directives`, and the extension will reuse Lamarkdown's "current" instance by default, if available.




[directive]: ../core.md#directives

[attr_prefix]: attr_prefix.md

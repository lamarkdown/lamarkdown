# `la.attr_prefix`

This extension permits attributes to be written above a block (perhaps with intervening whitespace). This can be compared to the `attr_list` extension, where attributes can be written below a block (or to the right of an inline element).

`la.attr_prefix` can assign styles and [directives](../core.md#directives) to elements that are inaccessible to `attr_list`, including lists, block quotes, and tables. To illustrate:

/// markdown-demo

    import lamarkdown as la
    la('la.attr_prefix', 'tables')
    la.css('.blue { background: #80c0ff; }'
           '.orange { background: #ffc080; }'
           '.fancy { background: #80c0ff; padding: 1em; }'
           '.fancy * { background: #ffc080; }')
    ---
    Ordinary text.

    {.blue}
    Text with styling.

    {.orange}

    More text with styling.

    {.fancy}
    * Styled list item 1
    * Styled list item 2

    {.fancy}
    > Here's a block
    > quote.

    {.fancy}
    Column A | Column B
    -------- | --------
    One      | Two
    Three    | Four

    Ordinary text.
///

With the `attr_list` extension, `{.blue}` and `{.orange}` could be written _below_ their respective elements to achieve the same effect. However, there's no way to do the same for lists, block quotes or tables; `attr_list` will only assign attributes to individual list _items_, or elements within a block quote, or table cells.

The extension addresses another weakness in `attr_list`: other inline parsing logic.

!!! note "Terminology Note"

    An _attribute list_ refers to the syntax `{...}`, generally consisting of style-related information. A fuller example of this is `{.blue #someid attr="value"}`, where `.blue` indicates a CSS class name, `#someid` an element ID, and `attr="value"` is an arbitrary attribute assignment.

    A _list element_ refers to actual document content to be shown to the reader (rendered in HTML as `<ol>` or `<ul>`). In Markdown, this is simply:
    ```markdown
    * List item 1
    * List item 2
    ```

!!! note "Design Notes"

    [Kramdown's syntax](https://kramdown.gettalong.org/syntax.html#block-ials) provides a precedent for attribute lists appearing above blocks.

    `la.attr_prefix` avoids interfering with (or being interfered with by) existing parsing logic, using a two-step process:

    1. It finds and parses attribute lists early in Python-Markdown's "block processing" phase (during which raw blocks of text are converted into tree elements), creating placeholder tree elements for them without, yet, attaching them to anything else.

    2. During the "tree processing" stage, it finally associates each set of attributes with the next (sibling) element in the tree, whatever it is.


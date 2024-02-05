# `la.attr_prefix`

This extension permits attributes to be written above a block (perhaps with intervening whitespace). This can be compared to the `attr_list` extension, where attributes can be written below a block (or to the right of an inline element).

The key motivation is the need to assign styles and [directives](../core.md#directives) to list elements, which `attr_list` cannot do. To illustrate:

/// markdown-demo

    import lamarkdown as la
    la('la.attr_prefix')
    la.css('.blue { background: #80c0ff; }'
           '.orange { background: #ffc080; }'
           '.fancy { background: #80c0ff; padding: 1em; }'
           '.fancy li { background: #ffc080; }')
    ---
    Ordinary text.

    {.blue}
    Text with styling.

    {.orange}

    More text with styling.

    {.fancy}
    * Styled list item 1
    * Styled list item 2

    Ordinary text.
///

With the `attr_list` extension, `{.blue}` and `{.orange}` could be written _below_ their respective elements to achieve the same effect. However, there's no way to do the same for `{.fancy}`. Where numbered or labelled lists of content are concerned, `attr_list` can only assign attributes to individual list _items_, not an overall list.

!!! note "Terminology Note"

    An _attribute list_ refers to the syntax `{...}`. A fuller example of this is `{.blue #someid attr="value"}`, where `.blue` indicates a CSS class name, `#someid` an element ID, and `attr="value"` is an arbitrary attribute assignment.

    A _list element_ refers to part of the actual document content (an `<ol>` or `<ul>` element); e.g.:
    ```markdown
    * List item 1
    * List item 2
    ```

!!! note "Design Notes"

    [Kramdown's syntax](https://kramdown.gettalong.org/syntax.html#block-ials), provides a precedent for attribute list appearing above blocks.

    Also, `la.attr_prefix` avoids interfering with existing parsing logic by operating (mostly) at a document tree level. It will first recognise an attribute list `{...}` at the start of a block, or in a block on its own (which wouldn't otherwise be recognised), and record their positions. After all block elements have been parsed, and the tree structure built, the extension will associate each attribute list with the next (sibling) element in the tree.


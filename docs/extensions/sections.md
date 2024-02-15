# `la.sections`

This extension lets you break up a document into sections---formally, using HTML `<section>` elements---by writing `---`. For instance:

/// markdown-demo

    import lamarkdown as la
    la('la.sections')
    la.css('section { margin: 1em 0; padding: 0 1em; '
           '          border: 1px solid blue; }')
    ---

    Section A.

    \---

    Section B.

    With some more text.

    \---

    Section C.
///

The key motivation is to support the [RevealJS presentation framework](https://revealjs.com/) (and similar), which uses `<section>` elements to define slide show frames.


Each `---` separator must be written on a separate line, surrounded by blank lines.

You may attach attributes to sections by writing an attribute list on the line immediately below `---` (if the `attr_list` extension is loaded); e.g.:

/// markdown-demo

    import lamarkdown as la
    la('la.sections', 'attr_list', 'la.attr_prefix')
    la.css('section { margin: 1em 0; padding: 0 1em; }'
           '.red   { background: #ffc0c0; }'
           '.green { background: #c0ffc0; }'
           '.blue  { background: #c0c0ff; }')
    ---

    \---
    {.red}

    Section A.

    \---
    {.green}

    Section B.

    With some more text.

    \---
    {.blue}

    Section C.
///

For this purpose, a separator is permitted to appear at the very top of the file. This _does not_ create a blank section before all others, but just provides a syntactic feature to let attributes be assigned to the first section.

!!! note "Design Notes"

    RevealJS already provides its own [Markdown plugin](https://revealjs.com/markdown/), but this is a dynamic, JavaScript-based approach that must parse and convert the Markdown each time the document is loaded. Using Lamarkdown, we can achieve the same thing statically (except for the core RevealJS logic), without the load-time performance and memory overhead, and with access to the full range of Python-Markdown extensions.

    The separator `---` is chosen because various Markdown presentation tools already use it: [RevealJS's Markdown plugin](https://revealjs.com/markdown/), [Marp/Marpit](https://marp.app/), [Remark](https://remarkjs.com), [Spectacle](https://commerce.nearform.com/open-source/spectacle/docs/md-slide-layouts/), and possibly others.

    In conventional Markdown, `---` has other uses, depending on where it appears:

    * If immediately below a line of text, it converts that text into an `<h1>` heading. This extension does not interfere with this.

    * Otherwise, `---` normally represents the `<hr>` (horizontal rule) element, and this extension _does_ override this behaviour. However:

        * You can still produce an `<hr>` by writing `----` (or more `-` characters); and
        * You may specify an alternate section separator as a configuration option.


## Options {-no-label}

{-list-table}
* #
    - Option
    - Description

*   - `separator`
    - Sections will be divided by this string (when it appears as its own top-level block). By default, this is `---`.

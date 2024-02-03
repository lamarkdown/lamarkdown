# Extensions

Lamarkdown provides access to [Python-Markdown's extension system](https://python-markdown.github.io/extensions/), to extend the markdown language. (The core language, though clean and simple, is limited.)

In Lamarkdown, you can determine which extensions you want to use in several ways:

* Accept the defaults (which are in place if you don't have a build file);

* Write a [build file](../process.md#build_files) that calls the `lamarkdown` package, providing one or more extension names (or `Extension` objects, typically if you want to [create your own extensions](https://python-markdown.github.io/extensions/api/)):

    ```python
    import lamarkdown as la
    la('attr_list', 'nl2br', 'toc', 'la.cite', 'pymdownx.extra')
    la('la.latex', tex = 'pdflatex')
    ```

* Write a build file that calls [`m.doc()`][doc], or another build module that happens to load extension(s).

* To avoid extensions altogether, simply write a build file that doesn't load any extensions. (This would include avoiding calls to [`m.doc()`][doc] and other build modules.)

{: .note}
> An extension alters the markdown language itself, and/or the structure of the document. A [build module][] (like [`m.doc()`][doc]), by comparison, is a bundle of Lamarkdown configuration that determines _which_ extensions to load, as well as the styling/scripting of the document.

[doc]: ../build_modules/doc.md
[build module]: ../build_modules/index.md


## Standard Lamarkdown Extensions

Extension               | Description                                                                                                  | In `m.doc()`?
-----------             | -----------                                                                                                  | :--:
[la.cite][]             | Builds a bibliography based on Bibtex-formatted reference file(s), and in-text citations of the form `[@citation_key]` (or `[@key1 p.15, @key2]`, etc.). | ✅
[la.eval][]             | Lets you insert placeholders using the syntax `` $`...` ``, to be replaced by corresponding values defined in the build file. If `allow_code` is enabled, this also lets you insert full Python expressions, which will be evaluated and replaced by their result. | ✅ (`allow_code` is False by default)
[la.heading_numbers][]  | Adds a decimal numbering scheme to document headings. |
[la.latex][]            | Lets you insert Latex code, to be compiled, converted to SVG, to be embedded in the output HTML. | ✅
[la.markers][]          | Lets you assign styling to lists. | ✅
[la.sections][]         | Lets you divide a document into `<section>` elements using `---` dividers, which may be used to create slideshows with [RevealJS](https://revealjs.com/), for instance.

[la.cite]: cite.md
[la.eval]: eval.md
[la.heading_numbers]: heading_numbers.md
[la.latex]: latex.md
[la.markers]: markers.md
[la.sections]: sections.md


## [Standard Python Markdown Extensions](https://python-markdown.github.io/extensions/)

These extensions are bundled with the core Python Markdown engine, on which Lamarkdown is based.

Extension        | Description                                                                                                  | In `m.doc()`?
-----------      | -----------                                                                                                  | :--:
[abbr][]         | For abbreviations, using the \<abbr> HTML element.                                                           | ✅
[admonition][]   | For creating callout/admonition boxes, such as for notes, warnings, etc.                                     | ✅
[attr_list][]    | For adding HTML attributes to various elements (which in turn enables CSS styling).                          | ✅
[codehilite][]   | _Consider [pymdownx.superfences][] + [pymdownx.highlight][] instead._                                      |
[def_list][]     | For creating definition lists, using the \<dl>, \<dt> and \<dd> HTML elements.                               | ✅
[extra][]        | Shortcut for [abbr][], [attr_list][], [def_list][], [fenced_code][], [footnotes][], [md_in_html][], [tables][]. _Consider [pymdownx.extra][] instead._ |
[fenced_code][]  | _Consider [pymdownx.superfences][] instead._                                                                 |
[footnotes][]    | For defining labelled footnotes.                                                                             | ✅
[legacy_attrs][] | _Deprecated._                                                                                                |
[legacy_em][]    | For emphasis syntax that more closely matches the markdown reference implementation.                         |
[md_in_html][]   | For nesting Markdown syntax inside embedded HTML.                                                            | ✅
[meta][]         | For adding key-value metadata to the top of markdown files.                                                  | ✅
[nl2br][]        | For treating single newlines in markdown as hard line breaks (rather than whitespace).                       |
[sane_lists][]   | Slightly nicer handling of markdown lists.                                                                   |
[smarty][]       | For auto-replacing quotes, ellipses and dashes with proper, non-ASCII symbols.                               | ✅
[tables][]       | For creating simple tables.                                                                                  | ✅
[toc][]          | Creates a table of contents based on headings in the document.                                               |
[wikilinks][]    | Provides a wiki-style link syntax. _This may not work well with Larmarkdown._                                |

[abbr]: https://python-markdown.github.io/extensions/abbreviations/
[admonition]: https://python-markdown.github.io/extensions/admonition/
[attr_list]: https://python-markdown.github.io/extensions/attr_list/
[codehilite]: https://python-markdown.github.io/extensions/code_hilite/
[def_list]: https://python-markdown.github.io/extensions/definition_lists/
[extra]: https://python-markdown.github.io/extensions/extra/
[fenced_code]: https://python-markdown.github.io/extensions/fenced_code_blocks/
[footnotes]: https://python-markdown.github.io/extensions/footnotes/
[legacy_attrs]: https://python-markdown.github.io/extensions/legacy_attrs/
[legacy_em]: https://python-markdown.github.io/extensions/legacy_em/
[md_in_html]: https://python-markdown.github.io/extensions/md_in_html/
[meta]: https://python-markdown.github.io/extensions/meta_data/
[nl2br]: https://python-markdown.github.io/extensions/nl2br/
[sane_lists]: https://python-markdown.github.io/extensions/sane_lists/
[smarty]: https://python-markdown.github.io/extensions/smarty/
[tables]: https://python-markdown.github.io/extensions/tables/
[toc]: https://python-markdown.github.io/extensions/toc/
[wikilinks]: https://python-markdown.github.io/extensions/wikilinks/



## [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)

These extensions together form a major 3rd-party package. Lamarkdown has a dependency on PyMdown extensions, so they (like those above) are available by default.

Extension                 | Description                                                               | In `m.doc()`?
-----------               | -----------                                                               | :--:
[pymdownx.arithmatex][]   | Preserves Latex math equations during compilation, so they can be parsed and displayed by Javascript libraries (like MathJax or KaTeX) when the output document is viewed. |
[pymdownx.b64][]          | _Consider using Lamarkdown's built-in media embedding instead._           |
[pymdownx.betterem][]     | Tweaks the handling of emphasis syntax (\_ and \*).                       | ✅
[pymdownx.blocks][]       | _Alpha release._                                                          |
[pymdownx.caret][]        | For superscript and insertions with the `^` character, using the \<sup> and \<ins> HTML elements. _See also [pymdownx.tilde][]._ |
[pymdownx.critic][]       | For marking up insertions and deletions, optionally displayed.            |
[pymdownx.details][]      | For hidable/expandable content using the \<details> and \<summary> HTML elements. |
[pymdownx.emoji][]        | For inserting emojis by name.                                             |
[pymdownx.escapeall][]    | Tweaks the handling of \\ to escape any character.                        |
[pymdownx.extra][]        | Shortcut for [pymdownx.betterem][], [pymdownx.superfences][], [abbr][], [attr_list][], [def_list][], [footnotes][], [md_in_html][], [tables][]. | ✅
[pymdownx.highlight][]    | Configures code highlighting for [pymdownx.inlinehilite][] and [pymdownx.superfences][].                                                        | ✅
[pymdownx.inlinehilite][] | For syntax highlighting of inline code snippets within \`...\`.           |
[pymdownx.keys][]         | For showing keyboard keys, using the \<kbd> HTML element.                 |
[pymdownx.magiclink][]    | For auto-linking URLs in the text without any special syntax (or with various alternative syntaxes). |
[pymdownx.mark][]         | For marking/highlighting text using the \<mark> HTML element.             |
[pymdownx.pathconverter][]| _Generally unnecessary in Larmarkdown._                                   |
[pymdownx.progressbar][]  | For showing progress bars (though additional CSS is required).            |
[pymdownx.saneheaders][]  | Tweaks the handling of `#` in markdown headers.                           |
[pymdownx.smartsymbols][] | For inserting various symbols by ASCII characters: `(tm)` for ™, `-->` for →, etc. |
[pymdownx.snippets][]     | For inserting file(s), or parts of a file, into the current markdown document.  |
[pymdownx.striphtml][]    | Strips HTML attributes from a document (and also comments, but this is unnecessary in Lamarkdown). |
[pymdownx.superfences][]  | For multi-line code blocks inside \`\`\`...\`\`\`; more flexible version of [fenced_code][]. | ✅
[pymdownx.tabbed][]       | For creating multiple tabs, each showing different content.               |
[pymdownx.tasklist][]     | For creating checkboxes for list items.                                   |
[pymdownx.tilde][]        | For subscript and deletions with the `~` character, using the \<sub> and \<del> HTML elements. _See also [pymdownx.caret][]._ |

[pymdownx.arithmatex]: https://facelessuser.github.io/pymdown-extensions/extensions/arithmatex/
[pymdownx.b64]: https://facelessuser.github.io/pymdown-extensions/extensions/b64/
[pymdownx.betterem]: https://facelessuser.github.io/pymdown-extensions/extensions/betterem/
[pymdownx.blocks]: https://facelessuser.github.io/pymdown-extensions/extensions/blocks/
[pymdownx.caret]: https://facelessuser.github.io/pymdown-extensions/extensions/caret/
[pymdownx.critic]: https://facelessuser.github.io/pymdown-extensions/extensions/critic/
[pymdownx.details]: https://facelessuser.github.io/pymdown-extensions/extensions/details/
[pymdownx.emoji]: https://facelessuser.github.io/pymdown-extensions/extensions/emoji/
[pymdownx.escapeall]: https://facelessuser.github.io/pymdown-extensions/extensions/escapeall/
[pymdownx.extra]: https://facelessuser.github.io/pymdown-extensions/extensions/extra/
[pymdownx.highlight]: https://facelessuser.github.io/pymdown-extensions/extensions/highlight/
[pymdownx.inlinehilite]: https://facelessuser.github.io/pymdown-extensions/extensions/inlinehilite/
[pymdownx.keys]: https://facelessuser.github.io/pymdown-extensions/extensions/keys/
[pymdownx.magiclink]: https://facelessuser.github.io/pymdown-extensions/extensions/magiclink/
[pymdownx.mark]: https://facelessuser.github.io/pymdown-extensions/extensions/mark/
[pymdownx.pathconverter]: https://facelessuser.github.io/pymdown-extensions/extensions/pathconverter/
[pymdownx.progressbar]: https://facelessuser.github.io/pymdown-extensions/extensions/progressbar/
[pymdownx.saneheaders]: https://facelessuser.github.io/pymdown-extensions/extensions/saneheaders/
[pymdownx.smartsymbols]: https://facelessuser.github.io/pymdown-extensions/extensions/smartsymbols/
[pymdownx.snippets]: https://facelessuser.github.io/pymdown-extensions/extensions/snippets/
[pymdownx.striphtml]: https://facelessuser.github.io/pymdown-extensions/extensions/striphtml/
[pymdownx.superfences]: https://facelessuser.github.io/pymdown-extensions/extensions/superfences/
[pymdownx.tabbed]: https://facelessuser.github.io/pymdown-extensions/extensions/tabbed/
[pymdownx.tasklist]: https://facelessuser.github.io/pymdown-extensions/extensions/tasklist/
[pymdownx.tilde]: https://facelessuser.github.io/pymdown-extensions/extensions/tilde/

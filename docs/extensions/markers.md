---
parent: Extensions
---

# `la.markers`

This extension lets you apply CSS styles to lists (HTML \<ol>, \<ul> and \<dl> elements) (among possibly other use cases).

Normally, markdown does not give us any say in how lists should be styled. We can add attributes to many parts of the document for stylistic purposes, but not lists, because there's no specific syntax for the list as a whole, only for individual list items. With `la.markers`, we can set the numbering scheme of a list to letters or Roman numerals (for instance), and/or apply general CSS declarations.

You may find the [examples below](#example-usage) instructive.

The extension works as follows: it recognises one-line paragraphs (markers) of the form `/{...}` in the markdown document, containing CSS classes/attributes as per the [`attr_list` syntax](https://python-markdown.github.io/extensions/attr_list/). The markers become empty, invisible elements in the output HTML (not shown due to the CSS declaration `display: none`, but logically present). By attaching CSS classes/attributes to these invisible elements, you can use them to style subsequent, visible elements, particularly lists, using the CSS sibling selector `+`.

The extension will be loaded in the following cases:

* By default if you have no build files;

* If any of your build files specify `doc()`:
    ```python
    import lamarkdown as la
    la.m.doc()
    ```

* If any of your build files include it explicitly:
    ```python
    import lamarkdown as la
    la('la.markers')
    ```

## Example Usage

`doc()` provides CSS rules to enable alphabetical or Roman numbering (in place of Arabic numerals). To make use of this, create a marker that specifies the `alpha` or `roman` CSS classes:

```python
import lamarkdown as la
la.m.doc()
```
```markdown
# Markdown Document

/{.alpha}

1. First list element, shown as (a)
2. Second list element, shown as (b)
3. etc.

/{.roman}

1. First list element, shown as (i)
2. Second list element, shown as (ii)
3. etc.
```

The numbers 1, 2 and 3 are still required in the above markdown to create the list in the first place, but the actual HTML will display (a), (b), (c); or (i), (ii), (iii); etc.

You can exert more arbitrary control by specifying CSS rules yourself:

```python
import lamarkdown as la
la('la.markers')
la.css('''
    .boxed + ul, .boxed + ol {
        border: 1px solid black;
    }
''')
```
```markdown
# Markdown Document

/{.boxed}

1. First list element
2. Second list element
3. etc.

The above list appears inside a box.
```

# Markers (`lamarkdown.ext.markers`)

This extension allows CSS styles to be applied to lists (HTML \<ol>, \<ul> and \<dl> elements), to set the numbering scheme to letters or Roman numerals (rather than Arabic numbers), or for general stylistic purposes. Markdown does not (otherwise) have any means of doing this, since there is no overall list syntax (only individual list items) to which you can attach a CSS class/attribute.

You may find the [examples below](#example-usage) simpler than the actual explanation.

The extension works as follows: it recognises one-line paragraphs (markers) of the form `/{...}` in the markdown document, containing CSS classes/attributes as per the [`attr_list` syntax](https://python-markdown.github.io/extensions/attr_list/). The markers become empty, invisible elements in the output HTML (not shown due to the CSS declaration `display: none`, but logically present). By attaching CSS classes/attributes to these invisible elements, you can use them to style subsequent, visible elements, particularly lists, using the CSS sibling selector `+`.

The extension will be loaded in the following cases:

* By default if you have no build files;

* If any of your build files specify `doc()`:
    ```python
    import lamarkdown as la
    la.doc()
    ```

* If any of your build files include it explicitly:
    ```python
    import lamarkdown as la
    la.extension('lamarkdown.ext.markers')
    ```

## Example usage

`doc()` provides CSS rules to enable alphabetical or Roman numbering (in place of Arabic numerals). To make use of this, create a marker that specifies the `alpha` or `roman` CSS classes:

```python
import lamarkdown as la
la.doc()
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
la.extension('lamarkdown.ext.markers')
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

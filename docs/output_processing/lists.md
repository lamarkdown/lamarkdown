---
parent: Output Processing
---

# Lists 

Lamarkdown provides the `:label` output directive, and the `label()` rule, to control the numbering and bullet-point style for lists (either ordered or unordered).

To use the `:label` output directive, you must load [`attr_prefix`](extensions/attr_prefix.md) (loaded by default by [`m.doc()`](../build_modules/doc.md)), as this extension provides the syntax necessary for attaching attributes to a list.

For example:

```markdown
{::label="(a)"}
1. First item
    
    {::label="i."}
    1. First subitem 
    2. Second subitem
    
2. Second item

3. Third item
```

The resulting HTML list will render as follows:
```
(a) First item
    i.  First subitem
    ii. Second subitem
(b) Second item
(c) Third item
```

The directive's value (e.g., "`(a)`") can include any combination of non-alphanumeric symbols, as well as one of the following:

* "`1`", for arabic numbering;
* "`a`", for lower-case alphabetic numbering;
* "`A`", for upper-case alphabetic numbering;
* "`i`", for lower-case Roman numerals;
* "`I`", for upper-case Roman numerals;
* Any of the standard numbering schemes supported by the [`list-style-type` CSS property](https://developer.mozilla.org/en-US/docs/Web/CSS/list-style-type); e.g., `disc`, `square`, `lower-greek`, `thai`.

Additionally, if literal alphanumeric characters need to be included, they can be enclosed in quotes.

{:todo}
TODO: Check the exact syntax for quoting.

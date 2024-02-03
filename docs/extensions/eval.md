---
parent: Extensions
---

# `la.eval`

This extension lets authors insert computed values into documents, with inline expressions of the form `` $`...` `` (or ``` $``...`` ```, etc). There are two approaches to doing this:

## Placeholders and Replacement Values

Users can supply a `dict` of replacement values via the `replace` config option. The extension will look up the text occurring in `` $`...` `` in the dict. If that text is a key in the dict, the whole expression is replaced by the corresponding dict value.

By default (with no configuration), the replacement dict contains keys `date` and `datetime`, allowing authors to write `` $`date` `` or `` $`datetime` `` to insert the current date, or date and time, into the document.

For example, using the defaults:
```markdown
# My Document    
Last updated: $`date`
...
```

Specifying custom replacements:
```python
# md_build.py
import lamarkdown as la
la('la.eval',
    replace = { publisher: "Example Inc.", 
                licence: "CC-BY-4.0" }
)
```
```markdown
# My Document
Published by $`publisher`, licenced $`licence`.
```

## Expression Evaluation

The extension can also execute the contents of `` $`...` `` as raw Python code. This will only be done if (a) the `allow_code` config option is `True` (by default it is `False`), and (b) if there is no matching key in the replacement dict.

When executing code this way, the result will be converted to a string, which will replace the original expression in the output document. For instance, writing `` $`1+1` `` will insert ``2`` into the document.

Such expressions are evaluated within the (combined) scope of any build files. Authors can refer to anything imported or defined in `md_build.py`, or any of the other build files. Thus, if your build file contains `from x import y`, then an expression could be `` $`y()` `` (assuming `y` is callable).

If there is an error in the expression, the error message will instead appear in the document.

This approach has _security implications_. The `allow_code` option must not be enabled if there is any question about whether to trust the author of the markdown file.

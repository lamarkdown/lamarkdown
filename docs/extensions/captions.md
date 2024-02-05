# `la.captions`

Assigns captions to document elements, using the proper HTML elements intended for this purpose
(<figure>, <figcaption>, etc.). (The _appearance_ of such captions is governed by CSS, which is
beyond the scope of this extension.)

To caption an element:

1. Write the caption _before_ the element you are captioning, with a paragraph break in between.

2. Attach the '-caption' directive to the caption. (The 'attr_list' extension will be loaded
   automatically for this purpose.)


## Example

```
Some ordinary
document text.

A diagram for your
consideration.
{-caption}

![Important diagram](diagram.png)

Some more ordinary
document text.
```

This will result in the following HTML:
```
<p>Some ordinary document text.</p>

<figure>
<figcaption>A diagram for your consideration</figcaption>
<img alt="Important diagram" src="diagram.png">
</figure>

<p>Some more ordinary document text.</p>
```

## Tables

HTML <table> elements can have their own embedded <caption> elements. This extension will use this
mechanism instead if the captioned element is a table (e.g., as produced by the 'tables'
extension), although _not_ if a literal <table> element is embedded directly in the markdown.

(Due to the order of processing, directly-embedded HTML elements are not actually included in the
document at the time this extension is run.)

---
parent: Output Processing
---

# Embedding

By default, Lamarkdown embeds all external resources within the output HTML file, with the exception of audio and video files, or anything displayed in an `<iframe>` tag. Embedding resources makes the output HTML file self-sufficient, so it can be stored anywhere and passed around as individual files without losing key features.

The intention is to use HTML in an equivalent fashion to PDF, _not_ necessarily to deploy a website (though the latter is still possible).

Embedding typically uses data URLs ("`data:...`). The external file is read and encoded in base-64, and the original URL is replaced by the base-64 encoding. There are a some special cases:

* CSS stylesheets are embedded _recursively_ (since one CSS file can `@import` another), and the outermost one is not encoded in base-64, but simply inserted into the document using a `<style>` element.

    {: .note}
    > Base-64 encoding increases the size of the data by one third, rounding up, since it uses 8 bits to represent only 6 bits. This effect compounds with nested embedding; i.e., when one CSS stylesheet imports another, which imports a third. Each extra layer of importing leads to less and less efficient encoding.
    >
    > Lamarkdown does not currently "flatten out" the imports, because it cannot guarantee that this would be functionally equivalent, because of certain ordering semantics defined in CSS.
        

* JavaScript files are similarly embedded using a `<script>` element rather than base-64 encoding. However, Lamarkdown currently does not attempt recursive embedding. If your `.js` file imports another `.js` file, the second will remain an external resource.

* When embedding TrueType and OpenType fonts (`.ttf` and `.otf` files), they are first converted to WOFF2 (Web Open Font Format v2), which has higher compression ratios. Embedded fonts are also "subsetted", meaning that unused characters are stripped out.

    {: .note}
    Subsetting is done in a simplistic fashion. Currently, Lamarkdown retains all ASCII characters, as well as any other Unicode code points found throughout the document. However, no attempt is made to determine which characters will be rendered in which fonts. If there are several embedded fonts, some redundant characters may remain.

TODO: `:embed` directive and `embed()` rule.

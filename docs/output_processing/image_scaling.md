---
parent: Output Processing
---

# Image Scaling

Lamarkdown can adjust the size of images in a document by a linear scaling factor. This is done at the HTML level, after markdown processing is complete, so it applies equally to any mechanism for generating or inserting images:

* Images included with the standard markdown notation: "`![Description](http://example.com/image.jpg)`".
* Latex code compiled into SVG using the [`la.latex`](extensions/latex.md) extension.
* SVGs produced by Graphviz, matplotlib, etc., via the [`m.plots`](build_modules/plots.md) build module.
* Anything else that creates `<svg>` or `<img>` elements.

Scaling only alters the size information present in the HTML document. It _doesn't_ affect the actual image content, and so it applies equally to embedded and linked images, and to (practically) any image format supported by web browsers.

However, Lamarkdown only scales "absolutely"-sized images---those whose sizes are given in units of pixels, points, millimetres, inches, etc. Scaling will not be done to images whose sizes expressed in relative units like, `em` (relative to the font size), `%` (relative to the parent element's size) and similar. We assume that relative units express the user's final preference for how large an image should be. (Relative units are unlikely to be present unless the user, or the author of a build module, has explicitly added them.)

For any given image, there are (potentially) two different scale factors: 

* You can give a per-image scaling factor using the `:scale` directive: 1.0 by default.
* The "scaling rule" (a function) gives a particular scaling factor for each image: 1.0 by default.

The combined scaling factor is (normally) the _product_ of these two numbers. However, if the `abs-scale` attribute exists for a given image, Lamarkdown ignores the scaling rule, and only applies the per-image scaling factor.


# Extensions

Markdown syntax is not well-standardised, and [Python-Markdown has an extension system](https://python-markdown.github.io/extensions/) (which Lamarkdown provides access to). Extensions essentially modify the markdown language.

In Lamarkdown, you can determine which extensions you want to use in several ways:

* Accept the defaults (which are in place if you don't have a build file);

* Write a [build file](./BuildFiles) that calls `extension()` or `extensions()`. Normally you would provide one or more extension names, as strings. You could also create and instantiate an Extension class according to the [Python-Markdown API documentation](https://python-markdown.github.io/extensions/api/).

* Write a build file that calls `doc()` or another such function representing a predefined bundle of settings which happens to include an extension.

(To emphasise: an extension only changes the markdown dialect, whereas a build file/module makes decisions about _which_ extensions to use, as well as determining the styling/scripting of the output document.)

## What extensions are available?

* You should be aware of the extensions that come [bundled with Python-Markdown itself](https://python-markdown.github.io/extensions/). Some of these, like [attr_list](https://python-markdown.github.io/extensions/attr_list/) in particular, may be important for styling, scripting and accessibility purposes.

* Lamarkdown provides some of its own extensions:

    * [`lamarkdown.ext.eval`](lamarkdown.ext.eval) lets you insert placeholders using the syntax `` $`...` ``, to be replaced by corresponding values defined in the build file. If `allow_code` is enabled, this also lets you insert full Python expressions, which will be evaluated and replaced by their result.
    * [`lamarkdown.ext.latex`](lamarkdown.ext.latex) lets you insert Latex code, to be compiled, converted to SVG, to be embedded in the output HTML.
    * [`lamarkdown.ext.markers`](lamarkdown.ext.markers) lets you assign styling to lists.
    * [`lamarkdown.ext.sections`](Ext/Sections) lets you divide a document into `<section>` elements using `---` dividers, which may be used to create slideshows with [RevealJS](https://revealjs.com/)), for instance.

* A separate package called [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/) provides a range of other specialist extensions. Lamarkdown has a dependency on PyMdown Extensions, so you should be able to use these without too much trouble.

* The Python-Markdown documentation also lists a [range of other third-party extensions](https://github.com/Python-Markdown/markdown/wiki/Third-Party-Extensions). You will need to manually install these, though.

## Extension configuration

Each extension can have configuration options. In Lamarkdown, these can be set by calling `extension()`, and passing it a keyword argument for each option you want to configure. You can call `extension()` multiple times for a given extension in order to accumulate or overwrite various options. It also returns a dictionary of config options, letting you query their current values and modify them asynchronously.

The `extension()` function is also described in the [Build API](../build_files.md#build-api).

Note that [Python Markdown](https://python-markdown.github.io/reference/) uses a parameter called "`extension_configs`" to specify configuration options to extensions, and Lamarkdown ultimately uses this mechanism, but does not _directly_ expose it to build files.

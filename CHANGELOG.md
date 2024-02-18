# Lamarkdown Changelog

## v0.10

Extensions:

* Added `la.attr_prefix`.
* Added `la.cite`.
* Added `la.captions`.
* Added `la.labels`.
* Added `la.list_tables`.
* Removed `la.heading_numbers` (functionality replaced by `la.labels`).
* Removed `la.markers` (functionality replaced by `la.attr_prefix`).
* `la.latex` supports math code within `$...$` and `$$...$$`.

Build API changes:

* Extensions are added and configured by calling the `lamarkdown` module itself.
* Build modules are now prefixed with `m.` (as in `m.doc()`).
* The `allow_exec` flag (with associated changes to the `la.eval`) extension.
* Some API functions converted into properties: `params`, `build_dir`, `env` and `name`.
* `basename()`.
* `command_formatter()`.
* `extendable()`.
* `fenced_block()`.
* `late()`.

Build modules:

* `m.plots`, with associated functionality for invoking Graphviz, Matplotlib, R, and PlantUML.
* `m.code` uses Pygments for syntax highlighting.
* Removed `cmd`, as it was just duplicating a tiny part of Pygments' functionality.
* Changes to CSS and structural code in `m.doc()`.

Other core functionality:

* '-B' and '-D' flags to control build module logic.
* Resource embedding.
* Image scaling.
* Improved progress, warning and error handling.
* Live updating detects changes to associated resource files.
* "Replacement processor" mechanism for helping to avoid extension conflicts.

Build:

* More unit tests.
* Now use tox, for testing with Py3.8 to 3.12, in combination with mypy and flake8.


## v0.9 (2023-01-11)

Initial release.

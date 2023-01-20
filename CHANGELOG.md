# Lamarkdown Changelog

## v0.10 (2023-01-23?)

New features:

* The new `la.cite` extension parses citations, and uses the 3rd-party Pybtex package to read and format bibliographies.

* We now support additional options for creating/embedding graphics, via Graphviz (`dot`, `neato`, etc.), PlantUML, Matplotlib and R. These packages must all be installed separately, but once installed, the relevant code can be embedded in a `.md` document using 'fences' (as implemented by `pymdownx.superfences`).

Build API changes:

* Breaking change -- the `la.eval` extension's `allow_code` option has been renamed to `allow_exec` (for consistency).

* New API function -- `allow_exec()` specifies, globally, whether executable code should be allowed inside a markdown file. By default, it is set to False. There is a corresponding command-line parameter, `-e`/`--allow-exec`. Currently, the build file overrides the command-line parameter. 

    The `la.eval` extension's own `allow_exec` option takes its default value from the global `allow_exec` value. The Matplotlib and R-plot formatters will refuse to run if `allow_exec` is False.

* New API function -- `fenced_block()` provides a thin wrapper around the `custom_fences` option in the `pymdownx.superfences` extension. But it allows custom fences to be provided one-by-one, and for results to be cached.

* New API function -- `command_formatter()` is a convenience function that provides a 'formatter', intended to be passed to `fenced_block()`, that invokes an external command to do the formatting. (This is used internally, for instance, to invoke Graphviz and PlantUML.)

* New build module -- `plots()` will set up support for Graphviz, PlantUML, Matplotlib, R and possibly other such tools/librarie in the future, via the mechanisms described above. Additionally, `doc()` will call `plots()`, so this functionality is available by default (except that Matplotlib and R will require `allow_exec`).

* The doc() module now uses a 'la-' namespace for its own HTML ID attributes.


Other changes:
* The `la.markers` extension and `cmd()` module now auto-load the attr_list extension (since they cannot work without it).
  
* Added (more) type hints to the API.

* More unit tests added, including for the heading_numbers, latex, markers and sections extensions, and the core compiler logic.

## v0.9 (2023-01-11)

Initial public release.

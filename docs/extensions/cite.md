# `la.cite`

This extension lets you embed citations (e.g., `[@author1990]` or `[see @author1; @author2; @{abc;def!}]`), which
are collected to generate a bibliography, based on an external database file.

(This citation format was inspired by [Pandoc's citation syntax](https://pandoc.org/MANUAL.html#citation-syntax), though it currently has less semantic structure. The extension uses the [Pybtex](https://pybtex.org/) library to read `.bib` files and construct a bibliography.)

/// markdown-demo
    extra_files:
        - ['references.bib', 'Reference database', 'bibtex', 'true']

    import lamarkdown as la
    la('la.cite', file = 'references.bib')
    la.css('#la-bibliography { display: table }'
           '#la-bibliography dt { display: table-cell; }')
    ---
    # references.bib
    @article{refA, author = "An Author",
                   title = "A Title",
                   journal = "The Journal",
                   year = "1990" }
    ---
    ## Referencing Example
    Here's a citation [@refA].

    ### References
    ///References Go Here///

///


## Citation Syntax

A citation consists of `[...]` containing one or more citation keys of the form `@xyz` or `@{xyz}`, at least one of which matches an entry in the reference database. There can be free-form text within the brackets, before, after and in-between citation keys.

In practice, most citations _probably_ contain just one citation key (e.g., `[@author1990]`), or a comma-separated list of them (e.g., `[@abc, @def, @ghi]`).

Without braces, a citation key can consider of letters, digits and `_`, with selected other characters available as single-char internal punctuation (e.g., a key can contain `.` and/or `-`, but cannot start or end with them, nor contain `..` or `--`).

If necessary, a citation key _with_ braces can contain any non-brace characters, as well as singly-nested, matching pairs of braces.


!!! note "Design Notes"

    `la.cite` takes care to check this syntax does not conflict with existing link or image syntax (e.g., `[...](...)`).

    In permitting (nearly) arbitrary special characters within braces, `la.cite` does not permit multiply-nested braces, as this would add implementation complexity for marginal benefit.

    The [BibTeX format](https://metacpan.org/dist/Text-BibTeX/view/btparse/doc/bt_language.pod) describes permitted citation key characters within `.bib` files. However, Pandoc may be the better reference point, being another Markdown implementation.


## Citation and Reference Formats

`la.cite`'s formatting capabilites are a work-in-progress. It currently has quite limited capabilities regarding the way citations and references are displayed in the output HTML.

It is a future ambition to integrate an implementation of CiteProc into `la.cite`.


<!-- ## Bibliography files in Document Metadata -->

<!--

In conjunction with the `meta` extension...

-->

<!--In conjunction with the `meta` extension, you can specify relevant BibTeX files at the top of your Markdown document:

/// markdown-demo

    import lamarkdown as la
    la('la.cite', 'meta')
    ---
///-->


## Options

{-list-table}
* #
    - Option
    - Description

*   - `encoding`
    - The encoding of reference file(s). By default, this is `utf-8-sig` (which represents UTF-8, but expects and skips over any "byte order mark").

*   - `file`
    - A filename, or a list of filenames, of BibTeX-formatted reference list(s). By default, `la.cite` looks for a file called `references.bib`.

        See also `references`.

*   - `format`
    - It's currently recommended to just leave this at the default, `bibtex`.

*   - `hyperlinks`
    - One of `both` (the default), `forward`, `back` or `none`, indicating whether to create hyperlinks from citation to reference (forward/both) and from reference back to citation(s) (back/both).

*   - `ignore_missing_file`
    - If `True` (the default), missing reference files are ignored, rather than reported as errors.

*   - `live_update_deps`
    - A set-like object into which the extension records all external BibTeX files, including those supplied via the `file` option, and also any supplied via document metadata (using the `meta` extension).

        By default, if available, the extension will use Lamarkdown's "current" set of such dependencies.

        This has no effect on the output produced, but assists Lamarkdown in understanding when it should recompile the `.md` document.

*   - `place_marker`
    - The string marking where bibliography entries will be placed. By default, this is `///References Go Here///`. If this is missing, the bibliography will simply be appended to the end of the document.

*   - `progress`
    - An object accepting error, warning and progress messages. This should be an instance of `lamarkdown.lib.Progress`, and the extension will reuse Lamarkdown's "current" instance by default, if available.

*   - `references`
    - Either `None` (the default), or a string directly containing BibTeX-formatted references (or None).

        See also `file`.

*   - `style`
    - One of `alpha`, `plain`, `unsrt` or `unsrtalpha`, indicating how to format citations and references.

<!--
---

            'label_style': [
                '',
                '"" (default), "alpha" or "number".'
            ],
            'name_style': [
                '',
                '"" (default), "lastfirst" or "plain".'
            ],
            'sorting_style': [
                '',
                '"" (default), "author_year_title" or "none".'
            ],
            'abbreviate_names': [
                False,
                'If True, use initials for first/middle names. If False (default), use full names.'
            ],
            'min_crossrefs': [
                2,
                '...'
            ],-->

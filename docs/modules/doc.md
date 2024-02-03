# `m.doc()`

A build module for styling output as a professional-looking document (albeit an unpaginated document), while invoking a range of Markdown extensions to improve productivity. (See the [list of extensions](../extensions/index.md) for the subset of extensions invoked by `m.doc()`.)

`m.doc()` has a slightly special status compared to [other build modules](index.md). It can be used like the others, but it also represents the default build settings for when no build files exist. It is designed to let authors use a sophisticated array of markdown syntax and functionality with zero configuration.

Among other things, `m.doc()` loads the Python Markdown [`toc`](https://python-markdown.github.io/extensions/toc/) (table-of-contents) extension. _If_ the `.md` file contains the placeholder `[TOC]`, then `toc` generates a table-of-contents, and `m.doc()` will cause it to appear as a separately-scrolling sidebar (or in-place if the document is printed).

'''
# la.list_tables Extension

Inspired by reStructuredText's 'list tables':
https://pandemic-overview.readthedocs.io/en/latest/myGuides/reStructuredText-Tables-Examples.html#list-table

## Rationale

With ASCII Markdown tables, you create a table in plain text with essentially the same structure as
would appear in the output, in keeping with the spirit of Markdown. However, this approach becomes
fatally cumbersome for sufficiently complex tables, where you wish cells to contain large blocks of
text or other block elements.

Other suggestions for the handling of complex tables include:

1. Use HTML embedded within Markdown, which is workable, but removes the readability benefit of
   Markdown;
2. Use an alternative, somewhat more flexible form of ASCII table, which may remove certain
   technical limits, but you must still 'draw' the table manually in plain text, which isn't easy
   when there are large block elements involved;
2. Don't, because Markdown "isn't the right tool for the job";

List tables represent a less severe compromise. The markdown code and the output are structurally
different, but the markdown _should_ retain more readability than raw HTML.


## Basic Use

A 'list table' is a table created based on a list of lists. The mechanism permits the creation of
arbitrarily complex tables in Markdown, overcoming the limitations of ASCII tabular formats. Here's
an example:

```
{-list-table}
*   - # Col Heading A
    - # Col Heading B
    - # Col Heading C
*   - Row 1, Col A
    - Row 1, Col B
    - Row 1, Col C
*   - Row 2, Col A
    - Row 2, Col B
    - Row 2, Col C
```

That is, one places the -list-table directive (using the 'la.attr_prefix' extension) prior to a
list of lists. Each item in the outer list then represents a table row, and items in each inner
list represent table cells.

The use of '#' at the start of a cell indicates a 'header' <th> cell (as opposed to a normal <td>
cell). The use of '#' at the start of a _row_ makes every cell in that row a header cell (whether
or not they individually start with '#'; e.g.:

```
{-list-table}
* #
    - Col Heading A
    - Col Heading B
    - Col Heading C
*   - Row 1, Col A
    - Row 1, Col B
    - Row 1, Col C
*   - Row 2, Col A
    - Row 2, Col B
    - Row 2, Col C
```


## Parsing and Co-opting

This extension does not directly parse anything, and does not technically introduce any new syntax.
Rather, it co-opts existing parsing mechanisms, though this requires some care and understanding
from users. Markdown understands '* - # ...' as being the first item in a nested list, containing a
heading. However, it does _not_ understand '* # - ...' as being a nested list of headings; hence we
must leave the '* #' on a separate line.

'#' itself traditionally represents the <h1> element, and is parsed as such even inside lists. We
co-opt and rewrite such elements here, on the grounds that:

1. We require _some_ way to indicate table headings;
2. In context, using '#' for this is broadly, conceptually consistent with its use elsewhere;
3. The use of actual <h1> elements inside a table is probably unnecessary (and perhaps
    questionable); and
4. If one actually does need <h1> inside a table, one can still write it using raw HTML (which the
    extension cannot see).

We don't co-opt any of the other heading levels, which are left alone as <h2>-<h6> elements.


## Semantic Table Structure

The extension will seek to separate the table into header, body, and footer sections, as follows:

1. Any unbroken sequence of rows at the start of the table that contain _only_ header cells will
   form the table header (<thead>). (If there are no such rows at the start, then <thead> is
   omitted.)

2. Row(s) immediately following the header form part of the table body (<tbody>). The body _may_
   contain a mix of header (<th>) and data (<td>) cells, but _may not_ contain a row of only <th>
   cells. (If there are no such rows, then <tbody> is omitted.)

3. The next header-cell-only row (if any), after the start of the table body, marks the start of
   the table footer (<tfoot>), and the remainder of the table is assigned here. (If there is no
   such row, or if the table body is omitted, then <tfoot> is omitted.)


## Heading Trees

The extension permits another way to specify the table header, designed for tables having a
hierarchy of column headings across several rows.

In such cases, one may provide corresponding nested lists representing the header tree structure:

```
{-list-table }
* #
    - Major Heading A
        - Subheading AA
        - Subheading AB
            - Subsubheading ABA
            - Subsubheading ABB
    - Major Heading B
        - Subheading BA
        - Subheading BB
*   - Row 1, Col AA
    - Row 1, Col ABA
    - Row 1, Col ABB
    - Row 1, Col BA
    - Row 1, Col BB
...
```

For this to work, there must initially be only a single heading row, which is then expanded into
further rows as needed to accommodate the subheadings. In the above example, the extension will
produce a table structured as follows (inserting HTML 'rowspan' and 'colspan' attributes to ensure
headings occupy the appropriate amount of space):

```
+-------------------------------------------------------+-------------------------------+
| Major Heading A                                       | Major Heading B               |
+---------------+---------------------------------------+---------------+---------------+
| Subheading AA | Subheading AB                         | Subheading BA | Subheading BB |
|               +-------------------+-------------------+               |               |
|               | Subsubheading ABA | Subsubheading ABB |               |               |
+===============+===================+===================+===============+===============+
| Row 1, Col AA | Row 1, Col ABA    | Row 1, Col ABB    | Row 1, Col BA | Row 1, Col BB |
+---------------+-------------------+-------------------+---------------+---------------+
  ...
```

Note that the number of data columns (5 in this case) is equal to the number of _leaf_ headings in
the heading tree (not the number of headings overall).

'''

from __future__ import annotations
from lamarkdown.lib.progress import Progress
from lamarkdown.lib.directives import Directives
import markdown
from xml.etree import ElementTree

NAME = 'la.list_tables'  # For error messages
LIST_LABEL_DIRECTIVE = 'list-table'


class ListTableTreeProcessor(markdown.treeprocessors.Treeprocessor):

    def __init__(self, md, directives: Directives):
        super().__init__(md)
        self._directives = directives


    def run(self, root):
        for element in root:
            if (element.tag == 'ul'
                    and self._directives.pop_bool(LIST_LABEL_DIRECTIVE, element, NAME)):
                self._convert(element)
            else:
                self.run(element)


    def _convert(self, outer_list_element: ElementTree.Element):
        assert outer_list_element.tag == 'ul'

        thead = ElementTree.Element('thead')
        tbody = ElementTree.Element('tbody')
        tfoot = ElementTree.Element('tfoot')
        section = thead

        keep_first_cells = False
        keep_last_cells = False

        inner_list: list[ElementTree.Element]
        for outer_li in outer_list_element:
            is_heading_row_override = self._unwrap_h1(outer_li)
            inner_list_index, inner_list = self._find_ul(outer_li)

            heading_cells = {e for e in inner_list if self._unwrap_h1(e)}
            is_heading_row = is_heading_row_override or 1 <= len(heading_cells) == len(inner_list)

            if is_heading_row:
                if section is tbody:
                    section = tfoot
            else:
                if section is thead:
                    section = tbody

            row = ElementTree.Element('tr')
            section.append(row)

            first_cell = ElementTree.Element('th' if is_heading_row else 'td')
            first_cell.text = outer_li.text
            first_cell[:] = outer_li[:inner_list_index]
            row.append(first_cell)
            keep_first_cells = (
                keep_first_cells
                or len(first_cell) > 0
                or (first_cell.text is not None and len(first_cell.text.strip()) > 0))

            for cell in inner_list:
                cell.tag = 'th' if is_heading_row_override or cell in heading_cells else 'td'
                row.append(cell)

            if len(inner_list) > 0:
                last_cell = ElementTree.Element('th' if is_heading_row else 'td')
                last_cell.text = outer_li[inner_list_index].tail
                last_cell[:] = outer_li[inner_list_index + 1:]
                row.append(last_cell)
                keep_last_cells = (
                    keep_last_cells
                    or len(last_cell) > 0
                    or (last_cell.text is not None and len(last_cell.text.strip()) > 0))
            else:
                keep_last_cells = True

        if not keep_first_cells:
            for section in [thead, tbody, tfoot]:
                for row in section:
                    del row[0]

        if not keep_last_cells:
            for section in [thead, tbody, tfoot]:
                for row in section:
                    del row[-1]


        # Header tree expansion
        if len(thead) == 1:
            self._expand_header_tree(thead, thead[0][:], 0)

            # Remove unnecessary rowspans from the last row
            for cell in thead[-1]:  # Last row of the header
                cell.attrib.pop('rowspan', None)

        # Put everything together in a <table>
        outer_list_element.tag = 'table'
        del outer_list_element[:]
        for section in [thead, tbody, tfoot]:
            for row in section:
                for cell in row:
                    # Unwrap single block elements within cells
                    if len(cell) == 1 and cell[0].tag in ['p', 'div']:
                        cell.text = ((cell.text or '').strip() + (cell[0].text or '')) or None
                        cell.attrib.update(cell[0].attrib)
                        cell[:] = cell[0][:]

                    self.run(cell)  # Recurse

            if len(section) > 0:
                outer_list_element.append(section)



    def _find_ul(self, element: ElementTree.Element) -> tuple[int, list[ElementTree.Element]]:
        try:
            return next((i, e[:]) for i, e in enumerate(element)
                        if (e.tag == 'ul'
                            and not self._directives.peek(LIST_LABEL_DIRECTIVE, e, NAME)))

        except StopIteration:
            return (0, [])


    def _unwrap_h1(self, element: ElementTree.Element) -> bool:
        if len(element) == 0 or element[0].tag != 'h1' or (element.text and element.text.strip()):
            return False

        h1 = element[0]
        element[:] = h1[:] + element[1:]
        element.text = h1.text  # The pre-existing text should be whitespace, which we overwrite
        element.attrib.update(h1.attrib)

        return True


    def _expand_header_tree(self,
                            thead: ElementTree.Element,
                            cell_list: list[ElementTree.Element],
                            depth: int) -> tuple[int, int]:

        max_depth = depth
        sum_width = 0
        next_row = None

        for cell in cell_list:
            self._unwrap_h1(cell)
            nested_list_index, nested_list = self._find_ul(cell)

            if len(nested_list) == 0:
                # rowspan="0" causes the cell to span all rows until the end of the section.
                # (This requires non-quirks-mode.)
                cell.set('rowspan', '0')
                sum_width += 1

            else:
                cell[:] = cell[:nested_list_index]
                if next_row is None:
                    depth += 1
                    if depth < len(thead):
                        next_row = thead[depth]
                    else:
                        next_row = ElementTree.Element('tr')
                        thead.append(next_row)

                next_row_start = len(next_row)

                for e in nested_list:
                    if e.tag == 'li':
                        e.tag = 'th'
                        next_row.append(e)

                # Treat any material trailing the nested list as if it was a final list element.
                if (nested_list_index + 1) < len(cell):
                    last = ElementTree.Element('th')
                    last[:] = cell[nested_list_index + 1:]
                    last.text = cell[nested_list_index].tail
                    next_row.append(last)

                d, w = self._expand_header_tree(thead, next_row[next_row_start:], depth)
                max_depth = max(max_depth, d)
                sum_width += w
                if w > 1:
                    cell.set('colspan', str(w))

        return max_depth, sum_width


class ListTablesExtension(markdown.Extension):
    def __init__(self, **kwargs):
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass  # Use default defaults

        self.config = {
            'directives': [
                p.directives if p else Directives(Progress()),
                'An object that retrieves directives from document elements.'
            ],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # Auto-load la.attr_prefix. We need to be able to write {-list-table} beforehand to
        # identify the table.
        md.registerExtensions(['la.attr_prefix'], {})

        proc = ListTableTreeProcessor(
            md,
            self.getConfig('directives'),
        )

        # Priority must be lower than attr_list (8) and higher than la.labels (6) (which itself
        # must also be higher than toc (5)).
        md.treeprocessors.register(proc, 'la-list-tables-tree', 7.5)


def makeExtension(**kwargs):
    return ListTablesExtension(**kwargs)

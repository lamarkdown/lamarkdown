# mypy: disable-error-code="attr-defined,operator"

import lamarkdown as la
import pymdownx  # noqa: F401
from lxml.etree import Element
import copy


def apply(heading_numbers = True):
    la(
        'admonition',
        'attr_list',
        'meta',
        'sane_lists',
        'smarty',

        # 3rd Party: pymdown
        'pymdownx.highlight',  # Needed to control whether 'super-fences' uses Pygments or not
        'pymdownx.extra',

        # Lamarkdown internal extensions.
        # (Note: lamarkdown extensions are located in package 'lamarkdown.ext', but the 'la.'
        # prefix is provided as a shorthand.)
        'la.attr_prefix',
        'la.captions',
        'la.cite',
        'la.eval',
        'la.labels',
        'la.list_tables',
    )

    def latex_preamble():
        font_size = la.css_vars.get('la-font-size')
        if font_size.endswith('pt'):
            return rf'\KOMAoptions{{fontsize={font_size}}}'
        return ''

    la('la.latex',
        doc_class_options = la.extendable('class=scrreprt', join=','),
        prepend = la.extendable(la.late(latex_preamble)))

    la('la.labels',
        labels = la.extendable({
            'ol':       '1.,(a),(I)',
            'ul':       '◼ ,▸ ,*',
            'figure':   '"Figure "h1.1. ',
            'table':    '"Table "h1.1. ',
            'listing':  '"Listing "h1.1. ',
            'math':     '(h1.1) ,(math""a) ',
        }))
    if heading_numbers:
        la('la.labels', labels = {'h2': 'H.1\u2001,*'})

    # Table of contents for H2 - H6 elements.
    # (Note: the user can choose NOT to have a table-of-contents just by omitting '[TOC]'.)
    la('toc', toc_depth = '2-6', title = 'Contents')

    la.m.plots()

    for name, value in {
        'la-sans-font':         '"Open Sans", sans-serif',
        'la-serif-font':        '"Merriweather", serif',
        'la-monospace-font':    '"Inconsolata", monospace',
        'la-main-font':         'var(--la-sans-font)',
        'la-header-font':       'var(--la-serif-font)',

        'la-font-size':         '12pt',

        'la-main-color':        'black',
        'la-main-background':   'white',
        'la-side-shadow-color': 'var(--la-main-color)',
        'la-side-background':   '#404040',
        'la-main-width-onscreen':      '50em',
        'la-main-padding-onscreen':    '4em',

        'la-admonition-border-color':  '#606060',
        'la-note-border-color':        '#0060c0',
        'la-note-background':          '#c0d8ff',
        'la-warning-border-color':     '#c03030',
        'la-warning-background':       '#ffc0c0',

        'la-table-border-color':       'black',
        'la-table-head-background':    '#ffc080',
        'la-table-oddrow-background':  'var(--la-main-background)',
        'la-table-evenrow-background': '#fff0e0',

        'la-figure-background':        '#e0e0e0',
        'la-caption-background':       '#d0d0d0',
        'la-figure-label-color':       '#c04000',

        'la-bullet1-color':            '#0080ff',
        'la-bullet2-color':            '#80c0ff',
        'la-number-color':             '#ff6000',

        'la-ul-indent':         '2em',
        'la-ul-marker-sep':     '0.5em',
        'la-ol-marker-width':   '1.5em',
        'la-ol-marker-sep':     '0.5em',

        'la-box-corner-radius': '5px',
    }.items():
        if name not in la.css_vars:
            la.css_vars[name] = value

    la.css_files(
        'https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,700;1,400;1,700&'
        'family=Merriweather&family=Inconsolata:wght@500'
    )

    la.css(r'''
        @media screen {
            html, body {
                background: var(--la-side-background);
                margin: 0;
            }
            body {
                display: flex;
                flex-direction: row;
                width: 100%;
            }
            #la-doc {
                overflow-x: visible;
                margin-left: auto;
                margin-right: auto;
                width: var(--la-main-width-onscreen);
                box-shadow: 5px 5px 10px var(--la-side-shadow-color);
                padding: var(--la-main-padding-onscreen);
            }
            pre {
                overflow: auto;
            }
        }

        @media print {
            pre {
                /* In paper/PDF, 'pull out all stops' to ensure that all code is visible, even if
                   we must break lines in strange places. */
                white-space: pre-wrap;
                word-break: break-all;
            }
        }

        html, body {
            font-family: var(--la-main-font);
            font-size: var(--la-font-size);
            line-height: 1.8em;
        }

        #la-doc {
            color:      var(--la-main-color);
            background: var(--la-main-background);
        }
    ''')

    la.css_rule(
        ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        'font-family: var(--la-header-font);'
    )

    la.css_rule(
        ['h2', 'h3', 'h4', 'h5', 'h6'],
        'margin-top: 1.5em;'
    )

    la.css_rule('pre', 'line-height: 1.3;')
    la.css_rule('code', 'font-family: var(--la-monospace-font);')

    la.css(
        'math > * { font-size: var(--la-font-size); }',
        if_selectors = 'math'
    )

    la.css_rule(
        ['details', '.admonition'],
        '''
        border-radius: var(--la-box-corner-radius);
        border: 1px solid var(--la-admonition-border-color);
        padding: 0 1em;
        margin: 0.5em 0;
        '''
    )

    la.css_rule(
        ['summary', '.admonition-title'],
        '''
        font-weight: bold;
        font-family: var(--la-main-font);
        '''
    )

    la.css_rule(
        '.note',
        '''
        border: 1px solid var(--la-note-border-color);
        background: var(--la-note-background);
        '''
    )

    la.css_rule(
        '.warning',
        '''
        border: 1px solid var(--la-warning-border-color);
        background: var(--la-warning-background);
        '''
    )


    la.css_rule(
        ['ul', 'ol'],
        '''
        width: 100%;
        padding-left: 0;
        padding-right: 0;
        margin-left: 0;
        margin-right: 0;
        ''')

    la.css(
        r'''
        ul > li {
            position: relative;
            margin-left: var(--la-ul-indent);
        }

        ul > li::before {
            position: absolute;
            right: 100%;
            padding-right: var(--la-ul-marker-sep);
            color: var(--la-bullet1-color);
        }
        ''',
        if_selectors = ['ul']
    )

    la.css(
        r'''
        ul ul > li::before {
            color: var(--la-bullet2-color);
        }
        ''',
        if_selectors = 'ul ul'
    )

    la.css(
        r'''
        ol > li {
            display: table;
            margin-left: 0;
            margin-right: 0;
            padding-left: 0;
            padding-right: 0;
            width: 100%;
        }

        ol > li::before {
            display: table-cell;
            width: var(--la-ol-marker-width);
            padding-right: var(--la-ol-marker-sep);
            color: var(--la-number-color);
            font-weight: bold;
        }

        /* Without 'display: table', the block (e.g., <p>) child elements of adjacent <li>
           elements will have their vertical margins collapsed together (which is visually
           appropriate), whereas 'display: table' causing such margins to concatenate, yielding
           unexpected amounts of vertical space.

           Thus, we have to do some explicit margin tinkering to avoid doubling-up on vertical
           margins. */

        ol > li:first-child > :first-child {
            /* No space before the first item in the first list item. Subsequent items retain any
               top-margin, which will represent the total internal space between list items. */
            margin-top: 0;
        }

        ol > li > :last-child,
        ol > li > :last-child > :last-child,
        ol > li > :last-child > :last-child > :last-child {
            /* No space after last item (or its last child/grandchild) in any of the list items. */
            margin-bottom: 0;
        }
        ''',
        if_selectors = 'ol'
    )

    la.css(
        r'''
        ol:not(.la-labelled) {
            counter-reset: list-item;
        }

        ol:not(.la-labelled) > li {
            counter-increment: list-item;
        }

        ol:not(.la-labelled) > li::before {
            content: counter(list-item, decimal) ". ";
        }
        ''',
        if_selectors = 'ol:not(.la-labelled)'
    )

    la.css(
        r'''
        table {
            border-collapse: collapse;
            border-bottom: 1px solid var(--la-table-border-color);
        }

        table thead tr {
            background-color: var(--la-table-head-background);
            border-top: 1px solid var(--la-table-border-color);
            border-bottom: 1px solid var(--la-table-border-color);
        }

        td, th {
            padding: 0.5em 1em;
        }

        tbody tr:nth-child(odd) {
            background-color: var(--la-table-oddrow-background);
        }

        tbody tr:nth-child(even) {
            background-color: var(--la-table-evenrow-background);
        }
        ''',
        if_selectors = 'table'
    )

    la.css_rule(
        'figure',
        '''
        background: var(--la-figure-background);
        display: table;
        margin: 1em 0;
        padding: 0.5em;
        '''
    )

    la.css_rule(
        'figcaption',
        '''
        display: table-caption;
        width: 100%;
        text-align: left;
        '''
    )

    la.css(
        r'''
        figcaption > .la-label {
            font-weight: bold;
            color: var(--la-figure-label-color);
        }
        ''',
        if_selectors = 'figcaption > .la-label'
    )

    la.css(
        r'''
        @media screen {
            #la-toc-sidebar {
                position: sticky;
                width: 20em;
                height: 100%;
                max-height: 95vh;
                top: 0px;
                overflow-y: scroll;
                resize: horizontal;
                background: var(--la-main-background, white);
                box-shadow: 5px 5px 10px var(--la-side-shadow-color, black);
            }

            #la-toc-inline {
                display: none;
            }
        }

        @media print {
            #la-toc-sidebar {
                display: none;
            }
        }

        .la-toc {
            padding: 1em;
        }

        .la-toc .toctitle {
            font-weight: bold;
            margin: 0;
        }

        .la-toc ul {
            list-style-type: none;
        }

        .la-toc > ul > li {
            margin-left: 0;
        }

        .la-toc a {
            text-decoration: none;
        }

        .la-toc a:hover {
            text-decoration: underline;
        }
        ''',
        if_selectors = '.la-toc'
    )

    la.css(
        r'''
        #la-bibliography {
            display: grid;
            width: 100%;
            grid-template-columns: 0fr 1fr;
        }

        #la-bibliography > dt {
            grid-column: 1;
            margin-top: 1ex;
        }

        #la-bibliography > dd {
            grid-column: 2;
            margin-top: 1ex;
        }
        ''',
        if_selectors = '#la-bibliography'
    )

    def create_structure(root):
        doc_element = Element('div', attrib = {'id': 'la-doc'})
        doc_element[:] = root[:]
        root[:] = [doc_element]

        if toc_list := doc_element.xpath('//*[@class="toc"]'):
            inline_toc = toc_list[0]
            inline_toc.attrib['class'] = 'la-toc'
            sidebar_toc = copy.deepcopy(inline_toc)
            if sidebar_toc_title := sidebar_toc.xpath('./span[1]'):
                sidebar_toc_title[0].text = la.meta['title'] or 'Contents'


            inline_toc.attrib['id'] = 'la-toc-inline'
            sidebar_toc.attrib['id'] = 'la-toc-sidebar'
            root.insert(0, sidebar_toc)

    la.with_tree(create_structure)

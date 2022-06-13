import lamarkdown as la
import pymdownx

def apply():
    la.extensions(
        'admonition', # 'Notes', 'warnings', etc.
        'meta',       # Allows for defining metadata in the markdown.
        'smarty',     # Auto-replacement of quotes, ellipses and dashes.
        'attr_list',

        # 3rd Party: pymdown
        'pymdownx.highlight', # Needed for control over whether 'super-fences' uses Pygments or not
        'pymdownx.extra',

        # Lamarkdown internal extensions
        'lamarkdown.ext.latex',
        'lamarkdown.ext.eval',
        'lamarkdown.ext.markers',
    )

    for name, value in {
        'la-sans-font':         '"Open Sans", sans-serif',
        'la-serif-font':        '"Merriweather", serif',
        'la-monospace-font':    '"Inconsolata", monospace',
        'la-main-font':         'var(--la-sans-font)',
        'la-header-font':       'var(--la-serif-font)',

        'la-main-color':        'black',
        'la-main-background':   'white',
        'la-side-shadow-color': 'var(--la-main-color)',
        'la-side-background':   '#404040',

        'la-admonition-border-color':  '#606060',
        'la-note-border-color':        '#0060c0',
        'la-note-background':          '#c0d8ff',
        'la-warning-border-color':     '#c03030',
        'la-warning-background':       '#ffc0c0',

        'la-table-border-color':       'black',
        'la-table-head-background':    '#ffc080',
        'la-table-oddrow-background':  'var(--la-main-background)',
        'la-table-evenrow-background': '#fff0e0',

        'la-bullet1-color': '#0080ff',
        'la-bullet1-shape': r'"\25A0"',
        'la-bullet2-color': '#80c0ff',
        'la-bullet2-shape': r'"\25B8"',
        'la-number-color': '#ff6000',
    }.items():
        if name not in la.css_vars:
            la.css_vars[name] = value

    la.css_files(
        'https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,700;1,400;1,700&family=Merriweather&family=Inconsolata:wght@500&display=swap'
    )

    la.css(r'''
        @media screen {
            html { background: var(--la-side-background); }
            body {
                box-shadow: 5px 5px 10px var(--la-side-shadow-color);
                max-width: 50em;
                padding: 4em;
                margin-left: auto;
                margin-right: auto;
            }
        }

        html {
            font-family: var(--la-main-font);
            line-height: 1.8em;
        }

        body {
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

    la.css_rule('pre', 'line-height: 1.7em;')
    la.css_rule('code', 'font-family: var(--la-monospace-font);')

    la.css_rule(
        '.admonition',
        '''
        border-radius: 5px;
        border: 1px solid var(--la-admonition-border-color);
        padding: 0 1em;
        margin: 1ex 0;
        '''
    )

    la.css_rule(
        '.admonition-title',
        '''
        font-weight: bold;
        font-family: var(--la-main-font);
        '''
    )

    la.css_rule(
        '.admonition.note',
        '''
        border: 1px solid var(--la-note-border-color);
        background: var(--la-note-background);
        '''
    )

    la.css_rule(
        '.admonition.warning',
        '''
        border: 1px solid var(--la-warning-border-color);
        background: var(--la-warning-background);
        '''
    )

    la.css(
        r'''
        ul > li::marker {
            color: var(--la-bullet1-color);
            content: var(--la-bullet1-shape) '\00A0';
        }
        ''',
        if_selectors = 'ul'
    )

    la.css(
        r'''
        ul ul > li::marker {
            color: var(--la-bullet2-color);
            content: var(--la-bullet2-shape) '\00A0';
        }
        ''',
        if_selectors = 'ul ul'
    )

    la.css(
        r'''
        ol {
            width: 100%;
            counter-reset: listitem;
            padding: 0;
        }

        ol > li {
            display: table;
            counter-increment: listitem;
        }

        ol > li::before {
            content: counters(listitem, ".") ". ";
            display: table-cell;
            width: 2ex;
            padding-right: 0.5em;
            color: var(--la-number-color);
            font-weight: bold;
        }

        ol > li > p:first-child {
            /* It seems that, without 'display: table', the <p> child elements of adjacent <li> elements will share their vertical margins, whereas 'display: table' causes those margins to exist separately. Thus, we want to set the bottom margin to zero to avoid too much vertical space. */
            margin-top: 0;
        }

        ol > li > :last-child {
            margin-bottom: 0;
        }
        ''',
        if_selectors = 'ol'
    )

    la.css(
        r'''
        ol ol > li::before {
            width: 3ex;
        }
        ''',
        if_selectors = 'ol ol'
    )

    la.css(
        r'''
        ol ol ol > li::before {
            width: 4ex;
        }
        ''',
        if_selectors = 'ol ol ol'
    )

    la.css(
        r'''
        .alpha + ol > li::before {
            content: "(" counter(listitem, lower-alpha) ") ";
        }
        ''',
        if_selectors = '.alpha + ol'
    )

    la.css(
        r'''
        .roman + ol > li::before {
            content: "(" counter(listitem, lower-roman) ") ";
        }
        ''',
        if_selectors = '.roman + ol'
    )

    la.css(
        r'''
        li {
            margin: 0.5em 0 0.5em 0;
            padding-left: 0.5em;
            padding-top: 0em;
            width: calc(100% - 1ex);
            margin-left: -1ex;
        }
        ''',
        if_selectors = ['ul', 'ol']
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

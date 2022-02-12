import lamarkdown as md
import pymdownx

md.extensions(
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

md.css(r'''
    @import url('https://fonts.googleapis.com/css2?family=Merriweather&family=Merriweather+Sans&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@500&family=Merriweather&family=Merriweather+Sans&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,700;1,400;1,700&display=swap');

    @media screen {
        html { background: #404040; }
        body {
            box-shadow: 5px 5px 10px black;
            max-width: 50em;
            padding: 4em;
            margin-left: auto;
            margin-right: auto;
        }
    }

    html {
        font-family: 'Open Sans', sans-serif;
        line-height: 1.8em;
    }

    body {
        background: white;
        counter-reset: section;
    }
''')

md.css_rule(
    ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
    'font-family: "Merriweather", serif;'
)

md.css_rule(
    ['h2', 'h3', 'h4', 'h5', 'h6'],
    'margin-top: 1.5em;'
)

md.css(
    r'''
    h2:not(.notnumbered) {
        counter-reset: subsection;
        counter-increment: section;
    }

    h2:not(.notnumbered)::before {
        content: counter(section);
        margin-right: 1em;
    }
    ''',
    if_selectors = 'h2:not(.notnumbered)'
)

md.css(
    r'''
    h3:not(.notnumbered) {
        counter-reset: subsubsection;
        counter-increment: subsection;
    }

    h3:not(.notnumbered)::before {
        content: counter(section) "." counter(subsection);
        margin-right: 1em;
    }
    ''',
    if_selectors = 'h3:not(.notnumbered)'
)

md.css(
    r'''
    h4:not(.notnumbered) {
        counter-increment: subsubsection;
    }

    h4:not(.notnumbered)::before {
        content: counter(section) "." counter(subsection) "." counter(subsubsection);
        margin-right: 1em;
    }
    ''',
    if_selectors = 'h4:not(.notnumbered)'
)

md.css_rule('pre', 'line-height: 1.7em;')
md.css_rule('code', 'font-family: "Inconsolata", monospace;')

md.css_rule(
    '.admonition',
    '''
    border-radius: 5px;
    border: 1px solid #606060;
    padding: 0 1em;
    margin: 1ex 0;
    '''
)

md.css_rule(
    '.admonition-title',
    '''
    font-weight: bold;
    font-family: "Merriweather Sans", sans-serif;
    '''
)

md.css_rule(
    '.admonition.note',
    '''
    border: 1px solid #0060c0;
    background: #c0d8ff;
    '''
)

md.css_rule(
    '.admonition.warning',
    '''
    border: 1px solid #c03030;
    background: #ffc0c0;
    '''
)

md.css(
    r'''
    ul > li::marker {
        color: #0080ff;
        content: '\25A0\00A0';
    }
    ''',
    if_selectors = 'ul'
)

md.css(
    r'''
    ul ul > li::marker {
        color: #80c0ff;
        content: '\25B8\00A0';
    }
    ''',
    if_selectors = 'ul ul'
)

md.css(
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
        color: #ff6000;
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

md.css(
    r'''
    ol ol > li::before {
        width: 3ex;
    }
    ''',
    if_selectors = 'ol ol'
)

md.css(
    r'''
    ol ol ol > li::before {
        width: 4ex;
    }
    ''',
    if_selectors = 'ol ol ol'
)

md.css(
    r'''
    .alpha + ol > li::before {
        content: "(" counter(listitem, lower-alpha) ") ";
    }
    ''',
    if_selectors = '.alpha + ol'
)

md.css(
    r'''
    .roman + ol > li::before {
        content: "(" counter(listitem, lower-roman) ") ";
    }
    ''',
    if_selectors = '.roman + ol'
)

md.css(
    '''
    li {
        margin: 0.5em 0 0.5em 0;
        padding-left: 0.5em;
        padding-top: 0em;
        width: calc(100% - 1ex);
    }
    ''',
    if_selectors = ['ul', 'ol']
)

md.css(
    '''
    table {
        border-collapse: collapse;
        border-bottom: 1px solid black;
    }

    table thead tr {
        background-color: #ffc080;
        border-top: 1px solid black;
        border-bottom: 1px solid black;
    }

    td, th {
        padding: 0.5em 1em;
    }

    tbody tr:nth-child(odd) {
        background-color: white;
    }

    tbody tr:nth-child(even) {
        background-color: #fff0e0;
    }
    ''',
    if_selectors = 'table'
)

import lamarkdown as md

def apply():
    md.extensions('admonition')

    md.css(
        r'''
        [nmarks]:not([nmarks="1"])::after {
            content: "[" attr(nmarks) " marks]";
        }
        ''',
        if_selectors = '[nmarks]:not([nmarks="1"])'
    )

    md.css(
        r'''
        [nmarks="1"]::after {
            content: "[1 mark]";
        }
        ''',
        if_selectors = '[nmarks="1"]'
    )

    md.css(
        r'''
        [nmarks]::after {
            display: block;
            text-align: right;
            font-weight: bold;
            position: relative;
        }
        ''',
        if_selectors = '[nmarks]'
    )

    md.css(
        r'''
        .inline {
            position: relative;
        }

        .inline[nmarks]::after {
            position: absolute;
            right: 0pt;
            bottom: 0pt;
        }
        ''',
        if_selectors = '.inline[nmarks]'
    )

    md.css_rule(
        '.admonition.answer',
        '''
        border: 1px solid #c000c0;
        background: #ffe0ff;
        '''
    )

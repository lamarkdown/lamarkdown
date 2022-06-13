import lamarkdown as la

def apply():
    la.extensions('admonition')

    la.css(
        r'''
        [nmarks]:not([nmarks="1"])::after {
            content: "[" attr(nmarks) " marks]";
        }
        ''',
        if_selectors = '[nmarks]:not([nmarks="1"])'
    )

    la.css(
        r'''
        [nmarks="1"]::after {
            content: "[1 mark]";
        }
        ''',
        if_selectors = '[nmarks="1"]'
    )

    la.css(
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

    la.css(
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

    la.css_vars['la-answer-border-color'] = '#c000c0';
    la.css_vars['la-answer-background'] = '#ffe0ff';
    la.css_rule(
        '.admonition.answer',
        '''
        border: 1px solid var(--la-answer-border-color);
        background: var(--la-answer-background);
        '''
    )

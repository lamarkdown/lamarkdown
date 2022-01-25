import lamarkdown as md

md.extensions('admonition')

md.css(r'''
    [nmarks]:not([nmarks="1"])::after {
        content: "[" attr(nmarks) " marks]";
    }

    [nmarks="1"]::after {
        content: "[1 mark]";
    }

    [nmarks]::after {
        display: block;
        text-align: right;
        font-weight: bold;
        position: relative;
    }

    .inline {
        position: relative;
    }

    .inline[nmarks]::after {
        position: absolute;
        right: 0pt;
        bottom: 0pt;
    }
    
    .admonition.answer {
        border: 1px solid #c000c0;
        background: #ffe0ff;
    }
''')

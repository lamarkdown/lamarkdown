import lamarkdown as la

def apply(from_level: int = 2, to_level: int = 6, title = 'Contents'):
    la.extension('toc',
                title = title,
                toc_depth = f'{from_level}-{to_level}')

    la.css(
        r'''
        @media screen {
            .toc {
                position: fixed;
                z-index: -1;
                left: 1ex;
                top: 1ex;
                overflow: auto;
                width: 20em;
                max-height: 90%;
                border-radius: 0.5ex;
                background: var(--la-main-background);
                box-shadow: 5px 5px 10px var(--la-side-shadow-color);
            }

            .toc:hover, .toc:focus {
                z-index: 1;
            }
        }

        .toc {
            padding: 1em;
        }

        .toc .toctitle {
            font-weight: bold;
            margin: 0;
        }

        .toc ul {
            padding-left: 1.5em;
        }
        ''',
        if_selectors = '.toc'
    )

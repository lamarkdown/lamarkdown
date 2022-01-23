import lamarkdown as md

md.extension('toc', {
    'title': 'Contents',
    'toc_depth': '2-6'
})

md.css(r'''
    @media screen {
        .toc {
            position: fixed;
            z-index: -1;
            left: 1ex;
            top: 1ex;
            width: 20em;
            border-radius: 0.5ex;
            background: white;
            box-shadow: 5px 5px 10px black;
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
''')

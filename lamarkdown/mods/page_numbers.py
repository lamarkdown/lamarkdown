from lamarkdown import *

def apply(pageHeight = 1200):
    css(r'''
        @media screen {
            body {
                position: relative;
            }

            .pageN {
                position: absolute;
                right: 0%;
                top: 0%;
                background: var(--la-main-background);
                color: var(--la-main-color);
                padding: 0 1em;
                margin-top: -1px;
            }

            .pageN:not(:last-child) {
                border-bottom: 1px solid var(--la-main-color);
            }
        }

        @media print {
            .pageN {
                display: none;
            }
        }
    ''')

    js(f'const pageHeight = {pageHeight};' +
        r'''
        function pageN(t, n)
        {
            let elem = document.createElement('div');
            elem.className = 'pageN';
            elem.style.top = `calc(${t}px - 1em)`;
            elem.textContent = n;
            elem.title = 'Pseudo page number';
            document.body.append(elem);
        }

        const totalHeight = document.body.clientHeight;
        let n = 1;
        let t = pageHeight;
        while(t < totalHeight)
        {
            pageN(t, n);
            n += 1;
            t += pageHeight;
        }

        let elem = document.createElement('div');
        elem.className = 'pageN';
        elem.style.top = 'auto';
        elem.style.bottom = '0';
        elem.textContent = n;
        elem.title = 'Pseudo page number';
        document.body.append(elem);
    ''')

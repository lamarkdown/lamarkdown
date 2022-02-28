from lamarkdown import *

def apply():
    css(r'''
        @media screen {
            body {
                position: relative;
            }

            .pageN {
                position: absolute;
                right: 0%;
                top: 0%;
                background: white;
                color: black;
                #box-shadow: 8px 5px 7px black;
                border-top: 1px solid black;
                padding: 0 1em;
                margin-top: -1px;
            }
        }
    ''')

    js(r'''
        const totalHeight = document.body.offsetHeight;
        let n = 1;
        for(let t = 0; t < totalHeight; t += 1200)
        {
            let pageN = document.createElement('div');
            pageN.className = 'pageN';
            pageN.style.top = t + 'px';
            pageN.textContent = n;
            pageN.title = 'Pseudo page number';
            document.body.append(pageN);
            n += 1;
        }
    ''')

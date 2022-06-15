from lamarkdown import *

def apply(pageHeight = 1200, element_id = 'document'):
    css(fr'''
        @media screen {{
            #{element_id} {{
                position: relative;
            }}

            .pageN {{
                position: absolute;
                right: 0%;
                top: 0%;
                background: var(--la-main-background, white);
                color: var(--la-main-color, black);
                padding: 0 1em;
                margin-top: -1px;
                border-bottom: 1px solid var(--la-main-color, black);
            }}
        }}

        @media print {{
            .pageN {{
                display: none;
            }}
        }}
    ''')

    #.pageN {{
        #position: absolute;
        #right: 0%;
        #top: 0%;
        #background: var(--la-main-background, white);
        #color: var(--la-main-color, black);
        #padding: 0 1em;
        #margin-top: -1px;
    #}}

    #.pageN:not(:last-child) {{
        #border-bottom: 1px solid var(--la-main-color, black);
    #}}

    js(fr'''
        (() =>
        {{
            const pageHeight = {pageHeight};
            const doc_element = document.getElementById('{element_id}');
            function pageN(t, n)
            {{
                let elem = document.createElement('div');
                elem.className = 'pageN';
                elem.style.top = `calc(${{t}}px - 1em)`;
                elem.textContent = n;
                elem.title = 'Pseudo page number';
                doc_element.append(elem);
            }}

            const totalHeight = doc_element.scrollHeight;
            let n = 1;
            let t = pageHeight;
            while(t < totalHeight)
            {{
                pageN(t, n);
                n += 1;
                t += pageHeight;
            }}
        }})()
    ''')

            #/*let elem = document.createElement('div');
            #elem.className = 'pageN';
            #elem.style.top = 'auto';
            #elem.style.bottom = '0';
            #elem.textContent = n;
            #elem.title = 'Pseudo page number';
            #doc_element.append(elem);*/

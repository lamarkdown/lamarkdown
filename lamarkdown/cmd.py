from lamarkdown import *

css(r'''
    .unixcmd::before, .wincmd::before, [prompt]::before, .unixcmd br+::before, .wincmd br+::before, [prompt] br+::before {
        font-family: 'Inconsolata', monospace;
        color: #808080;
    }

    .unixcmd::before, .unixcmd br+::before {
        content: "[user@pc]$ ";
    }

    .wincmd::before, wincmd br+::before {
        content: "C:\\> ";
    }

    [prompt]::before, [prompt] br+::before {
        content: attr(prompt) " ";
    }
''')

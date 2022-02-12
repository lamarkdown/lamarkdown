from lamarkdown import *

css(r'''
    .unixcmd::before, .wincmd::before, [prompt]::before, .unixcmd br+::before, .wincmd br+::before, [prompt] br+::before {
        font-family: 'Inconsolata', monospace;
        color: #808080;
    }
    ''',
    if_selectors = ['.unixcmd', '.wincmd', '[prompt]']
)

css(
    r'''
    .unixcmd::before, .unixcmd br+::before {
        content: "[user@pc]$ ";
    }
    ''',
    if_selectors = '.unixcmd'
)

css(
    r'''
    .wincmd::before, wincmd br+::before {
        content: "C:\\> ";
    }
    ''',
    if_selectors = '.wincmd'
)

css(
    r'''
    [prompt]::before, [prompt] br+::before {
        content: attr(prompt) " ";
    }
    ''',
    if_selectors = '[prompt]'
)

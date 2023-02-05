import lamarkdown as la

# Allows authors to mark certain paragraphs as (sets of) Unix/Windows/other commands.

# Limitation: currently the '{prompt=...}' syntax can only apply to one command at a time (due to
# CSS limitations).

def apply(unix_prompt = '[user@pc]$', win_prompt = r'C:\>'):

    # We rely on attr_list to mark the line/paragraph to be styled as command(s).
    la('attr_list')

    la.css_vars['la-prompt-color'] = '#808080';
    la.css_vars['la-unix-prompt-shape'] = '"' + unix_prompt.replace('\\', '\\\\') + '"'
    la.css_vars['la-win-prompt-shape']  = '"' + win_prompt.replace('\\', '\\\\') + '"'

    la.css(r'''
        .unixcmd::before, .wincmd::before, [prompt]::before, .unixcmd br+::before, .wincmd br+::before, [prompt] br+::before {
            font-family: var(--la-monospace-font, monospace);
            color: var(--la-prompt-color);
        }
        ''',
        if_selectors = ['.unixcmd', '.wincmd', '[prompt]']
    )

    la.css(
        r'''
        .unixcmd::before, .unixcmd br+::before {
            content: var(--la-unix-prompt-shape) " ";
        }
        ''',
        if_selectors = '.unixcmd'
    )

    la.css(
        r'''
        .wincmd::before, wincmd br+::before {
            content: var(--la-win-prompt-shape) " ";
        }
        ''',
        if_selectors = '.wincmd'
    )

    la.css(
        r'''
        [prompt]::before, [prompt] br+::before {
            content: attr(prompt) " ";
        }
        ''',
        if_selectors = '[prompt]'
    )

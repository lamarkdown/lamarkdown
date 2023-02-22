import lamarkdown as la

def apply(fenced = True, inline = True,
          style = 'default', noclasses = False,
          css_class = 'la-cd',
          **kwargs):

    style = kwargs.get('pygments_style', style)

    la('pymdownx.highlight', pygments_style = style,
                             noclasses = noclasses,
                             css_class = css_class,
                             **kwargs)
    if fenced: la('pymdownx.superfences')
    if inline: la('pymdownx.inlinehilite')

    if not noclasses:
        import pygments.formatters
        class Fmt(pygments.formatters.HtmlFormatter):
            @property
            def _pre_style(self): return ''

        la.css(Fmt(style = style, cssclass = css_class).get_style_defs(),
               if_selectors = f'.{css_class}')

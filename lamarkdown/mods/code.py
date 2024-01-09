import lamarkdown as la
import re


def apply(fenced = True, inline = True,
          style = 'default', noclasses = False,
          css_class = 'la-code',
          **kwargs):

    style = kwargs.get('pygments_style', style)

    la('pymdownx.highlight',
        pygments_style = style,
        noclasses = noclasses,
        css_class = css_class,
        **kwargs)

    if fenced:
        la('pymdownx.superfences')

    if inline:
        la('pymdownx.inlinehilite')

    # Pygments adds the CSS declaration 'line-height: 125%', which (by experience) causes the
    # text lines on Firefox to bunch up and overlap unexpectedly. We try to remove this declaration.

    if noclasses:
        # Styles are inline. We search for 'line-height' within the <pre> tag itself.

        regex = re.compile(r'\bline-height:\s*[0-9]+%\s*;?\s*')

        def strip_line_height(element):
            style = regex.sub('', element.get('style'))
            if len(style) == 0:
                del element.attrib['style']
            else:
                element.set('style', style)

        la.with_selector(f'.{css_class} pre[style]', strip_line_height)

    else:
        # Styles are separated. We get Pygments to separately generate the CSS rules, but prevent it
        # generating 'line-height'.

        import pygments.formatters

        class Fmt(pygments.formatters.HtmlFormatter):
            @property
            def _pre_style(self):
                return ''  # Normally returns 'line-height: 125%;'

        la.css(Fmt(style = style, cssclass = css_class).get_style_defs(),
               if_selectors = f'.{css_class}')

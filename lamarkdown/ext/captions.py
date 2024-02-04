'''
# Captions Extension

Assigns captions to document elements, using the proper HTML elements intended for this purpose
(<figure>, <figcaption>, etc.). (The _appearance_ of such captions is governed by CSS, which is
beyond the scope of this extension.)

To caption an element:

1. Write the caption _before_ the element you are captioning, with a paragraph break in between.

2. Attach the '-caption' directive to the caption. (The 'attr_list' extension will be loaded
   automatically for this purpose.)


## Example

```
Some ordinary
document text.

A diagram for your
consideration.
{-caption}

![Important diagram](diagram.png)

Some more ordinary
document text.
```

This will result in the following HTML:
```
<p>Some ordinary document text.</p>

<figure>
<figcaption>A diagram for your consideration</figcaption>
<img alt="Important diagram" src="diagram.png">
</figure>

<p>Some more ordinary document text.</p>
```

## Tables

HTML <table> elements can have their own embedded <caption> elements. This extension will use this
mechanism instead if the captioned element is a table (e.g., as produced by the 'tables'
extension), although _not_ if a literal <table> element is embedded directly in the markdown.

(Due to the order of processing, directly-embedded HTML elements are not actually included in the
document at the time this extension is run.)
'''

from lamarkdown.lib.progress import Progress
from lamarkdown.lib.directives import Directives
import markdown
from xml.etree import ElementTree

NAME = 'la.captions'  # For error messages
CAPTION_DIRECTIVE = 'caption'


class CaptionsTreeProcessor(markdown.treeprocessors.Treeprocessor):

    def __init__(self,
                 md,
                 directives: Directives,
                 progress: Progress,
                 autowrap_listings: bool,
                 autowrap_maths: bool):
        super().__init__(md)
        self._directives = directives
        self._progress = progress
        self._autowrap_listings = autowrap_listings
        self._autowrap_maths = autowrap_maths

    def run(self, root):
        self._recurse(root)

    def _recurse(self, parent: ElementTree.Element):
        i = 0
        while i < (len(parent) - 1):  # Captions cannot be the last element
            element = parent[i]

            if self._directives.pop_bool(CAPTION_DIRECTIVE, element, NAME):
                caption_element = element
                del parent[i]

                # The 'figure element' comes straight after the caption element; but also has
                # index i because we just removed the latter.
                fig_element = parent[i]
                if self._directives.pop_bool(CAPTION_DIRECTIVE, fig_element, NAME):
                    self._progress.warning(
                        NAME,
                        msg = (f'"Do not apply "{self._directives.format(CAPTION_DIRECTIVE)}" to '
                               'the element being captioned, but only to the caption itself.'))

                if fig_element.tag in {'div', 'p'}:
                    # If we're captioning one of these elements, we just _convert_ it a figure, to
                    # avoid an unnecessary extra layer of wrapping.
                    fig_element.tag = 'figure'

                if fig_element.tag == 'figure':
                    # The element to be captioned is already a <figure> (including the case above)
                    caption_tag = 'figcaption'
                elif fig_element.tag == 'table':
                    # The element to be captioned is already a <table>
                    caption_tag = 'caption'
                else:
                    # The element to be captioned needs to be wrapped inside a <figure>
                    fig_element = self._wrap(fig_element, 'figure')
                    parent[i] = fig_element
                    caption_tag = 'figcaption'

                if (existing_caption_element := fig_element.find(f'./{caption_tag}')) is not None:
                    # Special case: if a caption element already exists, the least surprising
                    # thing we can do (probably) is just append to it.

                    existing_caption_element.append(caption_element)

                else:
                    # Normal case: no pre-existing caption element.

                    if caption_element.tag in {'div', 'p', 'blockquote'}:
                        caption_element.tag = caption_tag
                    else:
                        caption_element = self._wrap(caption_element, caption_tag)

                    fig_element.insert(0, caption_element)

                if text := fig_element.text:
                    fig_element.text = None
                    caption_element.tail = text + (caption_element.tail or '')

            else:
                def is_code(e):
                    return e.tag == 'pre' and len(e) <= 2 and e[-1].tag == 'code'

                auto_wrap = (
                    (self._autowrap_listings
                        and (is_code(element) or (element.tag == 'div'
                                                  and len(element) == 1
                                                  and is_code(element[0]))))
                    or (self._autowrap_maths
                        and element.tag == 'math' and element.get('display') == 'block'))

                if auto_wrap:
                    fig_element = ElementTree.Element('figure')
                    parent[i] = fig_element
                    fig_element.append(element)


            self._recurse(parent[i])  # This will never recurse into an actual caption element
            i += 1

        if len(parent) > 0 and self._directives.pop_bool(CAPTION_DIRECTIVE, parent[-1], NAME):
            self._progress.warning(
                NAME,
                msg = (f'Caption "{parent[-1].text}" has not been applied properly. Check that '
                       'the attribute list is associated with the caption\'s paragraph/block, '
                       'and that the element to be captioned appears after the caption.'))


    def _wrap(self, orig_element: ElementTree.Element, new_tag: str) -> ElementTree.Element:
        wrapper = ElementTree.Element(new_tag)
        wrapper.append(orig_element)
        for attr_name in ['id', 'class']:
            if attr_value := orig_element.get(attr_name):
                wrapper.set(attr_name, attr_value)
                del orig_element.attrib[attr_name]
        return wrapper



class CaptionsExtension(markdown.Extension):
    def __init__(self, **kwargs):
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass  # Use default defaults

        default_progress = p.progress if p else Progress()

        self.config = {
            'directives': [
                p.directives if p else Directives(default_progress),
                'An object that retrieves directives from document elements.'
            ],
            'progress': [
                default_progress,
                'An object accepting progress messages.'
            ],
            'autowrap_listings': [
                False,
                'Wrap all code listings (<pre> elements containing a <code> element) in a '
                '<figure> element, even where no caption is provided.'
            ],
            'autowrap_maths': [
                False,
                'Wrap all block MathML elements (<math display="block">...</math>) in a <figure> '
                'element, even where no caption is provided.'
            ]
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # Auto-load attr_list, since 'la.captions' can't really do anything without it.
        md.registerExtensions(['attr_list'], {})

        proc = CaptionsTreeProcessor(
            md,
            self.getConfig('directives'),
            self.getConfig('progress'),
            self.getConfig('autowrap_listings'),
            self.getConfig('autowrap_maths')
        )

        # Priority must be lower than attr_list (8) and higher than la.labels (6) (which itself
        # must also be higher than toc (5)).
        md.treeprocessors.register(proc, 'la-captions-tree', 7)


def makeExtension(**kwargs):
    return CaptionsExtension(**kwargs)

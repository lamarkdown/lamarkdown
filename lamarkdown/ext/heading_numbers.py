'''
# Heading Numbers Extension

The 'lamarkdown.ext.heading_numbers' extension inserts decimal "x.y.z"-style numbers before each
heading element in the document. These can be restricted in a couple of ways:

* The 'from_level' and 'to_level' config options (1--6) define the range of heading tiers to be
  numbered.

* Any heading with the class 'notnumbered' is ignored (e.g., '## My Heading {.notnumbered}').

The numbers are inserted before the 'toc' extension runs (if it is loaded), so that they also show
up in the table-of-contents.
'''

import markdown

import re
from xml.etree import ElementTree


class HeadingNumbersTreeProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md, from_level: int, to_level: int, sep: str):
        super().__init__(md)
        self.from_level = from_level
        self.to_level = to_level
        self.sep = sep
        self.tags = set(f'h{n}' for n in range(from_level, to_level + 1))

    def run(self, root):
        # A vector of the current heading number at each heading level.
        numbers = [0] * (self.to_level - self.from_level + 1)

        for element in root.iter():
            if element.tag in self.tags and 'notnumbered' not in element.get('class', default=''):
                level = int(element.tag[1:])
                index = level - self.from_level

                # Increment current level
                numbers[index] += 1

                # Reset all subsequent levels
                for i in range(index + 1, len(numbers)):
                    numbers[i] = 0

                # Add heading number element
                hnumber = ElementTree.Element('span', attrib = {'class': 'hnumber'})
                hnumber.text = '.'.join(str(n) for n in numbers[:index + 1])
                hnumber.tail = self.sep + element.text
                element.text = ''
                element.insert(0, hnumber)

        return root


class HeadingNumbersExtension(markdown.Extension):
    def __init__(self, **kwargs):
        self.config = {
            'from_level': [1, 'Highest-level heading to number.'],
            'to_level':   [6, 'Lowest-level heading to number.'],
            'sep':        ['\u2003', 'Separator string, inserted between the number and the original heading text.'],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        proc = HeadingNumbersTreeProcessor(
            md,
            from_level = self.getConfig('from_level'),
            to_level = self.getConfig('to_level'),
            sep = self.getConfig('sep'),
        )

        # Tight range of suitable priorities!
        # * We must run after 'attr_list' (priority 8) in order to query class="notnumbered".
        # * We must run before 'toc' (priority 5), to get numbers into the table-of-contents.

        md.treeprocessors.register(proc, 'lamarkdown.ext.heading_numbers', 7)



def makeExtension(**kwargs):
    return HeadingNumbersExtension(**kwargs)

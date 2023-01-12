import unittest

import markdown
from lamarkdown.ext import markers


class MarkersTestCase(unittest.TestCase):

    def run_markdown(self, markdown_text, **kwargs):
        md = markdown.Markdown(
            extensions = ['lamarkdown.ext.markers']
        )
        return md.convert(dedent(markdown_text).strip())


    # def test_date(self):
    #     html = self.run_markdown(
    #         r'''
    #         /{.alpha}
    # 
    #         1. First list element, shown as (a)
    #         2. Second list element, shown as (b)
    #         3. etc.
    # 
    #         /{.roman}
    # 
    #         1. First list element, shown as (i)
    #         2. Second list element, shown as (ii)
    #         3. etc.
    #         ''')
    # 
    #     self.assertRegex(
    #         html,
    #         fr'''(?x)
    #         <p>Sometext[ ]
    #         <span>
    #         {re.escape(str(datetime.date.today())).replace(' ', '[ ]')}
    #         </span>
    #         [ ]sometext</p>
    #         '''
    #     )

from markdown import *
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
from xml.etree import ElementTree

# This extension lets markdown authors write Python expressions, to be executed, within markdown 
# documents. The expressions are of the form the form $`...`. Each expression will be replaced with
# the result of its execution, converted to a string.
#
# Expressions are evaluated within the (combined) scope of any build files. Thus, from a $`...` 
# expression, you can refer to anything imported or defined in md_build.py, or any of the other 
# build files.
#
# Thus, if your build file contains 'from datetime import date', then the expression $`date.today`
# will cause the date of compilation to appear in the document at that point.
#
# If there is an error in the expression, the error message will instead appear in the document,
# highlighted in red.
#
# Warning: this has security implications. This extension should not be enabled if there is any 
# question about whether to trust the author of the markdown.


class EvalInlineProcessor(InlineProcessor):
    ERROR_STYLE = 'font-weight: bold; color: white; background: #800000;'
    
    def __init__(self, regex, md, env):
        super().__init__(regex, md)
        self.env = env
    
    def handleMatch(self, match, data):
        element = ElementTree.Element('span')
        try:
            element.text = str(eval(match.group(1), self.env))
        except Exception as e:
            element.text = str(e)
            element.attrib['style'] = self.ERROR_STYLE
        return element, match.start(0), match.end(0)


class EvalExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            'env': [{}, 'Environment in which to evaluate expressions'],
        }
        super().__init__(**kwargs)
        
    def extendMarkdown(self, md):
        md.registerExtension(self)
        proc = EvalInlineProcessor(r'\$`(.*?)`', md, self.getConfig('env'))
        
        # Note: the built-in "BacktickInlineProcessor" has a priority of 190, and we need to have 
        # a higher priority than that (or not use backticks).
        md.inlinePatterns.register(proc, 'eval', 200)

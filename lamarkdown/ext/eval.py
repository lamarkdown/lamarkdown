'''
# Eval Extension

This extension lets markdown authors write Python expressions, to be executed, within markdown
documents. The expressions are of the form the form $`...` (or $``...``, etc). Each expression will
be replaced with the result of its execution, converted to a string; e.g. $`1+1` will insert '2'
into the document.

Expressions are evaluated within the (combined) scope of any build files. Thus, from a $`...`
expression, you can refer to anything imported or defined in md_build.py, or any of the other
build files.

Thus, if your build file contains 'from datetime import date', then the expression
$`date.today()` will cause the date of compilation to appear in the document at that point.

If there is an error in the expression, the error message will instead appear in the document,
highlighted in red.

WARNING: **this has security implications!** This extension should not be enabled if there is any
question about whether to trust the author of the markdown.
'''

#from lamarkdown.lib.error import Error
from lamarkdown.lib.progress import Progress, ErrorMsg
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
import re
from xml.etree import ElementTree


class EvalInlineProcessor(InlineProcessor):
    def __init__(self, regex, md, env, progress):
        super().__init__(regex, md)
        self.env = env
        self.progress = progress

    def handleMatch(self, match, data):
        try:
            element = ElementTree.Element('span')
            element.text = str(eval(match.group('code'), self.env))
        except Exception as e:
            #element = Error.from_exception('eval', e, match.group('code')).to_element()
            #element = self.progress.error_from_exception('Eval', e, match.group('code')).as_dom_element()
            element = self.progress.error('Eval', str(e), match.group('code')).as_dom_element()

        return element, match.start(0), match.end(0)


class EvalExtension(Extension):
    def __init__(self, **kwargs):
        # Try to get the default environment (the set of names that the embedded snippet will
        # be able to reference) from the actual current build parameters. This will only work
        # if this extension is being used within the context of lamarkdown.
        #
        # But we do have a fallback on the off-chance that someone wants to use it elsewhere.
        p = None
        try:
            from lamarkdown.lib.build_params import BuildParams
            p = BuildParams.current
        except ModuleNotFoundError:
            pass
            
        self.config = {
            'env':       [dict(p.env) if p else {}, 'Environment in which to evaluate expressions'],
            'progress':  [p.progress  if p else Progress(), 'An object accepting progress messages.'],
            'start':     ['$', 'Character (or string) marking the start of an eval expression'],
            'end':       ['',  'Character (or string) marking the end of an eval expression'],
            'delimiter': ['`', 'Character (or string) enclosing an eval expression (after the start and before the end strings)'],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        start = re.escape(self.getConfig('start'))
        end   = re.escape(self.getConfig('end'))
        delim = re.escape(self.getConfig('delimiter'))

        proc = EvalInlineProcessor(f'{start}(?P<bt>{delim}+)(?P<code>.*?)(?P=bt){end}', md, 
                                   self.getConfig('env'), self.getConfig('progress'))

        # Note: the built-in "BacktickInlineProcessor" has a priority of 190, and we need to have
        # a higher priority than that (or not use backticks).
        md.inlinePatterns.register(proc, 'lamarkdown.eval', 200)


def makeExtension(**kwargs):
    return EvalExtension(**kwargs)

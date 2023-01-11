'''
# Eval Extension

This extension lets markdown authors insert computed values into documents, with inline expressions
of the form $`...` (or $``...``, etc). There are two approaches to doing this:

1.  Users can supply a dict of replacement values when this extension is loaded (the 'replace'
    config option). The extension will look up the text occurring in $`...` in the dict. If that
    text is a key in the dict, the whole expression is replaced by the corresponding dict value.

    By default (with no configuration), the replacement dict contains keys 'date' and 'datetime',
    allowing authors to write "$`date`" or "$`datetime`" to insert the current date, or date and
    time, into the document.

2.  The extension can also execute the contents of $`...` as raw Python code. This will only be done
    if (a) the 'allow_code' config option is True (by default it is False), and (b) if there is no
    matching key in the replacement dict.

    When executing code this way, the result will be converted to a string, which will replace the
    original expression in the output document. For instance, writing "$`1+1`" will insert "2" into
    the document.

    Such expressions are evaluated within the (combined) scope of any build files. Authors can
    refer to anything imported or defined in md_build.py, or any of the other build files. Thus,
    if your build file contains 'from x import y', then an expression could be "$`y()`" (assuming
    y is callable).

    If there is an error in the expression, the error message will instead appear in the document,
    highlighted in red.

    This approach has _security implications_! The `allow_code` option must not be enabled if there
    is any question about whether to trust the author of the markdown file.
'''

from lamarkdown.lib.progress import Progress, ErrorMsg
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
import re
from xml.etree import ElementTree

import datetime


DEFAULT_REPLACEMENTS = {
    'date':     str(datetime.date.today()),
    'datetime': str(datetime.datetime.now()),
}


class EvalInlineProcessor(InlineProcessor):
    def __init__(self, regex, md, progress, replace, allow_code, env):
        super().__init__(regex, md)
        self.progress = progress
        self.replace = replace
        self.allow_code = allow_code
        self.env = env

    def handleMatch(self, match, data):
        element = ElementTree.Element('span')
        code = match.group('code')
        code_stripped = code.strip()
        if code_stripped in self.replace:
            element.text = str(self.replace[code_stripped])

        elif self.allow_code:
            try:
                element.text = str(eval(code, self.env))
            except Exception as e:
                element = self.progress.error_from_exception('Eval', str(e), code).as_dom_element()

        else:
            element = self.progress.error(
                'Eval',
                f'Unrecognised label - no available replacement value. (Note: the eval extension\'s "allow_code" option is set to False, so the text will not be executed as code.)',
                code
            ).as_dom_element()

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
            'progress':   [p.progress  if p else Progress(), 'An object accepting progress messages.'],
            'replace':    [DEFAULT_REPLACEMENTS, 'A dict for looking up replacement values for labels encountered in $`...`.'],
            'allow_code': [False, 'Whether or not to execute raw Python code (if the text does not match any fixed replacements).'],
            'env':        [dict(p.env) if p else {}, 'Environment in which to evaluate expressions (if allow_code==True).'],
            'start':      ['$',   'Character (or string) marking the start of an eval expression'],
            'end':        ['',    'Character (or string) marking the end of an eval expression'],
            'delimiter':  ['`',   'Character (or string) enclosing an eval expression (after the start and before the end strings)'],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        start = re.escape(self.getConfig('start'))
        end   = re.escape(self.getConfig('end'))
        delim = re.escape(self.getConfig('delimiter'))

        proc = EvalInlineProcessor(
            f'{start}(?P<bt>{delim}+)(?P<code>.*?)(?P=bt){end}', md,
            progress = self.getConfig('progress'),
            replace = self.getConfig('replace'),
            allow_code = self.getConfig('allow_code'),
            env = self.getConfig('env'))

        # Note: the built-in "BacktickInlineProcessor" has a priority of 190, and we need to have
        # a higher priority than that (or not use backticks).
        md.inlinePatterns.register(proc, 'lamarkdown.eval', 200)


def makeExtension(**kwargs):
    return EvalExtension(**kwargs)

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
    if (a) the 'allow_exec' config option is True (by default it is False), and (b) if there is no
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

    This approach has _security implications_! The `allow_exec` option must not be enabled if there
    is any question about whether to trust the author of the markdown file.
'''

from .util import replacement_patterns

from lamarkdown.lib.progress import Progress, ErrorMsg
from markdown.extensions import Extension
import re
from xml.etree import ElementTree

import datetime

NAME = 'la.eval' # For error messages

DEFAULT_REPLACEMENTS = {
    'date':     str(datetime.date.today()),
    'datetime': str(datetime.datetime.now()),
}


EVAL_REGEX = rf'\$(?P<bt>`+)(?P<code>.*?)(?P=bt)'

class EvalReplacementProcessor(replacement_patterns.ReplacementPattern):
    def __init__(self, progress, replace, allow_exec, env):
        super().__init__(EVAL_REGEX)
        self.progress = progress
        self.replace = replace
        self.allow_exec = allow_exec
        self.env = env

    def handle_match(self, match):
        element = ElementTree.Element('span')
        code = match.group('code')
        code_stripped = code.strip()
        if code_stripped in self.replace:
            element.text = str(self.replace[code_stripped])

        elif self.allow_exec:
            try:
                element.text = str(eval(code, self.env))
            except Exception as e:
                element = self.progress.error(
                    NAME, exception = e, show_traceback = False, code = code).as_dom_element()

        else:
            element = self.progress.error(
                NAME,
                msg = f'Unrecognised label - no available replacement value. (Note: the eval extension\'s "allow_exec" option is set to False, so the text will not be executed as code.)',
                code = code
            ).as_dom_element()

        return element


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
            'progress': [
                p.progress  if p else Progress(),
                'An object accepting progress messages.'
            ],
            'replace': [
                DEFAULT_REPLACEMENTS,
                'A dict for looking up replacement values for labels encountered in $`...`.'
            ],
            'allow_exec': [
                p.allow_exec if p else False,
                'Whether or not to execute raw Python code (if the text does not match any fixed replacements).'
            ],
            'env': [
                dict(p.env) if p else {},
                'Environment in which to evaluate expressions (if allow_exec==True).'
            ],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        proc = EvalReplacementProcessor(
            progress = self.getConfig('progress'),
            replace = self.getConfig('replace'),
            allow_exec = self.getConfig('allow_exec'),
            env = self.getConfig('env'))

        replacement_patterns.init(md)
        md.replacement_patterns.register(proc, 'la-eval-replacement', 30)
        md.ESCAPED_CHARS.append('$')


def makeExtension(**kwargs):
    return EvalExtension(**kwargs)

from lamarkdown import *

# Based on https://github.com/richleland/pygments-css/blob/master/default.css

def sel(*classes):
    return [f'code .{x}' for x in classes]

# Operator, .Word, (not sure what .p is)
css_rule(
    sel('o', 'ow', 'p'),
    'color: red;'
)

# Comment, Comment.Hashbang, Comment.Multiline, Comment.PreprocFile, Comment.Single, Comment.Special, Comment.Preproc
css_rule(
    sel('c', 'ch', 'cm', 'cpf', 'c1', 'cs', 'cp'),
    'color: #c06000; font-style: italic;'
)

# Keyword, Keyword.Constant, .Declaration, .Namespace, .Pseudo, .Reserved, .Type
css_rule(
    sel('k', 'kc', 'kd', 'kn', 'kp', 'kr', 'kt'),
    'color: blue; font-weight: bold;'
)

# Literal.Number, Number.Bin, .Float, .Hex, .Integer, .Oct, Literal.Number.Integer.Long
css_rule(
    sel('m', 'mb', 'mf', 'mh', 'mi', 'mo', 'il'),
    'color: #008080;'
)

# Literal.String, .Affix, .Backtick, .Char, .Delimiter, .Doc, .Double, .Escape, .Heredoc, .Interpol, .Other, .Regex, .Single, .Symbol
css_rule(
    sel('s', 'sa', 'sb', 'sc', 'dl', 'sd', 's2', 'se', 'sh', 'si', 'sx', 'sr', 's1', 'ss'),
    'color: green;'
)

# Name.Attribute, .Builtin, .Class, .Constant, .Decorator, .Entity, .Exception, .Function, .Label, .Namespace, .Tag, .Variable, Name.Builtin.Pseudo, Name.Function.Magic, .Name.Variable.Class, Name.Variable.Global, Name.Variable.Instance, Name.Variable.Magic
css_rule(
    sel('na', 'nb', 'nc', 'no', 'nd', 'ni', 'ne', 'nf', 'nl', 'nn', 'nt', 'nv', 'bp', 'fm', 'vc', 'vg', 'vi', 'vm'),
    'color: black;'
)

# Text.Whitespace
css_rule('w', 'color: #bbbbbb')

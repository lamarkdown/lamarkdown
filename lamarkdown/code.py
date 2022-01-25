from lamarkdown import *

# Based on https://github.com/richleland/pygments-css/blob/master/default.css
css(r'''
    /*
    code .hll { background-color: #ffffcc }
    code  { background: #f8f8f8; }
    code .err { border: 1px solid #FF0000 }             /* Error * /
    code .gd { color: #A00000 }                         /* Generic.Deleted * /
    code .ge { font-style: italic }                     /* Generic.Emph * /
    code .gr { color: #FF0000 }                         /* Generic.Error * /
    code .gh { color: #000080; font-weight: bold }      /* Generic.Heading * /
    code .gi { color: #00A000 }                         /* Generic.Inserted * /
    code .go { color: #888888 }                         /* Generic.Output * /
    code .gp { color: #000080; font-weight: bold }      /* Generic.Prompt * /
    code .gs { font-weight: bold }                      /* Generic.Strong * /
    code .gu { color: #800080; font-weight: bold }      /* Generic.Subheading * /
    code .gt { color: #0044DD }                         /* Generic.Traceback * /
    */

    /* Operator, .Word, (not sure what .p is) */
    code .o, code .ow, code .p { color: red; }

    /* Comment, Comment.Hashbang, Comment.Multiline, Comment.PreprocFile, Comment.Single, Comment.Special, Comment.Preproc */
    code .c, .ch, code .cm, code .cpf, code .c1, code .cs, code .cp { color: #c06000; font-style: italic }

    /* Keyword, Keyword.Constant, .Declaration, .Namespace, .Pseudo, .Reserved, .Type */
    code .k, .kc, code .kd, code .kn, code .kp, code .kr, code .kt { color: blue; font-weight: bold }

    /* Literal.Number, Number.Bin, .Float, .Hex, .Integer, .Oct, Literal.Number.Integer.Long */
    code .m, code .mb, code .mf, code .mh, code .mi, code .mo, code .il { color: #008080; }

    /* Literal.String, .Affix, .Backtick, .Char, .Delimiter, .Doc, .Double, .Escape, .Heredoc, .Interpol, .Other, .Regex, .Single, .Symbol */
    code .s, code .sa , code .sb , code .sc , code .dl , code .sd , code .s2 , code .se , code .sh , code .si , code .sx , code .sr , code .s1 , code .ss { color: green; }

    /* Name.Attribute, .Builtin, .Class, .Constant, .Decorator, .Entity, .Exception, .Function, .Label, .Namespace, .Tag, .Variable, Name.Builtin.Pseudo, Name.Function.Magic, .Name.Variable.Class, Name.Variable.Global, Name.Variable.Instance, Name.Variable.Magic */
    code .na, code .nb, code .nc, code .no, code .nd, code .ni, code .ne, code .nf, code .nl, code .nn, code .nt, code .nv, code .bp, code .fm, code .vc, code .vg, code .vi, code .vm { color: black; }

    /* Text.Whitespace */
    code .w { color: #bbbbbb }
''')

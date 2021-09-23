from lib import eval
from lib import latex

import markdown 
import pymdownx


def md_init(buildParams):
    buildParams.extensions = [
        # Built-in
        'admonition', # 'Notes', 'warnings', etc.
        'meta',       # Allows for defining metadata in the markdown.
        'smarty',     # Auto-replacement of quotes, ellipses and dashes.
        'attr_list',
        
        # 3rd Party: pymdown
        'pymdownx.extra',
        
        # 3rd Party: custom blocks
        # https://pypi.org/project/markdown-customblocks/
        #'customblocks',

        # Custom
        latex.TikzExtension(build_dir=buildParams.build_dir),
        
        eval.EvalExtension(env=buildParams.env),
    ]


# Based on https://github.com/richleland/pygments-css/blob/master/default.css
codeCss = r'''
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
'''


md_css = r'''
    @import url('https://fonts.googleapis.com/css2?family=Merriweather&family=Merriweather+Sans&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@500&family=Merriweather&family=Merriweather+Sans&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,700;1,400;1,700&display=swap');

    @media screen {
        html { background: #404040; }
        /*body {
            background: 
        }*/
    }

    html {
        font-family: 'Open Sans', sans-serif;
        line-height: 1.8em;
        /*background: #404040;*/
    }

    body {
        background: white;
        max-width: 50em;
        margin-left: auto;
        margin-right: auto;
        padding: 4em;
        
        counter-reset: section;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Merriweather', serif;
    }

    h2, h3, h4, h5, h6 {
        margin-top: 1.5em;
    }

    h2:not(.notnumbered) {
        counter-reset: subsection;
        counter-increment: section;
    }

    h2:not(.notnumbered)::before {
        content: counter(section);
        margin-right: 1em;
    }

    h3:not(.notnumbered) {
        counter-reset: subsubsection;
        counter-increment: subsection;
    }

    h3:not(.notnumbered)::before {
        content: counter(section) "." counter(subsection);
        margin-right: 1em;
    }

    h4:not(.notnumbered) {
        counter-increment: subsubsection;
    }

    h4:not(.notnumbered)::before {
        content: counter(section) "." counter(subsection) "." counter(subsubsection);
        margin-right: 1em;
    }


    /* Code */

    pre {
        line-height: 1.7em;    
    }

    code {
        font-family: 'Inconsolata', monospace;
    }

    .unixcmd::before, .wincmd::before, [prompt]::before, .unixcmd br+::before, .wincmd br+::before, [prompt] br+::before {
        font-family: 'Inconsolata', monospace;
        color: #808080;    
    }

    .unixcmd::before, .unixcmd br+::before {
        content: "[user@pc]$ ";
    }

    .wincmd::before, wincmd br+::before {
        content: "C:\\> ";
    }

    [prompt]::before, [prompt] br+::before {
        content: attr(prompt) " ";
    }


    /* Boxes */

    .admonition {
        border-radius: 5px;
        border: 1px solid #606060;
        padding: 0 1em;
        margin: 1ex 0;
    }

    .admonition-title {
        font-weight: bold;
        font-family: 'Merriweather Sans', sans-serif;
    }

    .admonition.note {
        border: 1px solid #0060c0;
        background: #c0d8ff;
    }

    .admonition.warning {
        border: 1px solid #c03030;
        background: #ffc0c0;
    }

    .admonition.answer {
        border: 1px solid #c000c0;
        background: #ffe0ff;
    }


    /* Lists */

    ul > li::marker {
        color: #0080ff;
        content: '\25A0\00A0';
    }

    ul ul > li::marker {
        color: #80c0ff;
        content: '\25B8\00A0';
    }

    ol {
        width: 100%;
        counter-reset: listitem;
        padding: 0;
    }

    ol > li {
        display: table;
        counter-increment: listitem;
    }

    ol > li::before {
        content: counters(listitem, ".") ". ";
        display: table-cell;
        width: 2ex;
        padding-right: 0.5em;
        color: #ff6000;
        font-weight: bold;
    }

    ol ol > li::before {
        width: 3ex;
    }

    ol ol ol > li::before {
        width: 4ex;
    }

    .alpha + ol > li::before {
        content: "(" counter(listitem, lower-alpha) ") ";
    }

    .roman + ol > li::before {
        content: "(" counter(listitem, lower-roman) ") ";
    }

    li {
        margin: 0.5em 0 0.5em 0;
        padding-left: 0.5em;
        padding-top: 0em;
        width: calc(100% - 1ex);
    }


    ol > li > p:first-child {
        /* It seems that, without 'display: table', the <p> child elements of adjacent <li> elements will share their vertical margins, whereas 'display: table' causes those margins to exist separately. Thus, we want to set the bottom margin to zero to avoid too much vertical space. */
        margin-top: 0;
    }

    ol > li > :last-child {
        margin-bottom: 0;
    }


    /* Tables */
    table {
        border-collapse: collapse;
        border-bottom: 1px solid black;
    }

    table thead tr {
        background-color: #ffc080;
        border-top: 1px solid black;
        border-bottom: 1px solid black;
    }

    td, th {
        padding: 0.5em 1em;
    }

    tbody tr:nth-child(odd) {
        background-color: white;
    }

    tbody tr:nth-child(even) {
        background-color: #fff0e0;
    }


    /* Mark Counts */

    [nmarks]:not([nmarks="1"])::after {
        content: "[" attr(nmarks) " marks]";
    }

    [nmarks="1"]::after {
        content: "[1 mark]";
    }

    [nmarks]::after {
        display: block;
        text-align: right;
        font-weight: bold;
        position: relative;
    }

    .inline {
        position: relative;
    }

    .inline[nmarks]::after {
        position: absolute;
        right: 0pt;
        bottom: 0pt;
    }

'''

md_css += codeCss

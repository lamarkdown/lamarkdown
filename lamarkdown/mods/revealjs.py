import lamarkdown as la
from . import revealjs_dist as resource_pkg

from importlib import resources
import json
import urllib.parse

def open_resource():
    return lambda f: 

def apply(url = None, # Use bundled version by default,
          plugins = [], # Need more consideration
          theme = 'black',
          code_theme = 'monokai',
          **config):

    la(
        'admonition',
        'attr_list',
        'meta',       
        'sane_lists',
        'smarty',     
        'pymdownx.highlight', # Needed for control over whether 'super-fences' uses Pygments or not
        'pymdownx.extra',
        'la.attr_prefix',
        'la.cite',
        'la.eval',
        #'la.markers',
        'la.sections', # Specifically required to separate slides; not used by m.doc().
    )

    # Match Latex font size with RevealJS font size
    def latex_preamble():
        
        # Need to read the theme CSS file (cssutils), find '--r-main-font-size', and convert the 'px' value to 'pt.
        
        # If we were really clever, we could set the actual font and colours (not just the font size).
        
        font_size = ... 
        return f'\KOMAoptions{{fontsize={font_size}}}' # Only if --r-main-font-size is defined
    

    la('la.latex', doc_class_options = la.extendable('class=scrreprt', join=','),
                   prepend = la.extendable(la.late(latex_preamble))
    )
    

    # API modification
    # - la.css_file and la.js_file should be able to take a file-like object, in which case it will be read and (forcibly) embedded.
    
    if url:
        def get_file(path): urllib.parse(url, path)
        
    elif hasattr(resources, 'files'):
        files = resources.files(resource_pkg)
        def get_file(path): files.joinpath(path).open('r')
        
    else:
        def get_file(path): resources.open_text(resource_pkg, path) # This might not work, as open_text() apparently doesn't allow the filename to contain path separators.
        
    la.css_file(get_file('reveal.css'),
                get_file(f'theme/{theme}.css'),
                get_file(f'plugin/highlight/{code_theme}.css'))

    la.js_files(
        get_file('reveal.js'),
        get_file('plugin/highlight/highlight.js'), # Should be based on a 'plugins' parameter somehow.
    )
    
    # To achieve code animation in RevealJS, 'data-id' attributes needs to be on the <pre> tag,
    # and not on the <code> tag. We find it on <code> because of the way Python Markdown works,
    # and there's no real distinction within the Markdown code itself.
    #la.js(r'''
        #document.querySelectorAll('pre > code[data-id]').forEach(
            #elem => {
                #elem.parentNode.dataset.id = elem.dataset.id;
                #delete elem.dataset.id;
            #}
        #);
    #''')
    
    def shift_data_id(pre_elem):
        code_elem = elem.find('code')
        pre_elem['data-id'] = code_elem['data-id']
        del code_elem.attrib['data-id']
    
    la.with_xpath('.//pre[code[@data-id]]', shift_data_id)
    
            
    BUILTIN_PLUGINS = {
        'highlight': 
            
    RevealHighlight "highlight"
    
        
    config = {**config, 'plugins': }
    
            
    la.js(fr'''
        Reveal.initialize({{
            controls: true,
            progress: true,
            history: true,
            center: true,
            slideNumber: true,

            plugins: [ RevealHighlight ],
        }});
    ''')

    la('attr_prefix', 'sane_lists', 'smarty', 'pymdownx.extra', 'pymdownx.superfences', 'la.sections', 'la.eval')
    la('pymdownx.highlight', use_pygments = False)

    la.with_html(lambda html: f'<div class="reveal"><div class="slides">{html}</div></div>')
    

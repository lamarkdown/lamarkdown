from .build_params import BuildParams
from . import resources

import io
import re


NAME = 'lists' # Progress/error messages

LABEL_DIRECTIVE = ':label'
CLASS_PREFIX = 'la-list-'

ABBREVIATIONS = {
    '1': 'decimal',
    'a': 'lower-alpha',
    'A': 'upper-alpha',
    'i': 'lower-roman',
    'I': 'upper-roman',
}

STYLE_NAME_RE = re.compile('[A-Za-z0-9-]+')

def label_lists(root_element, build_params: BuildParams):
    generated_styles = {}
    style_n = 0

    for element in root_element.iter():
        if element.tag in ['ol', 'ul'] and LABEL_DIRECTIVE in element.attrib:

            spec = element.get(LABEL_DIRECTIVE)
            del element.attrib[LABEL_DIRECTIVE]

            buf = None
            label_parts = []
            while len(spec) > 0:
                match = STYLE_NAME_RE.match(spec)
                if match:
                    if buf is not None:
                        label_parts.append(_as_css_str(buf.getvalue()))
                        buf = None

                    symbol = match.group(0)
                    label_parts.append(f'counter(list-item, {ABBREVIATIONS.get(symbol, symbol)})')
                    spec = spec[match.end(0):]

                else:
                    if buf is None:
                        buf = io.StringIO()

                    if spec[0] in ['"', "'"]:
                        quote = spec[0]
                        end_index = spec.find(quote, 1)
                        if end_index == -1:
                            buf.write(spec[1:])
                            spec = ''
                            break
                        else:
                            buf.write(spec[1:end_index])
                            spec = spec[end_index + 1:]

                            # Two quotes in a row means one literal quote, and the string continues
                            while spec.startswith(quote):
                                end_index = spec.find(quote, 1)
                                if end_index == -1:
                                    buf.write(spec) # Include quote this time
                                    spec = ''
                                    break
                                buf.write(spec[:end_index])
                                spec = spec[end_index + 1:]

                    else:
                        buf.write(spec[0])
                        spec = spec[1:]

            if buf is not None:
                label_parts.append(_as_css_str(buf.getvalue()))
            label = ' '.join(label_parts)

            if label in generated_styles:
                class_name = CLASS_PREFIX + str(generated_styles[label])

            else:
                style_n += 1
                generated_styles[label] = style_n
                class_name = CLASS_PREFIX + str(style_n)

            if 'class' in element.attrib:
                element.set('class', f'{element.get("class")} {class_name}')

            else:
                element.set('class', class_name)

            css = rf'''
                .{class_name} > li {{
                    --la-list-label: {label};
                }}
            '''

            build_params.css.append(resources.ContentResourceSpec(
                xpaths_required = [],
                content_factory = _as_factory(css)
            ))


def _as_factory(string):
    return lambda *_: string


def _as_css_str(string):
    string = string.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{string}"'

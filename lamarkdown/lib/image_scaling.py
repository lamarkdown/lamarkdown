from .build_params import BuildParams

import cssutils

import re
import xml.dom
from xml.etree import ElementTree


def scale_images(root_element, build_params: BuildParams):
    css_parser = cssutils.CSSParser()
    for element in root_element.iter():
        if element.tag == 'svg':
            _rescale_svg(element, css_parser, build_params)

        elif element.tag == 'img':
            # TODO: if <img> has its width or height specified explicitly, we can scale it
            # in the same way as <svg>. Otherwise, we'll need to fetch the image content and
            # examine the intrinsic width/height.
            pass

        elif element.tag == 'source':
            # TODO: we can probably just treat this like <img>, its mime type is image/* (based
            # first on the type= attribute, falling back to the URL).
            pass


def _rescale_svg(element,
                 css_parser: cssutils.CSSParser,
                 build_params: BuildParams):
    progress = build_params.progress

    if 'scale' in element.attrib:
        try:
            local_scale = float(element.get('scale'))
        except ValueError:
            progress.warning('la.scale', f'Non-numeric value "{element.get("scale")}" given as a scaling factor')
            return
        del element.attrib['scale']
    else:
        local_scale = 1.0

    scale = local_scale * build_params.scale_rule(type = 'image/svg+xml',
                                                  tag = 'svg',
                                                  attr = element.attrib)

    if scale != 1.0:
        # We find CSS width and/or height properties, and HTML width and/or height
        # attributes, and multiply each one by 'scale'.
        #
        # Units are irrelevant, except that we abort if _any_ of the widths or heights:
        # (a) Are percentages of a containing box, in which case we assume that this is the intended
        #     final size and should be left as-is; OR
        #
        # (b) Are not literal CSS dimensions. We can scale '5em' or '4px', for instance, but
        #     not 'var(--xyz)' nor 'calc(5em + 4px)'.
        #
        # (And we can't scale one dimension without the other, since that would upset the
        # aspect ratio.)
        #
        # The browser can figure out the correct size based on width _or_ height, from
        # either the CSS style (for preference) _or_ tag attributes.
        #
        # FYI: the <svg> element's 'viewBox' attribute is irrelevant too. It only defines
        # the bounding box in terms of the picture's internal coordinates. (We could use it
        # to identify the aspect ratio, if we wanted to, but we don't need that for simple
        # linear scaling.)

        new_style = None
        new_width = None
        new_height = None

        if 'style' in element.attrib:
            try:
                style_decls = css_parser.parseStyle(element.get('style'))
            except xml.dom.SyntaxErr:
                self.progress.warning('la.scale', f'Syntax error in style attribute for <{element.tag}> element: "{element.get("style")}"')
            else:
                if 'width' in style_decls:
                    spec = style_decls.getProperty('width').propertyValue[0]
                    if not _scalable(spec): return
                    spec.value *= scale

                if 'height' in style_decls:
                    spec = style_decls.getProperty('height').propertyValue[0]
                    if not _scalable(spec): return
                    spec.value *= scale

            if 'width' in style_decls or 'height' in style_decls:
                new_style = style_decls.cssText

        spec = _length_value(element, 'width')
        if spec:
            if not _scalable(spec): return
            spec.value *= scale
            new_width = spec.cssText

        spec = _length_value(element, 'height')
        if spec:
            if not _scalable(spec): return
            spec.value *= scale
            new_height = spec.cssText

        if new_style:  element.set('style',  new_style)
        if new_width:  element.set('width',  new_width)
        if new_height: element.set('height', new_height)


# These are the length units that will cause scaling to abort; they are specifically those units
# relative to some containing box or other. (Units relative to the font size, such as 'em' or 'ch',
# don't seem to pose a challenge for scalability, so they aren't included here.)
#
_RELATIVE_UNITS = {'%', 'vw', 'vh', 'vmin', 'vmax', 'vb', 'vi',
                   'svw', 'svh', 'lvw', 'lvh', 'dvw', 'dvh'}

def _scalable(obj) -> bool:
    return (
        isinstance(obj, cssutils.css.DimensionValue)
        and (obj.dimension is None or
             obj.dimension.lower() not in _RELATIVE_UNITS)
    )


def _length_value(element, key: str):
    if key not in element.attrib:
        return None
    try:
        return cssutils.css.value.DimensionValue(element.get(key))
    except xml.dom.SyntaxErr:
        self.progress.warning('la.scale', f'Syntax error in {key} attribute for <{element.tag}> element: "{element.get(key)}"')
        return None

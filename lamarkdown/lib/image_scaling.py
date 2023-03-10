from .build_params import BuildParams
from . import resources

import cssutils
import PIL.Image

import io
import re
import xml.dom
from xml.etree import ElementTree


def scale_images(root_element, build_params: BuildParams):
    progress = build_params.progress
    css_parser = cssutils.CSSParser()
    for element in root_element.iter():
        if element.tag in ['svg', 'img', 'source']:

            content = None
            type = None
            if element.tag == 'svg':
                type = 'image/svg+xml'

            elif element.tag in ['img', 'source']:
                if 'src' in element.attrib:
                    try:
                        _, content, type = resources.read_url(element.get('src'),
                                                              build_params.fetch_cache,
                                                              progress)
                    except Exception as e:
                        progress.error_from_exception('scaling', e)
                        continue

                else:
                    progress.warning('scaling', f'<{element.tag}> element missing src attribue')

            else:
                raise AssertionError

            scale = _calc_scale(element, type, build_params)
            if scale != 1.0:
                _rescale_element(element, scale, content, type, css_parser, progress)


def _calc_scale(element, type, build_params) -> bool:

    if 'scale' in element.attrib:
        try:
            local_scale = float(element.get('scale'))
        except ValueError:
            progress.warning('scaling', f'Non-numeric value "{element.get("scale")}" given as a scaling factor')
            return 1.0 # Don't scale
        del element.attrib['scale']
    else:
        local_scale = 1.0

    if 'abs-scale' in element.attrib:
        del element.attrib['abs-scale']
        return local_scale

    else:
        return local_scale * build_params.scale_rule(type = type,
                                                     tag = element.tag,
                                                     attr = element.attrib)


def _rescale_element(element,
                     scale: float,
                     content: bytes,
                     type: str,
                     css_parser: cssutils.CSSParser,
                     build_params: BuildParams):
    #
    # 1. Try scaling based directly on the element's width/height CSS properties or HTML attributes.
    #    This is format agnostic. Scale whichever width(s)/height(s) are found.
    #
    #    If any widths/heights were present, then we're done. The browser needs only one of them to
    #    correctly scale the image. (If any are present but "unscalable", then nothing is scaled.)
    #
    #    Otherwise, if no widths/heights were present...
    #
    # 2. For <img> elements, extract the src URL.
    #    (a) If src= points to an SVG image, extract the width/height in a manner similar to (1).
    #    (b) If src= points to a raster image, use Pillow to extract the width/height.
    #
    #    In either case, add scaled width/height attributes to the original <img> element. (The src
    #    attribute and its contents are left unchanged.)
    #
    #
    # Units
    # -----
    #
    # In (1), we only deal in units of absolute length (e.g., 'px', 'mm'), not units relative to
    # font sizes (e.g., 'em') or bounding boxes (e.g., '%', 'vh'), or expressions (e.g., 'var(--x)',
    # 'calc(5em + 4px)'). We assume non-absolute units are intended to be the 'final say', and no
    # further scaling should be done.
    #
    # Given that absolute units have been used, they are left unmodified. Conversion is possible but
    # unnecessary, as the multiplication works equally well in any units.
    #
    # +------------------------------------------------------------------------------------------+
    # | Aside: technically, units aren't always allowed at all:                                  |
    # |                                                                                          |
    # |                               | <svg>         | <img> / <source>                         |
    # | ------------------------------+---------------+-------------------------------           |
    # |  width/height HTML attributes | units allowed | *unitless* (implicitly 'px')             |
    # |  width/height CSS properties  | units allowed | units allowed                            |
    # |                                                                                          |
    # | However, for simplicity, if units do occur where technically not allowed, they are       |
    # | preserved as if they were. (This module is just scaling things, not policing standards.) |
    # +------------------------------------------------------------------------------------------+
    #
    # In (2)(a), we convert all (absolute) units to pixel-based units for the <img>/<source>
    # element.
    #
    # In (2)(b), units are inherently pixel-based. We assume that browsers will render an X??Y
    # image at the same size, by default, as when explicitly sized withwidth="<X>px" and/or
    # height="<Y>px". (No need to assume that 1px == one physical pixel, and it probably isn't for
    # certain media, particularly print.)
    #
    #
    # FYI: SVG's viewBox attribute
    # --------------------------
    #
    # This is irrelevant. It only defines the bounding box in terms of the picture's internal
    # coordinates. (We could use it to identify the aspect ratio, if we wanted to, but we don't need
    # that for simple linear scaling.)
    #

    new_style = None
    new_width = None
    new_height = None

    if 'style' in element.attrib:
        try:
            style_decls = css_parser.parseStyle(element.get('style'))
        except xml.dom.SyntaxErr:
            build_params.progress.warning(
                'scaling',
                f'Syntax error in style attribute for <{element.tag}> element: "{element.get("style")}"')
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

    if new_style or new_width or new_height:
        # Scaling all done!
        return

    if element.tag not in ['img', 'source'] or 'src' not in element.attrib:
        build_params.progress.warning(
            'scaling', f'Cannot identify image dimensions')
        return


    if type == 'image/svg+xml':
        svg_root = ElementTree.fromstring(content.decode())

        width = None
        height = None

        if 'style' in svg_root.attrib:
            try:
                style_decls = css_parser.parseStyle(svg_root.get('style'))
            except xml.dom.SyntaxErr:
                build_params.progress.warning(
                    'scaling',
                    f'Syntax error in style attribute for <{svg_root.tag}> element: "{svg_root.get("style")}"')
            else:
                if 'width' in style_decls:
                    spec = style_decls.getProperty('width').propertyValue[0]
                    if not _scalable(spec): return
                    width = _as_pixel_value(spec, scale)

                if 'height' in style_decls:
                    spec = style_decls.getProperty('height').propertyValue[0]
                    if not _scalable(spec): return
                    height = _as_pixel_value(spec, scale)

        spec = _length_value(svg_root, 'width')
        if spec:
            if not _scalable(spec): return
            if width is None:
                width = _as_pixel_value(spec, scale)

        spec = _length_value(svg_root, 'height')
        if spec:
            if not _scalable(spec): return
            if height is None:
                height = _as_pixel_value(spec, scale)

        if width is not None:
            element.set('width', width)

        if height is not None:
            element.set('height', height)

    else: # Raster image
        try:
            with PIL.Image.open(io.BytesIO(content)) as image:
                element.set('width', f'{image.width * scale}')
                element.set('height', f'{image.height * scale}')

        except PIL.UnidentifiedImageError as e:
            self.progress.warning('scaling', f'Image format unrecognised: {str(s)}')


ABSOLUTE_UNITS = {
    'cm': 96.0 / 2.54,       # ??? 37.8
    'mm': 96.0 / 25.4,       # ??? 3.78
    'q':  96.0 / 25.4 / 4.0, # ??? 0.945
    'in': 96.0,              # = 96
    'pc': 96.0 / 6.0,        # = 16
    'pt': 96.0 / 72.0,       # ??? 1.33
    'px': 1.0,               # = 1
}

def _scalable(obj) -> bool:
    return (
        isinstance(obj, cssutils.css.DimensionValue)
        and (obj.dimension is None or
             obj.dimension.lower() in ABSOLUTE_UNITS)
    )

def _as_pixel_value(dimension, scale):
    assert isinstance(dimension, cssutils.css.DimensionValue)
    return str(dimension.value * ABSOLUTE_UNITS[dimension.dimension or 'px'] * scale)


def _length_value(element, key: str):
    if key not in element.attrib:
        return None
    try:
        return cssutils.css.value.DimensionValue(element.get(key))
    except xml.dom.SyntaxErr:
        self.progress.warning('scaling', f'Syntax error in {key} attribute for <{element.tag}> element: "{element.get(key)}"')
        return None

from ..util.mock_progress import MockProgress
from lamarkdown.lib import image_scaling

import unittest
from unittest.mock import Mock, PropertyMock

import io
import re
from textwrap import dedent
from xml.etree import ElementTree

class ImageScalingTestCase(unittest.TestCase):

    def test_rescale_svg(self):

        mock_build_params = Mock()

        # Mock scaling rule: scale <svg> elements by 2.5 iff they have an 'x=...' attribute
        # (or 1.0 if they don't).
        type(mock_build_params).scale_rule = \
            lambda self, attr = {}, **k: 2.5 if 'x' in attr else 1.0

        # Test input shorthands
        # ---------------------

        # Misc
        x = {'x': 'dummy'} # Arbitrary attribute that invokes the scale rule
        sc = {'scale': '0.1'}

        # Main test input shorthands
        w_10       = {'width': '10'}
        h_20       = {'height': '20pt'}
        s_w30      = {'style': 'width: 30px'}
        s_h40      = {'style': 'height: 40em'}
        s_w30_h40  = {'style': 'width: 30px; height: 40em'}

        # Relative-unit test input shorthands
        w_RR       = {'width': '10vw'}
        h_RR       = {'height': '20vh'}
        s_wRR      = {'style': 'width: 30vmax'}
        s_hRR      = {'style': 'height: 40vmin'}
        s_wRR_hRR  = {'style': 'width: 30%; height: 40%'}


        # Expected result shorthands
        # --------------------------

        # Results when scaled by 2.5 (as per scale_rule())
        w_25       = {'width': '25'}
        h_50       = {'height': '50pt'}
        s_w75      = {'style': 'width: 75px'}
        s_h100     = {'style': 'height: 100em'}
        s_w75_h100 = {'style': 'width: 75px; height: 100em'}

        # Results when scaled by 0.1 (as per the scale=... attribute)
        w_1        = {'width': '1'}
        h_2        = {'height': '2pt'}
        s_w3       = {'style': 'width: 3px'}
        s_h4       = {'style': 'height: 4em'}
        s_w3_h4    = {'style': 'width: 3px; height: 4em'}

        # Results when scaled by 0.25 (combined)
        w_2p5      = {'width': '2.5'}
        h_5        = {'height': '5pt'}
        s_w7p5     = {'style': 'width: 7.5px'}
        s_h10      = {'style': 'height: 10em'}
        s_w7p5_h10 = {'style': 'width: 7.5px; height: 10em'}


        # Regex to allow us to strip out any whitespace and trailing post-decimal zeros from the
        # actual result, so we can then do simple string comparisons rather than parsing the values.
        WHITESPACE = re.compile('\s+')
        TRAILING_ZEROS = re.compile(r'(\.[0-9]*?)0+\b')
        TRAILING_ZERO_REPL = r'\1'

        for inp_attr, exp_attr in [
            # Without the criteria that invokes the scaling rule (well, technically it's always
            # invoked, but here it returns 1.0), and without a 'scale' attribute, no scaling should
            # happen. ('...' refers to the test input.)
            ({},                            ...),
            ({**w_10},                      ...),
            ({**h_20},                      ...),
            ({**w_10, **h_20},              ...),
            ({**s_w30},                     ...),
            ({**w_10, **s_w30},             ...),
            ({**h_20, **s_w30},             ...),
            ({**w_10, **h_20, **s_w30},     ...),
            ({**s_h40},                     ...),
            ({**w_10, **s_h40},             ...),
            ({**h_20, **s_h40},             ...),
            ({**w_10, **h_20, **s_h40},     ...),
            ({**s_w30_h40},                 ...),
            ({**w_10, **s_w30_h40},         ...),
            ({**h_20, **s_w30_h40},         ...),
            ({**w_10, **h_20, **s_w30_h40}, ...),

            # Given a criteria that invokes the scaling rule (for a scaling factor of 2.5), check
            # that the scale is applied to all width/height combinations.
            ({**x},                              {**x}),
            ({**x, **w_10},                      {**x, **w_25}),
            ({**x, **h_20},                      {**x, **h_50}),
            ({**x, **w_10, **h_20},              {**x, **w_25, **h_50}),
            ({**x, **s_w30},                     {**x, **s_w75}),
            ({**x, **w_10, **s_w30},             {**x, **w_25, **s_w75}),
            ({**x, **h_20, **s_w30},             {**x, **h_50, **s_w75}),
            ({**x, **w_10, **h_20, **s_w30},     {**x, **w_25, **h_50, **s_w75}),
            ({**x, **s_h40},                     {**x, **s_h100}),
            ({**x, **w_10, **s_h40},             {**x, **w_25, **s_h100}),
            ({**x, **h_20, **s_h40},             {**x, **h_50, **s_h100}),
            ({**x, **w_10, **h_20, **s_h40},     {**x, **w_25, **h_50, **s_h100}),
            ({**x, **s_w30_h40},                 {**x, **s_w75_h100}),
            ({**x, **w_10, **s_w30_h40},         {**x, **w_25, **s_w75_h100}),
            ({**x, **h_20, **s_w30_h40},         {**x, **h_50, **s_w75_h100}),
            ({**x, **w_10, **h_20, **s_w30_h40}, {**x, **w_25, **h_50, **s_w75_h100}),

            # Given a scale=0.1 attribute, check that the scale is applied to all width/height
            # combinations. (Also, the scale= attribute must be removed.)
            ({**sc},                              {}),
            ({**sc, **w_10},                      {**w_1}),
            ({**sc, **h_20},                      {**h_2}),
            ({**sc, **w_10, **h_20},              {**w_1, **h_2}),
            ({**sc, **s_w30},                     {**s_w3}),
            ({**sc, **w_10, **s_w30},             {**w_1, **s_w3}),
            ({**sc, **h_20, **s_w30},             {**h_2, **s_w3}),
            ({**sc, **w_10, **h_20, **s_w30},     {**w_1, **h_2, **s_w3}),
            ({**sc, **s_h40},                     {**s_h4}),
            ({**sc, **w_10, **s_h40},             {**w_1, **s_h4}),
            ({**sc, **h_20, **s_h40},             {**h_2, **s_h4}),
            ({**sc, **w_10, **h_20, **s_h40},     {**w_1, **h_2, **s_h4}),
            ({**sc, **s_w30_h40},                 {**s_w3_h4}),
            ({**sc, **w_10, **s_w30_h40},         {**w_1, **s_w3_h4}),
            ({**sc, **h_20, **s_w30_h40},         {**h_2, **s_w3_h4}),
            ({**sc, **w_10, **h_20, **s_w30_h40}, {**w_1, **h_2, **s_w3_h4}),

            # Test both the global rule and the scale= attribute; combined scaling factor should be
            # 2.5 * 0.1 = 0.25.
            ({**x, **sc},                              {**x}),
            ({**x, **sc, **w_10},                      {**x, **w_2p5}),
            ({**x, **sc, **h_20},                      {**x, **h_5}),
            ({**x, **sc, **w_10, **h_20},              {**x, **w_2p5, **h_5}),
            ({**x, **sc, **s_w30},                     {**x, **s_w7p5}),
            ({**x, **sc, **w_10, **s_w30},             {**x, **w_2p5, **s_w7p5}),
            ({**x, **sc, **h_20, **s_w30},             {**x, **h_5, **s_w7p5}),
            ({**x, **sc, **w_10, **h_20, **s_w30},     {**x, **w_2p5, **h_5, **s_w7p5}),
            ({**x, **sc, **s_h40},                     {**x, **s_h10}),
            ({**x, **sc, **w_10, **s_h40},             {**x, **w_2p5, **s_h10}),
            ({**x, **sc, **h_20, **s_h40},             {**x, **h_5, **s_h10}),
            ({**x, **sc, **w_10, **h_20, **s_h40},     {**x, **w_2p5, **h_5, **s_h10}),
            ({**x, **sc, **s_w30_h40},                 {**x, **s_w7p5_h10}),
            ({**x, **sc, **w_10, **s_w30_h40},         {**x, **w_2p5, **s_w7p5_h10}),
            ({**x, **sc, **h_20, **s_w30_h40},         {**x, **h_5, **s_w7p5_h10}),
            ({**x, **sc, **w_10, **h_20, **s_w30_h40}, {**x, **w_2p5, **h_5, **s_w7p5_h10}),

            # Test that scaling is prevented when at least one attribute/property is expressed in
            # relative units. ('RR' in our shorthand notation.)
            ({**x},                              ...),
            ({**x, **w_RR},                      ...),
            ({**x, **h_RR},                      ...),
            ({**x, **w_10, **h_RR},              ...),
            ({**x, **s_wRR},                     ...),
            ({**x, **w_10, **s_wRR},             ...),
            ({**x, **h_RR, **s_w30},             ...),
            ({**x, **w_10, **h_20, **s_wRR},     ...),
            ({**x, **s_hRR},                     ...),
            ({**x, **w_RR, **s_h40},             ...),
            ({**x, **h_20, **s_hRR},             ...),
            ({**x, **w_10, **h_RR, **s_h40},     ...),
            ({**x, **s_wRR_hRR},                 ...),
            ({**x, **w_RR, **s_w30_h40},         ...),
            ({**x, **h_20, **s_wRR_hRR},         ...),
            ({**x, **w_10, **h_20, **s_wRR_hRR}, ...),
        ]:
            if exp_attr is ...: exp_attr = inp_attr

            root = ElementTree.Element('div')
            p = ElementTree.SubElement(root, 'p')
            svg = ElementTree.SubElement(p, 'svg', attrib = inp_attr)

            image_scaling.scale_images(root, mock_build_params)

            msg = repr({'inputs': inp_attr, 'expected_result': exp_attr})

            self.assertTrue('scale' not in svg.attrib, msg = msg)
            self.assertEqual(list(exp_attr.keys()), list(svg.attrib.keys()), msg = msg)

            for key, exp_value in exp_attr.items():

                # Strip spaces and new-lines
                exp_value = WHITESPACE.sub('', exp_value)
                actual_value = svg.get(key)
                actual_value = WHITESPACE.sub('', actual_value)
                actual_value = TRAILING_ZEROS.sub(TRAILING_ZERO_REPL, actual_value)

                self.assertEqual(exp_value, actual_value, msg = msg)

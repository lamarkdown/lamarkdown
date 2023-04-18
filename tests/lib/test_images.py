from ..util.mock_progress import MockProgress
from lamarkdown.lib import images

import unittest
from unittest.mock import Mock, PropertyMock, patch
from hamcrest import *

import lxml
import PIL.Image

import collections
import io
import re
from textwrap import dedent
from xml.etree import ElementTree

# TODO:
# - test <img>/<source> with:
#   - src= points to something invalid or is missing

class ImageScalingTestCase(unittest.TestCase):


    NUMBER_REGEX = re.compile('[0-9]+(\.[0-9]+)?')

    @classmethod
    def setUpClass(cls):
        import cssutils
        cssutils.log.setLevel('CRITICAL')

    def normalise_number_str(self, match):
        return str(float(match.group()))[:8]

    def _compare_attrs(self, element, expected_attrs, msg):
        self.assertNotIn('scale', element.attrib, msg = msg)
        self.assertNotIn('abs-scale', element.attrib, msg = msg)
        self.assertEqual(list(expected_attrs.keys()), list(element.attrib.keys()), msg = msg)

        for key, expected_value in expected_attrs.items():

            actual_value = element.get(key).replace('\n', ' ')
            expected_value = expected_value.replace('\n', ' ')

            # Reformat any numeric component of the attribute, so we don't get caught out by
            # '5' vs '5.0', for instance.
            expected_value = self.NUMBER_REGEX.sub(self.normalise_number_str, expected_value)
            actual_value = self.NUMBER_REGEX.sub(self.normalise_number_str, actual_value)

            self.assertEqual(expected_value, actual_value, msg = msg)


    @patch('lamarkdown.lib.resources.read_url')
    def test_rescale_direct(self, mock_real_url):

        mock_build_params = Mock()

        # Mock scaling rule: scale <svg> elements by 2.5 iff they have an 'x=...' attribute
        # (or 1.0 if they don't).
        type(mock_build_params).scale_rule = \
            PropertyMock(return_value = lambda attr = {}, **k: 2.5 if 'x' in attr else 1.0)

        # Test input shorthands
        # ---------------------

        # Misc
        x = {'x': 'dummy'} # Arbitrary attribute that invokes the scale rule
        sc = {'scale': '0.1'}
        abs_sc = {'abs-scale': ''}

        # Main test input shorthands
        w_10       = {'width': '10'}
        h_20       = {'height': '20pt'}
        s_w30      = {'style': 'width: 30px'}
        s_h40      = {'style': 'height: 40mm'}
        s_w30_h40  = {'style': 'width: 30px; height: 40mm'}

        # Relative-unit test input shorthands
        w_RR       = {'width': '10vw'}
        h_RR       = {'height': '20vh'}
        s_wRR      = {'style': 'width: 30em'}
        s_hRR      = {'style': 'height: 40ex'}
        s_wRR_hRR  = {'style': 'width: 30%; height: 40%'}


        # Expected result shorthands
        # --------------------------

        # Results when scaled by 2.5 (as per scale_rule())
        w_25       = {'width': '25'}
        h_50       = {'height': '50pt'}
        s_w75      = {'style': 'width: 75px'}
        s_h100     = {'style': 'height: 100mm'}
        s_w75_h100 = {'style': 'width: 75px; height: 100mm'}

        # Results when scaled by 0.1 (as per the scale=... attribute)
        w_1        = {'width': '1'}
        h_2        = {'height': '2pt'}
        s_w3       = {'style': 'width: 3px'}
        s_h4       = {'style': 'height: 4mm'}
        s_w3_h4    = {'style': 'width: 3px; height: 4mm'}

        # Results when scaled by 0.25 (combined)
        w_2p5      = {'width': '2.5'}
        h_5        = {'height': '5pt'}
        s_w7p5     = {'style': 'width: 7.5px'}
        s_h10      = {'style': 'height: 10mm'}
        s_w7p5_h10 = {'style': 'width: 7.5px; height: 10mm'}


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

            # Test that abs-scale eliminates the effect of the scale_rule.
            ({**x, **abs_sc, **sc},                              {**x}),
            ({**x, **abs_sc, **sc, **w_10},                      {**x, **w_1}),
            ({**x, **abs_sc, **sc, **h_20},                      {**x, **h_2}),
            ({**x, **abs_sc, **sc, **w_10, **h_20},              {**x, **w_1, **h_2}),
            ({**x, **abs_sc, **sc, **s_w30},                     {**x, **s_w3}),
            ({**x, **abs_sc, **sc, **w_10, **s_w30},             {**x, **w_1, **s_w3}),
            ({**x, **abs_sc, **sc, **h_20, **s_w30},             {**x, **h_2, **s_w3}),
            ({**x, **abs_sc, **sc, **w_10, **h_20, **s_w30},     {**x, **w_1, **h_2, **s_w3}),
            ({**x, **abs_sc, **sc, **s_h40},                     {**x, **s_h4}),
            ({**x, **abs_sc, **sc, **w_10, **s_h40},             {**x, **w_1, **s_h4}),
            ({**x, **abs_sc, **sc, **h_20, **s_h40},             {**x, **h_2, **s_h4}),
            ({**x, **abs_sc, **sc, **w_10, **h_20, **s_h40},     {**x, **w_1, **h_2, **s_h4}),
            ({**x, **abs_sc, **sc, **s_w30_h40},                 {**x, **s_w3_h4}),
            ({**x, **abs_sc, **sc, **w_10, **s_w30_h40},         {**x, **w_1, **s_w3_h4}),
            ({**x, **abs_sc, **sc, **h_20, **s_w30_h40},         {**x, **h_2, **s_w3_h4}),
            ({**x, **abs_sc, **sc, **w_10, **h_20, **s_w30_h40}, {**x, **w_1, **h_2, **s_w3_h4}),

            # Test that scaling is prevented when at least one attribute/property is expressed in
            # relative units. ('RR' in our shorthand notation.)
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

            for tag in ['svg', 'img', 'source']:

                root = ElementTree.Element('div')
                p = ElementTree.SubElement(root, 'p')
                image = ElementTree.SubElement(p, tag, attrib = inp_attr)

                images.scale_images(root, mock_build_params)

                self._compare_attrs(image, exp_attr,
                                    repr({'inputs': inp_attr, 'expected_result': exp_attr}))
                mock_real_url.assert_not_called()


    @patch('lamarkdown.lib.resources.read_url')
    def test_rescale_img_svg(self, mock_real_url):

        mock_build_params = Mock()

        # Mock scaling rule: scale <svg> elements by 2.5 iff they have an 'x=...' attribute
        # (or 1.0 if they don't).
        type(mock_build_params).scale_rule = \
            PropertyMock(return_value = lambda attr = {}, **k: 2.5 if 'x' in attr else 1.0)

        # Test input shorthands
        # ---------------------

        # Misc
        x = {'x': 'dummy'} # Arbitrary attribute that invokes the scale rule
        sc = {'scale': '0.1'}
        abs_sc = {'abs-scale': ''}
        src = {'src': 'mock url'}

        # Main test input shorthands
        w_10       = {'width': '10'}
        h_20       = {'height': '20pt'}
        s_w30      = {'style': 'width: 30px'}
        s_h40      = {'style': 'height: 40mm'}
        s_w30_h40  = {'style': 'width: 30px; height: 40mm'}

        # Relative-unit test input shorthands
        w_RR       = {'width': '10vw'}
        h_RR       = {'height': '20vh'}
        s_wRR      = {'style': 'width: 30vmax'}
        s_hRR      = {'style': 'height: 40vmin'}
        s_wRR_hRR  = {'style': 'width: 30%; height: 40%'}


        # Expected result shorthands
        # --------------------------

        # Results when scaled by 2.5 (as per scale_rule())
        w_25       = {'width':  str(10 * 2.5)}
        h_50       = {'height': str(20 * 2.5 * 96/72)} # pt->px
        w_75       = {'width':  str(30 * 2.5)}
        h_100      = {'height': str(40 * 2.5 * 96/25.4)} # mm->px

        # Results when scaled by 0.1 (as per the scale=... attribute)
        w_1        = {'width':  str(10 * 0.1)}
        h_2        = {'height': str(20 * 0.1 * 96/72)} # pt->px
        w_3        = {'width':  str(30 * 0.1)}
        h_4        = {'height': str(40 * 0.1 * 96/25.4)} # mm->px

        # Results when scaled by 0.25 (combined)
        w_2p5      = {'width':  str(10 * 0.25)}
        h_5        = {'height': str(20 * 0.25 * 96/72)} # pt->px
        w_7p5      = {'width':  str(30 * 0.25)}
        h_10       = {'height': str(40 * 0.25 * 96/25.4)} # mm->px


        # Regex to allow us to strip out any whitespace and trailing post-decimal zeros from the
        # actual result, so we can then do simple string comparisons rather than parsing the values.
        WHITESPACE = re.compile('\s+')
        TRAILING_ZEROS = re.compile(r'(\.[0-9]*?)0+\b')
        TRAILING_ZERO_REPL = r'\1'

        for inp_parent_attr, inp_svg_attr, exp_attr in [
            # Without the criteria that invokes the scaling rule (well, technically it's always
            # invoked, but here it returns 1.0), and without a 'scale' attribute, no scaling should
            # happen. ('...' refers to the test input.)
            ({**src}, {},                            ...),
            ({**src}, {**w_10},                      ...),
            ({**src}, {**h_20},                      ...),
            ({**src}, {**w_10, **h_20},              ...),
            ({**src}, {**s_w30},                     ...),
            ({**src}, {**w_10, **s_w30},             ...),
            ({**src}, {**h_20, **s_w30},             ...),
            ({**src}, {**w_10, **h_20, **s_w30},     ...),
            ({**src}, {**s_h40},                     ...),
            ({**src}, {**w_10, **s_h40},             ...),
            ({**src}, {**h_20, **s_h40},             ...),
            ({**src}, {**w_10, **h_20, **s_h40},     ...),
            ({**src}, {**s_w30_h40},                 ...),
            ({**src}, {**w_10, **s_w30_h40},         ...),
            ({**src}, {**h_20, **s_w30_h40},         ...),
            ({**src}, {**w_10, **h_20, **s_w30_h40}, ...),

            # Given a criteria that invokes the scaling rule (for a scaling factor of 2.5), check
            # that the scale is applied to all width/height combinations.
            ({**src, **x}, {},                            {**src, **x}),
            ({**src, **x}, {**w_10},                      {**src, **x, **w_25}),
            ({**src, **x}, {**h_20},                      {**src, **x, **h_50}),
            ({**src, **x}, {**w_10, **h_20},              {**src, **x, **w_25, **h_50}),
            ({**src, **x}, {**s_w30},                     {**src, **x, **w_75}),
            ({**src, **x}, {**w_10, **s_w30},             {**src, **x, **w_75}),
            ({**src, **x}, {**h_20, **s_w30},             {**src, **x, **w_75, **h_50}),
            ({**src, **x}, {**w_10, **h_20, **s_w30},     {**src, **x, **w_75, **h_50}),
            ({**src, **x}, {**s_h40},                     {**src, **x, **h_100}),
            ({**src, **x}, {**w_10, **s_h40},             {**src, **x, **w_25, **h_100}),
            ({**src, **x}, {**h_20, **s_h40},             {**src, **x, **h_100}),
            ({**src, **x}, {**w_10, **h_20, **s_h40},     {**src, **x, **w_25, **h_100}),
            ({**src, **x}, {**s_w30_h40},                 {**src, **x, **w_75, **h_100}),
            ({**src, **x}, {**w_10, **s_w30_h40},         {**src, **x, **w_75, **h_100}),
            ({**src, **x}, {**h_20, **s_w30_h40},         {**src, **x, **w_75, **h_100}),
            ({**src, **x}, {**w_10, **h_20, **s_w30_h40}, {**src, **x, **w_75, **h_100}),

            # Given a scale=0.1 attribute, check that the scale is applied to all width/height
            # combinations. (Also, the scale= attribute must be removed.)
            ({**src, **sc}, {},                            {**src}),
            ({**src, **sc}, {**w_10},                      {**src, **w_1}),
            ({**src, **sc}, {**h_20},                      {**src, **h_2}),
            ({**src, **sc}, {**w_10, **h_20},              {**src, **w_1, **h_2}),
            ({**src, **sc}, {**s_w30},                     {**src, **w_3}),
            ({**src, **sc}, {**w_10, **s_w30},             {**src, **w_3}),
            ({**src, **sc}, {**h_20, **s_w30},             {**src, **w_3, **h_2}),
            ({**src, **sc}, {**w_10, **h_20, **s_w30},     {**src, **w_3, **h_2}),
            ({**src, **sc}, {**s_h40},                     {**src, **h_4}),
            ({**src, **sc}, {**w_10, **s_h40},             {**src, **w_1, **h_4}),
            ({**src, **sc}, {**h_20, **s_h40},             {**src, **h_4}),
            ({**src, **sc}, {**w_10, **h_20, **s_h40},     {**src, **w_1, **h_4}),
            ({**src, **sc}, {**s_w30_h40},                 {**src, **w_3, **h_4}),
            ({**src, **sc}, {**w_10, **s_w30_h40},         {**src, **w_3, **h_4}),
            ({**src, **sc}, {**h_20, **s_w30_h40},         {**src, **w_3, **h_4}),
            ({**src, **sc}, {**w_10, **h_20, **s_w30_h40}, {**src, **w_3, **h_4}),

            # Test both the global rule and the scale= attribute; combined scaling factor should be
            # 2.5 * 0.1 = 0.25.
            ({**src, **x, **sc}, {},                            {**src, **x}),
            ({**src, **x, **sc}, {**w_10},                      {**src, **x, **w_2p5}),
            ({**src, **x, **sc}, {**h_20},                      {**src, **x, **h_5}),
            ({**src, **x, **sc}, {**w_10, **h_20},              {**src, **x, **w_2p5, **h_5}),
            ({**src, **x, **sc}, {**s_w30},                     {**src, **x, **w_7p5}),
            ({**src, **x, **sc}, {**w_10, **s_w30},             {**src, **x, **w_7p5}),
            ({**src, **x, **sc}, {**h_20, **s_w30},             {**src, **x, **w_7p5, **h_5}),
            ({**src, **x, **sc}, {**w_10, **h_20, **s_w30},     {**src, **x, **w_7p5, **h_5}),
            ({**src, **x, **sc}, {**s_h40},                     {**src, **x, **h_10}),
            ({**src, **x, **sc}, {**w_10, **s_h40},             {**src, **x, **w_2p5, **h_10}),
            ({**src, **x, **sc}, {**h_20, **s_h40},             {**src, **x, **h_10}),
            ({**src, **x, **sc}, {**w_10, **h_20, **s_h40},     {**src, **x, **w_2p5, **h_10}),
            ({**src, **x, **sc}, {**s_w30_h40},                 {**src, **x, **w_7p5, **h_10}),
            ({**src, **x, **sc}, {**w_10, **s_w30_h40},         {**src, **x, **w_7p5, **h_10}),
            ({**src, **x, **sc}, {**h_20, **s_w30_h40},         {**src, **x, **w_7p5, **h_10}),
            ({**src, **x, **sc}, {**w_10, **h_20, **s_w30_h40}, {**src, **x, **w_7p5, **h_10}),

            # Test that abs-scale eliminates the effect of the scale_rule.
            ({**src, **x, **abs_sc, **sc}, {},                            {**src, **x}),
            ({**src, **x, **abs_sc, **sc}, {**w_10},                      {**src, **x, **w_1}),
            ({**src, **x, **abs_sc, **sc}, {**h_20},                      {**src, **x, **h_2}),
            ({**src, **x, **abs_sc, **sc}, {**w_10, **h_20},              {**src, **x, **w_1, **h_2}),
            ({**src, **x, **abs_sc, **sc}, {**s_w30},                     {**src, **x, **w_3}),
            ({**src, **x, **abs_sc, **sc}, {**w_10, **s_w30},             {**src, **x, **w_3}),
            ({**src, **x, **abs_sc, **sc}, {**h_20, **s_w30},             {**src, **x, **w_3, **h_2}),
            ({**src, **x, **abs_sc, **sc}, {**w_10, **h_20, **s_w30},     {**src, **x, **w_3, **h_2}),
            ({**src, **x, **abs_sc, **sc}, {**s_h40},                     {**src, **x, **h_4}),
            ({**src, **x, **abs_sc, **sc}, {**w_10, **s_h40},             {**src, **x, **w_1, **h_4}),
            ({**src, **x, **abs_sc, **sc}, {**h_20, **s_h40},             {**src, **x, **h_4}),
            ({**src, **x, **abs_sc, **sc}, {**w_10, **h_20, **s_h40},     {**src, **x, **w_1, **h_4}),
            ({**src, **x, **abs_sc, **sc}, {**s_w30_h40},                 {**src, **x, **w_3, **h_4}),
            ({**src, **x, **abs_sc, **sc}, {**w_10, **s_w30_h40},         {**src, **x, **w_3, **h_4}),
            ({**src, **x, **abs_sc, **sc}, {**h_20, **s_w30_h40},         {**src, **x, **w_3, **h_4}),
            ({**src, **x, **abs_sc, **sc}, {**w_10, **h_20, **s_w30_h40}, {**src, **x, **w_3, **h_4}),

            # Test that scaling is prevented when at least one attribute/property is expressed in
            # relative units. ('RR' in our shorthand notation.)
            ({**src, **x}, {**w_RR},                      ...),
            ({**src, **x}, {**h_RR},                      ...),
            ({**src, **x}, {**w_10, **h_RR},              ...),
            ({**src, **x}, {**s_wRR},                     ...),
            ({**src, **x}, {**w_10, **s_wRR},             ...),
            ({**src, **x}, {**h_RR, **s_w30},             ...),
            ({**src, **x}, {**w_10, **h_20, **s_wRR},     ...),
            ({**src, **x}, {**s_hRR},                     ...),
            ({**src, **x}, {**w_RR, **s_h40},             ...),
            ({**src, **x}, {**h_20, **s_hRR},             ...),
            ({**src, **x}, {**w_10, **h_RR, **s_h40},     ...),
            ({**src, **x}, {**s_wRR_hRR},                 ...),
            ({**src, **x}, {**w_RR, **s_w30_h40},         ...),
            ({**src, **x}, {**h_20, **s_wRR_hRR},         ...),
            ({**src, **x}, {**w_10, **h_20, **s_wRR_hRR}, ...),
        ]:
            if exp_attr is ...: exp_attr = inp_parent_attr

            for tag in ['img', 'source']:

                svg = ElementTree.Element('svg', attrib = inp_svg_attr)
                mock_real_url.return_value = (False,
                                              ElementTree.tostring(svg),
                                              'image/svg+xml')

                root = ElementTree.Element('div')
                p = ElementTree.SubElement(root, 'p')
                image = ElementTree.SubElement(p, tag, attrib = inp_parent_attr)

                images.scale_images(root, mock_build_params)

                self._compare_attrs(image, exp_attr,
                                    repr({'parent attr': inp_parent_attr,
                                          'child attr': inp_svg_attr,
                                          'expected result': exp_attr}))


    @patch('lamarkdown.lib.resources.read_url')
    def test_all_unit_conversions(self, mock_real_url):

        scale = 2.5
        mock_build_params = Mock()
        type(mock_build_params).scale_rule = PropertyMock(return_value = lambda **k: scale)

        for unit,  px_equiv in [
            ('cm', 96/2.54),
            ('mm', 96/25.4),
            ('q',  96/25.4/4),
            ('in', 96),
            ('pc', 96/6),
            ('pt', 96/72),
            ('px', 1),
            ('',   1),
        ]:
            for unit_str in [
                unit,
                unit.upper(),
                *([] if len(unit) < 2 else [
                    unit[0].upper() + unit[1],
                    unit[0] + unit[1].upper()
                ])
            ]:
                for attrib in [
                    {'width': f'10{unit_str}', 'height': f'20{unit_str}'},
                    {'style': f'width: 10{unit_str}; height: 20{unit_str}'},
                ]:
                    svg = ElementTree.Element('svg', attrib = attrib)
                    mock_real_url.return_value = (False,
                                                  ElementTree.tostring(svg),
                                                  'image/svg+xml')
                    root = ElementTree.Element('div')
                    p = ElementTree.SubElement(root, 'p')
                    image = ElementTree.SubElement(p, 'img', attrib = {'src': 'mock url'})

                    images.scale_images(root, mock_build_params)

                    expected_attrib = {'src': 'mock url',
                                       'width': str(10 * 2.5 * px_equiv),
                                       'height': str(20 * 2.5 * px_equiv)}

                    self._compare_attrs(image, expected_attrib,
                                        repr({'unit': unit_str, 'px_equiv': px_equiv, 'attrib': attrib}))


    @patch('lamarkdown.lib.resources.read_url')
    def test_rescale_img_raster(self, mock_real_url):

        mock_build_params = Mock()

        # Mock scaling rule: scale <svg> elements by 2.5 iff they have an 'x=...' attribute
        # (or 1.0 if they don't).
        type(mock_build_params).scale_rule = \
            PropertyMock(return_value = lambda attr = {}, **k: 2.5 if 'x' in attr else 1.0)

        # Test input shorthands
        x = {'x': 'dummy'} # Arbitrary attribute that invokes the scale rule
        sc = {'scale': '0.1'}
        abs_sc = {'abs-scale': ''}
        src = {'src': 'mock url'}

        for width, height, format, mime_type in [
            (10,   20,     'PNG',  'image/png'),
            (20,   10,     'JPEG', 'image/jpeg'),
            ( 1,    1,     'PNG',  'image/png'),
            (20,   20,     'JPEG', 'image/jpeg'),
        ]:
            image_buf = io.BytesIO()
            PIL.Image.new(mode = "RGB", size = (width, height)).save(image_buf, format = format)
            mock_real_url.return_value = (False, image_buf.getvalue(), mime_type)

            for inp_attr,                      exp_attr in [
                ({**src},                      {**src}),
                ({**src, **x},                 {**src, **x, 'width': str(width * 2.5),
                                                            'height': str(height * 2.5)}),
                ({**src, **sc},                {**src,      'width': str(width * 0.1),
                                                            'height': str(height * 0.1)}),
                ({**src, **x, **sc},           {**src, **x, 'width': str(width * 0.25),
                                                            'height': str(height * 0.25)}),
                ({**src, **abs_sc, **x, **sc}, {**src, **x, 'width': str(width * 0.1),
                                                            'height': str(height * 0.1)}),
            ]:
                for tag in ['img', 'source']:

                    root = ElementTree.Element('div')
                    p = ElementTree.SubElement(root, 'p')
                    image = ElementTree.SubElement(p, tag, attrib = inp_attr)

                    images.scale_images(root, mock_build_params)

                    self._compare_attrs(image, exp_attr,
                                        repr({'input attr': inp_attr, 'expected result': exp_attr}))



    def test_disentangle_svgs_fn(self):
        doc = r'''
            <div id="alpha">
                <p id="beta"></p>
                <p id="gamma"></p>
                <svg id="delta">
                    <defs>
                        <g id="gamma" />
                        <g id="delta" />
                        <g id="epsilon" />
                        <g id="zeta" />
                    </defs>
                    <use href="#alpha" />
                    <use href="#beta" />
                    <use href="#gamma" />
                    <use href="#delta" />
                    <use href="#epsilon" />
                    <use href="#zeta" />
                </svg>
                <svg id="epsilon">
                    <defs>
                        <g id="alpha" />
                        <g id="gamma" />
                        <g id="gamma_0" />
                        <g id="gamma_1" />
                    </defs>
                    <use href="#alpha" />
                    <use href="#gamma" />
                    <use href="#gamma_0" />
                    <use href="#gamma_1" />
                    <use href="#zeta" />
                </svg>
            </div>
        '''

        root_element = lxml.html.fromstring(doc)
        original_id_set = set(root_element.xpath('//@id'))

        # Copy all id and href attributes to id0 and href0, so that the original matching elements
        # can be matched up again after their id and href have changed.

        for id_element in root_element.xpath('//svg//*[@id]'):
            id_element.set('id0', id_element.get('id'))

        for href_element in root_element.xpath('//svg//*[@href]'):
            href = href_element.get('href')
            href_element.set('href0', href)
            # Sanity-check the test setup itself:
            self.assertTrue(href.startswith('#'))
            self.assertTrue(href[1:] in original_id_set)

        images.disentangle_svgs(root_element)

        new_ids = collections.Counter(root_element.xpath('//@id'))
        assert_that(new_ids, has_entries({id: 1 for id in original_id_set}))

        # Within each <svg> element, test for consistency in how href= and id= elements map to
        # one another

        for svg_element in root_element.xpath('//svg'):
            id_map = {} # New->old ID mapping
            for id_element in svg_element.xpath('.//*[@id]'):
                id_map[id_element.get('id')] = id_element.get('id0')

            for href_element in svg_element.xpath('.//*[@href]'):
                new_href = href_element.get('href')[1:]
                old_href = href_element.get('href0')[1:]
                if new_href in id_map:
                    self.assertEqual(old_href, id_map[new_href])
                else:
                    # If the reference isn't defined now (within the <svg> element), then it
                    # shouldn't have been defined before either.
                    self.assertNotIn(old_href, id_map.values())

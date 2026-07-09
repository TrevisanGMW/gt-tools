import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.utils import hypertext as utils_html


class TestHyperTextUtils(unittest.TestCase):
    def test_default_parameters(self):
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        result = utils_html.extract_text_from_html(html)
        expected = "Hello\nWorld"
        self.assertEqual(expected, result)

    def test_ignore_tags(self):
        html = "<html><body><script>console.log('test');</script><p>World</p></body></html>"
        result = utils_html.extract_text_from_html(html, ignore_tags=["script"])
        expected = "World"
        self.assertEqual(expected, result)

    def test_preserve_whitespace(self):
        html = "<html><body><p>   Hello   </p><p>   World   </p></body></html>"
        result = utils_html.extract_text_from_html(html, preserve_whitespace=True)
        expected = "   Hello   \n   World   "
        self.assertEqual(expected, result)

    def test_no_preserve_whitespace(self):
        html = "<html><body><p>   Hello   </p><p>   World   </p></body></html>"
        result = utils_html.extract_text_from_html(html, preserve_whitespace=False)
        expected = "Hello\nWorld"
        self.assertEqual(expected, result)

    def test_convert_entities(self):
        html = "<html><body><p>&lt;div&gt;Hello World&lt;/div&gt;</p></body></html>"
        result = utils_html.extract_text_from_html(html, convert_entities=True)
        expected = "<div>Hello World</div>"
        self.assertEqual(expected, result)

    def test_include_comments(self):
        html = "<html><body><!-- This is a comment --><p>World</p></body></html>"
        result = utils_html.extract_text_from_html(html, include_comments=True)
        expected = "This is a commentWorld"
        self.assertEqual(expected, result)

    def test_no_include_comments(self):
        html = "<html><body><!-- This is a comment --><p>World</p></body></html>"
        result = utils_html.extract_text_from_html(html, include_comments=False)
        expected = "World"
        self.assertEqual(expected, result)

    def test_preserve_line_breaks(self):
        html = "<html><body><h1>Hello</h1><p>World</p><br><p>New Paragraph</p></body></html>"
        result = utils_html.extract_text_from_html(html, preserve_line_breaks=True)
        expected = "Hello\nWorld\nNew Paragraph"
        self.assertEqual(expected, result)

    def test_no_preserve_line_breaks(self):
        html = "<html><body><h1>Hello</h1><p>World</p><br><p>New Paragraph</p></body></html>"
        result = utils_html.extract_text_from_html(html, preserve_line_breaks=False)
        expected = "HelloWorldNew Paragraph"
        self.assertEqual(expected, result)

    def test_multiple_tags_and_line_breaks(self):
        html = "<html><body><h1>Header</h1><p>First Paragraph</p><br><p>Second Paragraph</p><br></body></html>"
        result = utils_html.extract_text_from_html(html, preserve_line_breaks=True)
        expected = "Header\nFirst Paragraph\nSecond Paragraph"
        self.assertEqual(expected, result)

    def test_empty_html(self):
        html = ""
        result = utils_html.extract_text_from_html(html)
        expected = ""
        self.assertEqual(expected, result)

    def test_no_tags(self):
        html = "Just some plain text."
        result = utils_html.extract_text_from_html(html)
        expected = "Just some plain text."
        self.assertEqual(expected, result)

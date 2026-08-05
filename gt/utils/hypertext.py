"""
HTML (HyperText) Utilities

Import Line:
    import gt.utils.hypertext as utils_html
"""

from html.parser import HTMLParser
from html import unescape


class HTMLTextExtractor(HTMLParser):
    """
    A flexible HTML parser that extracts plain text from HTML content while preserving line breaks.

    Attributes:
        ignore_tags (set[str]): Tags whose content should be ignored (e.g., {"script", "style"}).
        preserve_whitespace (bool): Whether to preserve all whitespace in the output.
        convert_entities (bool): Whether to convert HTML entities to Unicode characters.
        include_comments (bool): Whether to include HTML comments in the output.
        preserve_line_breaks (bool): Whether to preserve line breaks (e.g., after <p>, <br>, etc.).
    """

    def __init__(
        self,
        ignore_tags=None,
        preserve_whitespace=False,
        convert_entities=True,
        include_comments=False,
        preserve_line_breaks=True,
    ):
        """
        Initializes the HTMLTextExtractor parser.

        Args:
            ignore_tags (list[str], optional): Tags to ignore while parsing. Defaults to ["script", "style"].
            preserve_whitespace (bool): Whether to preserve whitespace. Defaults to False.
            convert_entities (bool): Whether to convert HTML entities. Defaults to True.
            include_comments (bool): Whether to include HTML comments. Defaults to False.
            preserve_line_breaks (bool): Whether to preserve line breaks. Defaults to True.
        """
        super().__init__()
        self.ignore_tags = set(ignore_tags or ["script", "style"])
        self.preserve_whitespace = preserve_whitespace
        self.convert_entities = convert_entities
        self.include_comments = include_comments
        self.preserve_line_breaks = preserve_line_breaks
        self._text_parts = []
        self._ignoring = False
        self._ignore_stack = []
        self._last_tag = None
        self._last_added_text = None  # To keep track of the last added text

    def handle_starttag(self, tag, attrs):
        """
        Overrides HTMLParser.handle_starttag.

        Called when the parser encounters the start of a tag.

        Args:
            tag (str): The name of the tag.
            attrs (list[tuple[str, str]]): A list of (attribute, value) pairs found in the tag.
        """
        if tag in self.ignore_tags:
            self._ignoring = True
            self._ignore_stack.append(tag)

        if tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "br"} and self.preserve_line_breaks:
            self._last_tag = tag

    def handle_endtag(self, tag):
        """
        Overrides HTMLParser.handle_endtag.

        Called when the parser encounters the end of a tag.

        Args:
            tag (str): The name of the tag.
        """
        if tag in self.ignore_tags:
            if self._ignore_stack and self._ignore_stack[-1] == tag:
                self._ignore_stack.pop()
            if not self._ignore_stack:
                self._ignoring = False

        # If it's a block element that requires a line break, insert a newline after it
        if tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "br"} and self.preserve_line_breaks:
            if tag != "br":
                # Only add a newline if it's not the last added text
                if self._last_added_text != "\n":
                    self._text_parts.append("\n")
                self._last_added_text = "\n"
            else:
                self._last_added_text = None  # Reset for <br>

    def handle_data(self, data):
        """
        Overrides HTMLParser.handle_data.

        Called to process the data within HTML tags.

        Args:
            data (str): The textual data found between HTML tags.
        """
        if not self._ignoring:
            text = data if self.preserve_whitespace else data.strip()
            if text:
                if self.convert_entities:
                    text = unescape(text)  # Convert HTML entities to Unicode
                self._text_parts.append(text)
                self._last_added_text = text

    def handle_comment(self, data):
        """
        Overrides HTMLParser.handle_comment.

        Called to process an HTML comment.

        Args:
            data (str): The text inside the comment.
        """
        if self.include_comments and not self._ignoring:
            # Ensure no leading or trailing whitespace is added between comment and the following text
            comment_text = data.strip()
            if comment_text:
                # If the previous part was text, add a space between comment and text
                if self._last_added_text and self._last_added_text not in {"\n", " "}:
                    self._text_parts.append(" ")
                self._text_parts.append(comment_text)

    def get_text(self):
        """
        Returns the accumulated plain text extracted from the HTML.

        Returns:
            str: The plain text content.
        """
        # Remove the final newline if it was added after the last block of text
        if self._text_parts and self._text_parts[-1] == "\n":
            self._text_parts.pop()
        return "".join(self._text_parts)


def extract_text_from_html(
    html_string,
    ignore_tags=None,
    preserve_whitespace=False,
    convert_entities=True,
    include_comments=False,
    preserve_line_breaks=True,
):
    """
    Extracts plain text from an HTML string using HTMLTextExtractor.

    Args:
        html_string (str): The HTML content to parse.
        ignore_tags (list[str], optional): Tags whose content should be ignored. Defaults to ["script", "style"].
        preserve_whitespace (bool): Whether to preserve whitespace in output. Defaults to False.
        convert_entities (bool): Whether to convert HTML entities to Unicode. Defaults to True.
        include_comments (bool): Whether to include comments in the output. Defaults to False.
        preserve_line_breaks (bool): Whether to preserve line breaks. Defaults to True.

    Returns:
        str: The extracted plain text.
    """
    parser = HTMLTextExtractor(
        ignore_tags=ignore_tags,
        preserve_whitespace=preserve_whitespace,
        convert_entities=convert_entities,
        include_comments=include_comments,
        preserve_line_breaks=preserve_line_breaks,
    )
    parser.feed(html_string)
    return parser.get_text()


if __name__ == "__main__":
    html = "<html><body><h1>Hello World</h1><p>This is a test.</p></body></html>"
    result = extract_text_from_html(html)
    print(result)

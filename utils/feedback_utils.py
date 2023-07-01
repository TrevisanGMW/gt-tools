"""
Feedback Utilities
github.com/TrevisanGMW/gt-tools
"""
from dataclasses import dataclass, field
import maya.cmds as cmds
import logging
import random

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class FeedbackMessage:
    """
    Class used to describe a feedback message. Only provided arguments are returned/considered/used.
    Pattern follows this exact order:
        prefix, intro, <quantity>, singular/plural, conclusion, suffix
    Parts that are not provided are ignored.
    If "zero_overwrite_message" is provided, the whole message is overwritten when quantity is zero.

    Attributes:
        quantity (int, None): If provided, it will be used to in the feedback, pluralization and overwrite functions.
                              e.g. "7 elements were affected"
                              e.g. "1 element was affected"
                              e.g. "No elements were affected"
        quantity_index (int): Determines the index (position) of the quantity portion in the feedback.
                              Default value is 2.  That is: prefix, intro, <quantity>, singular/plural...
                              e.g. If value is 0, then : <quantity>, prefix, intro, singular/plural...
                              e.g. If value is 1, then : prefix, <quantity>, intro, singular/plural...
        prefix (str, optional) : Prefix to the feedback message - 1st item (index 0)
        intro (str, optional) : Intro to the feedback message - 2nd item (index 1)
        singular (str, optional) : Text used when quantity is exactly 1 (one)
        plural  (str, optional) : Text used when quantity is a number different from 1 (one) - e.g. -1, 0 , 2, 3...
        conclusion (str, optional) : End of the message (before suffix)
        suffix (str, optional) : Very last portion of the message.
        zero_overwrite_message (str, optional): Message that overwrites the entire feedback when the quantity is zero.
        general_overwrite (str, optional) : if provided, it will ignore all other options and only print this string
                                            as feedback/message. "style_general" can be used to determine its style.

    """
    quantity: int = field(default=None)
    quantity_index: int = field(default=None)  # "_update_quantity_index" moves it after prefix and intro
    prefix: str = field(default="")
    intro: str = field(default="")
    singular: str = field(default="")
    plural: str = field(default="")
    conclusion: str = field(default="")
    suffix: str = field(default="")
    zero_overwrite_message: str = field(default=None)
    general_overwrite: str = field(default=None)

    # Only used for inview feedback - "get_inview_formatted_message()"
    style_general: str = field(default="color:#FFFFFF;")  # White
    style_quantity: str = field(default="color:#FF0000;text-decoration:underline;")  # Red with underline
    style_prefix: str = field(default=None)
    style_intro: str = field(default=None)
    style_pluralization: str = field(default=None)
    style_conclusion: str = field(default=None)
    style_suffix: str = field(default=None)
    style_zero_overwrite: str = field(default=None)

    _pluralization = ""
    _quantity_str = ""
    _overwrite_message = ""

    def _update_quantity_index(self):
        """
        Handles quantity index when it's not directly specified.
        Checks if prefix or intro exist to determine that.
        """
        if self.quantity_index is None:
            default_index = 0
            if self.prefix:
                default_index += 1
            if self.intro:
                default_index += 1
            self.quantity_index = default_index

    def _update_pluralization(self):
        """
        Determines if pluralization should be singular or plural.
        If quantity is not available pluralization becomes an empty string (not using numbers)
        """
        if self.quantity is not None:
            if self.quantity == 1:
                self._pluralization = self.singular
            else:
                self._pluralization = self.plural
            self._quantity_str = str(self.quantity)
        else:
            self._pluralization = ""
            self._quantity_str = ""

    def _update_overwrites(self):
        """
        Determines if overwrite message should be used when quantity is zero "0".
        """
        if self.quantity is not None and self.quantity == 0:
            # Override entire message?
            if self.zero_overwrite_message:
                self._overwrite_message = self.zero_overwrite_message
            else:
                self._overwrite_message = ""

    def __repr__(self):
        """
        Uses "get_string_message()" to return a proper sentence when printing or casting this object to string.
        """
        return self.get_string_message()

    def get_string_message(self):
        """
        Create string feedback sentence using available fields.
        """
        self._update_quantity_index()
        self._update_pluralization()
        self._update_overwrites()
        found_text = []
        for text in [self.prefix,
                     self.intro,
                     self._pluralization,
                     self.conclusion,
                     self.suffix]:
            if text:
                found_text.append(text)
        # Quantity use and index
        if self._quantity_str:
            found_text.insert(self.quantity_index, self._quantity_str)
        result_print = f" ".join(found_text)
        # Determine if zero overwriting - Overwrites when quantity is zero
        if self._overwrite_message:
            result_print = self._overwrite_message
        # Determine if general overwriting - Always overwrite when present
        if self.general_overwrite:
            result_print = self.general_overwrite
        return result_print

    def get_inview_formatted_message(self):
        """
        Returns feedback message with spans
        """
        self._update_quantity_index()
        self._update_pluralization()
        self._update_overwrites()
        inview_message = f"<{str(random.random())}>"  # So it can be repeated without delay
        if self.style_general:
            inview_message += f'<span style="{str(self.style_general)}">'  # Start general style span ---

        # Create content
        text_to_join = []
        for text, style in [(self.prefix, self.style_prefix),
                            (self.intro, self.style_intro),
                            (self._pluralization, self.style_pluralization),
                            (self.conclusion, self.style_conclusion),
                            (self.suffix, self.style_suffix)]:
            if text:
                if style:
                    text_to_join.append(f'<span style="{str(style)}">{text}</span>')
                else:
                    text_to_join.append(text)
        # Quantity use and index
        if self._quantity_str:
            if self.style_quantity:
                text_to_join.insert(self.quantity_index,
                                    f'<span style="{str(self.style_quantity)}">{self._quantity_str}</span>')
            else:
                text_to_join.insert(self.quantity_index,
                                    self._quantity_str)
        # Determine if zero overwriting - Overwrites when quantity is zero
        if self._overwrite_message:
            text_to_join = []
            if self.style_zero_overwrite:
                text_to_join.append(f'<span style="{str(self.style_zero_overwrite)}">{self._overwrite_message}</span>')
            else:
                text_to_join.append(self._overwrite_message)
        # Determine if general overwriting - Always overwrite when present
        if self.general_overwrite:
            text_to_join = [self.general_overwrite]

        inview_message += f" ".join(text_to_join)

        if self.style_general:
            inview_message += f'</span>'  # End general style span ---
        return inview_message


def inview_number_feedback(number, show_feedback=True):  # Add inview options
    """
    Print inViewMessage to the viewport as user feedback.
    Uses "random" to force identical messages to appear at the same time.

    Parameters:
        number (int): how many objects were renamed.
        show_feedback (bool, optional):
    """
    if not show_feedback:
        return
    if number != 0:
        inview_message = f"<{str(random.random())}>"
        inview_message += f'<span style="{"number_style"}">{str(number)}</span>'

        if number == 1:
            inview_message += '<span style=\"color:#FFFFFF;\"> object was renamed.</span>'
        else:
            inview_message += '</span><span style=\"color:#FFFFFF;\"> objects were renamed.</span>'
        cmds.inViewMessage(amg=inview_message, pos='botLeft', fade=True, alpha=.9)
    else:
        return "zero"
    return "return"


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    # import maya.standalone
    # maya.standalone.initialize()
    out = None
    # out = inview_number_feedback(number=123)

    out = FeedbackMessage(quantity=2,
                          prefix="prefix",
                          intro="intro",
                          singular="was",
                          plural="were",
                          conclusion="conclusion",
                          suffix="suffix",
                          style_general="color:#00FF00;",
                          style_intro="color:#0000FF;",
                          style_pluralization="color:#FF00FF;",
                          style_conclusion="color:#00FFFF;",
                          style_suffix="color:#F0FF00;"
                          )

    try:
        import maya.cmds as cmds
        message = out.get_inview_formatted_message()
        print(message)
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    except:
        pass
    pprint(out)

from unittest.mock import patch, MagicMock
from io import StringIO
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from utils import feedback_utils
from utils.feedback_utils import redirect_output_to_function


class TestFeedbackUtils(unittest.TestCase):
    def test_feedback_message_class_empty(self):
        feedback_object = feedback_utils.FeedbackMessage()  # cast as string to use __repr__
        result = str(feedback_object)
        expected = ""
        self.assertEqual(expected, result)

    def test_feedback_message_class_get_string_message_empty(self):
        feedback_object = feedback_utils.FeedbackMessage()
        result = feedback_object.get_string_message()
        expected = ""
        self.assertEqual(expected, result)

    def test_feedback_message_class_default_quantity_index_one(self):
        feedback_object = feedback_utils.FeedbackMessage(quantity=2,
                                                         intro="intro",
                                                         singular="was",
                                                         plural="were",
                                                         conclusion="conclusion")
        result = str(feedback_object)
        expected = "intro 2 were conclusion"
        self.assertEqual(expected, result)

    def test_feedback_message_class_default_quantity_index_two(self):
        feedback_object = feedback_utils.FeedbackMessage(quantity=2,
                                                         prefix="prefix",
                                                         singular="was",
                                                         plural="were",
                                                         conclusion="conclusion")
        result = str(feedback_object)
        expected = "prefix 2 were conclusion"
        self.assertEqual(expected, result)

    def test_feedback_message_class_default_quantity_index_three(self):
        feedback_object = feedback_utils.FeedbackMessage(quantity=2,
                                                         singular="was",
                                                         plural="were",
                                                         conclusion="conclusion")
        result = str(feedback_object)
        expected = "2 were conclusion"
        self.assertEqual(expected, result)

    def test_feedback_message_class_message_full(self):
        feedback_object = feedback_utils.FeedbackMessage(quantity=1,
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
                                                         style_suffix="color:#F0FF00;",
                                                         zero_overwrite_message="zero")
        result = str(feedback_object)
        expected = "prefix intro 1 was conclusion suffix"
        self.assertEqual(expected, result)

    def test_feedback_message_class_message_full_overwrite(self):
        feedback_object = feedback_utils.FeedbackMessage(quantity=1,
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
                                                         style_suffix="color:#F0FF00;",
                                                         zero_overwrite_message="zero",
                                                         general_overwrite="general_overwrite")
        result = str(feedback_object)
        expected = "general_overwrite"
        self.assertEqual(expected, result)

    @patch('random.random')
    def test_feedback_message_class_inview_message_zero_overwrite(self, mock_random):
        mock_random.return_value = 0.5  # Force random to return 0.5
        feedback_object = feedback_utils.FeedbackMessage(quantity=0,
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
                                                         style_suffix="color:#F0FF00;",
                                                         zero_overwrite_message="zero")
        result = feedback_object.get_inview_formatted_message()
        expected = '<0.5><span style="color:#00FF00;">zero</span>'
        self.assertEqual(expected, result)

    @patch('random.random')
    def test_feedback_message_class_inview_message_zero_overwrite_style(self, mock_random):
        mock_random.return_value = 0.5  # Force random to return 0.5
        feedback_object = feedback_utils.FeedbackMessage(quantity=0,
                                                         singular="was",
                                                         plural="were",
                                                         style_zero_overwrite="color:#FF00FF;",
                                                         style_general="",
                                                         zero_overwrite_message="zero")
        result = feedback_object.get_inview_formatted_message()
        expected = '<0.5><span style="color:#FF00FF;">zero</span>'
        self.assertEqual(expected, result)

    @patch('random.random')
    def test_feedback_message_class_inview_message_full_overwrite(self, mock_random):
        mock_random.return_value = 0.5  # Force random to return 0.5
        feedback_object = feedback_utils.FeedbackMessage(quantity=1,
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
                                                         style_suffix="color:#F0FF00;",
                                                         zero_overwrite_message="zero",
                                                         general_overwrite="general_overwrite")
        result = feedback_object.get_inview_formatted_message()
        expected = '<0.5><span style="color:#00FF00;">general_overwrite</span>'
        self.assertEqual(expected, result)

    @patch('random.random')
    def test_feedback_message_class_inview_message_full(self, mock_random):
        mock_random.return_value = 0.5  # Force random to return 0.5
        feedback_object = feedback_utils.FeedbackMessage(quantity=1,
                                                         prefix="prefix",
                                                         intro="intro",
                                                         singular="was",
                                                         plural="were",
                                                         conclusion="conclusion",
                                                         suffix="suffix",
                                                         style_general="color:#00FF00;",
                                                         style_intro="color:#0000FF;",
                                                         style_pluralization="color:#FFFFFF;",
                                                         style_conclusion="color:#00FFFF;",
                                                         style_suffix="color:#F0FF00;",
                                                         zero_overwrite_message="zero")
        result = feedback_object.get_inview_formatted_message()
        expected = '<0.5><span style="color:#00FF00;">prefix <span style="color:#0000FF;">intro</span> ' \
                   '<span style="color:#FF0000;text-decoration:underline;">1</span> ' \
                   '<span style="color:#FFFFFF;">was</span> <span style="color:#00FFFF;">conclusion</span> ' \
                   '<span style="color:#F0FF00;">suffix</span></span>'
        self.assertEqual(expected, result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_when_true_simple(self, mock_stdout):
        input_string = "mocked_message"
        feedback_utils.print_when_true(input_string=input_string, do_print=True, use_system_write=False)
        result = mock_stdout.getvalue()
        expected = input_string + "\n"
        self.assertEqual(expected, result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_when_true_sys_write(self, mock_stdout):
        input_string = "mocked_message"
        feedback_utils.print_when_true(input_string=input_string, do_print=True, use_system_write=True)
        result = mock_stdout.getvalue()
        expected = input_string + "\n"
        self.assertEqual(expected, result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_when_true_false(self, mock_stdout):
        input_string = "mocked_message"
        feedback_utils.print_when_true(input_string=input_string, do_print=False, use_system_write=False)
        result = mock_stdout.getvalue()
        expected = ""
        self.assertEqual(expected, result)

    def test_redirect_output_to_function_info(self):
        # Create the MagicMock object
        process_func = MagicMock()

        # Define a dummy function to be decorated
        @redirect_output_to_function(process_func)
        def dummy_function():
            print("Hello, World!")
            logging.info("This is an info message.")

        dummy_function()

        expected_output = "Hello, World!\n"
        expected_logs = "This is an info message.\n"
        process_func.assert_called_with(expected_output, expected_logs)

    def test_redirect_output_to_function_debug(self):
        # Create the MagicMock object
        process_func = MagicMock()

        # Define a dummy function to be decorated
        @redirect_output_to_function(process_func, logger_level=logging.DEBUG)
        def dummy_function():
            print("Hello, World!")
            logging.debug("This is a debug message.")

        dummy_function()

        expected_output = "Hello, World!\n"
        expected_logs = "This is a debug message.\n"
        process_func.assert_called_with(expected_output, expected_logs)

    def test_redirect_output_to_function_no_log(self):
        # Create the MagicMock object
        process_func = MagicMock()

        # Define a dummy function to be decorated
        @redirect_output_to_function(process_func, logger_level=logging.INFO)
        def dummy_function():
            print("Hello, World!")
            logging.debug("This is a debug message.")

        dummy_function()

        expected_output = "Hello, World!\n"
        expected_logs = ""
        process_func.assert_called_with(expected_output, expected_logs)


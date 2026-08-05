"""
Sample Tool Model

This module contains the SampleToolModel class, which handles the data logic
for saving text to a file. This tool is intentionally small so it can be used
as a practical MVC example for new gt-tools tools.
"""

import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SampleToolModel:
    """Model used by the sample text saver tool."""

    def save_text_to_file(self, text, file_path):
        """Saves text to a specified file path.

        Args:
            text (str): Text content to save.
            file_path (str): Absolute path to the file.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(text)
            logger.info('Successfully saved text to: "%s"', file_path)
            return True
        except Exception as exception:
            logger.warning("Failed to save text. Issue: %s", exception)
            return False

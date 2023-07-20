"""
Naming Utilities
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_short_name(full_name):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)

    Args:
        full_name (string) - object to extract short name
    """
    output_short_name = ''
    if full_name == '':
        return ''
    split_path = full_name.split('|')
    if len(split_path) >= 1:
        output_short_name = split_path[len(split_path) - 1]
    return output_short_name

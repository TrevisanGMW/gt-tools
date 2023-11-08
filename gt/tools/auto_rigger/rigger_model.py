"""
Auto Rigger Model
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RiggerModel:
    def __init__(self):
        """
        Initialize the RiggerModel object.
        """
        self.project = None


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = RiggerModel()

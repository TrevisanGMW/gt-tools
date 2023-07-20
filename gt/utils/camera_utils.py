import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
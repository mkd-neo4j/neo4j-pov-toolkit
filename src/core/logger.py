"""
Pre-configured logging for the toolkit.
Provides clean, colorized output for user feedback.
"""

import logging
import sys

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout
)

log = logging.getLogger('neo4j-pov-toolkit')

# Usage in generated code:
# from src.core.logger import log
# log.info("Message")
# log.debug("Debug info")
# log.error("Error message")

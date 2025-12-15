"""
Pre-configured Logging Infrastructure for the Neo4j PoV Toolkit

Purpose:
    Provides a standardized, pre-configured logging system for the entire toolkit.
    This ensures consistent, readable output across all components - both the
    CLI commands and LLM-generated data mapper code.

Why This Module Exists:
    Instead of having each module configure its own logging, we centralize the
    configuration here. This gives us:
    - Consistent timestamp and message formatting
    - Single point of control for log levels
    - Clean, readable output for users watching ingestion progress
    - LLM-generated code can import and use immediately without configuration

Architecture Context:
    This is a foundational utility used by:
    - CLI commands (neo4j-test, neo4j-info, etc.)
    - Core functionality (query runner, version detection)
    - LLM-generated data mapper code (workspace/generated/*.py)

    The logger is intentionally simple - no file outputs, no rotation, no complex
    handlers. Just clean console output with timestamps.

Usage in Toolkit Code:
    from src.core.logger import log

    log.info("Connection successful")
    log.debug("Processing batch 5/20")
    log.warning("Missing optional field: phone")
    log.error("Failed to connect to Neo4j")

Usage in LLM-Generated Code:
    The LLM should instruct generated data_mapper.py files to import this logger:

    from src.core.logger import log

    def load_customers():
        log.info("Loading customer data from CSV...")
        # ... processing ...
        log.info(f"Created {count} Customer nodes")

Output Format:
    14:35:22 | INFO | Connection successful
    14:35:23 | DEBUG | Processing batch 5/20
    14:35:24 | ERROR | Failed to connect to Neo4j

Configuration:
    - Level: INFO (shows info, warning, error; hides debug)
    - Format: HH:MM:SS | LEVEL | message
    - Stream: stdout (not stderr, so output flows naturally)
    - Logger name: 'neo4j-pov-toolkit'
"""

import logging
import sys
import time


class ElapsedTimeFormatter(logging.Formatter):
    """
    Custom formatter that includes elapsed time since logger initialization.

    Format: HH:MM:SS | [+MM:SS] | LEVEL | message

    Example:
        08:03:00 | [+00:00] | INFO | Starting process...
        08:03:06 | [+00:06] | INFO | Progress update...
        08:08:30 | [+05:30] | INFO | More progress...
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()

    def format(self, record):
        # Calculate elapsed time
        elapsed_seconds = int(time.time() - self.start_time)
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60

        # Add elapsed time to the record
        record.elapsed = f"[{minutes:02d}:{seconds:02d}]"

        return super().format(record)


# Create our custom formatter with elapsed time tracking
formatter = ElapsedTimeFormatter(
    fmt='%(asctime)s | %(elapsed)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)

# Configure the handler with our custom formatter
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

# Create our toolkit-specific logger
# All toolkit code should import and use this 'log' instance
log = logging.getLogger('neo4j-pov-toolkit')
log.setLevel(logging.INFO)

# Guard against duplicate handlers on reimport (e.g., importlib.reload())
# Unlike logging.basicConfig() which is idempotent, manual addHandler() is not
if not log.handlers:
    log.addHandler(handler)

# Prevent propagation to avoid duplicate logs
log.propagate = False

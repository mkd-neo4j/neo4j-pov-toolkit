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

# Configure the root logging system with our standard format
# This runs once when the module is imported, establishing the format
# for all subsequent logging calls throughout the toolkit
logging.basicConfig(
    level=logging.INFO,  # Show INFO and above; use --debug flag to change to DEBUG
    format='%(asctime)s | %(levelname)s | %(message)s',  # Clean, parseable format
    datefmt='%H:%M:%S',  # Simple time format (no date needed for short-running operations)
    stream=sys.stdout  # Output to stdout for natural flow (not stderr)
)

# Create our toolkit-specific logger
# All toolkit code should import and use this 'log' instance
log = logging.getLogger('neo4j-pov-toolkit')

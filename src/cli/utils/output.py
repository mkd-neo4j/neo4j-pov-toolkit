"""
Output Formatting Utilities

Handles different output formats (JSON, table, etc.)
"""

import json


def format_as_json(data, indent=2):
    """Format data as JSON string"""
    return json.dumps(data, indent=indent)


def print_json(data, indent=2):
    """Print data as JSON"""
    print(format_as_json(data, indent=indent))

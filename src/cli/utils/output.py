"""
Output Format Utilities for CLI Commands

Purpose:
    Provides utilities for formatting and outputting data in different formats,
    primarily JSON for LLM-friendly output and programmatic consumption.

Why This Module Exists:
    CLI commands need to support two audiences:
    1. Human users - Want pretty, colored, formatted output
    2. LLMs and scripts - Want structured JSON output

    This module handles the second case, allowing commands to output JSON
    when the --json flag is used.

Used By:
    CLI commands that support --json flag:
    - neo4j-test (outputs connection info as JSON)
    - neo4j-info (outputs database info as JSON)
    - list-usecases (outputs use case hierarchy as JSON)

Design Pattern:
    Commands typically follow this pattern:

    def execute(args):
        # ... gather data ...

        if args.json:
            print_json(data)
            return 0

        # ... pretty format for humans ...

LLM Usage:
    When an LLM needs structured data from a CLI command, it should:
    1. Run the command with --json flag
    2. Parse stdout as JSON
    3. Use the structured data for decision-making

    Example:
        $ python cli.py neo4j-test --json
        {
          "connected": true,
          "neo4j_version": "6.0.3",
          "cypher_version": ["5", "25"],
          "enterprise": true,
          "config": {
            "uri": "neo4j://localhost:7687",
            "database": "neo4j",
            "user": "neo4j"
          }
        }
"""

import json


def format_as_json(data, indent=2):
    """
    Format Python data structures as a JSON string.

    Purpose:
        Converts Python dicts, lists, and primitives into pretty-printed JSON
        suitable for output or logging.

    Args:
        data: Any JSON-serializable Python data structure (dict, list, str, int, etc.)
        indent (int): Number of spaces for indentation (default 2)

    Returns:
        str: Formatted JSON string with indentation

    Example:
        data = {'connected': True, 'version': '6.0.3'}
        json_str = format_as_json(data)
        print(json_str)

        Output:
        {
          "connected": true,
          "version": "6.0.3"
        }

    Note:
        This is a wrapper around json.dumps() with sensible defaults for
        CLI output. Use this instead of calling json.dumps() directly for
        consistency across the toolkit.

    Raises:
        TypeError: If data contains non-JSON-serializable objects
    """
    return json.dumps(data, indent=indent)


def print_json(data, indent=2):
    """
    Print Python data structures as formatted JSON to stdout.

    Purpose:
        Primary output method for commands run with --json flag. Provides
        structured, parseable output suitable for LLMs and scripts.

    Args:
        data: Any JSON-serializable Python data structure
        indent (int): Number of spaces for indentation (default 2)

    Usage in Commands:
        from src.cli.utils.output import print_json

        def execute(args):
            # Gather data...
            info = get_neo4j_info()

            # Check if JSON output requested
            if args.json:
                print_json(info)
                return 0

            # Otherwise format for humans...

    Example:
        print_json({
            'connected': True,
            'neo4j_version': '6.0.3',
            'cypher_version': ['5', '25']
        })

        Output:
        {
          "connected": true,
          "neo4j_version": "6.0.3",
          "cypher_version": [
            "5",
            "25"
          ]
        }

    Why JSON Output Matters:
        - LLMs can easily parse JSON to understand system state
        - Scripts can process JSON without regex/text parsing
        - JSON is language-agnostic (works with Python, Node, etc.)
        - Structured data is more reliable than text parsing

    LLM Workflow:
        1. LLM runs: python cli.py neo4j-info --json
        2. Parses stdout as JSON
        3. Extracts neo4j_version field
        4. Makes decisions based on version
        5. Generates appropriate code

    Note:
        Always output JSON to stdout (not stderr) so it can be captured and
        parsed by calling scripts or LLMs.

    Raises:
        TypeError: If data contains non-JSON-serializable objects
    """
    print(format_as_json(data, indent=indent))

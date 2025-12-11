"""
neo4j-test CLI Command - Quick Connection Validation

Purpose:
    Provides a fast, user-friendly way to validate that the Neo4j database connection is working before
    attempting data loading operations. First command users should run after configuration.

Command Usage:
    python cli.py neo4j-test                 # Quick test with minimal output
    python cli.py neo4j-test --verbose       # Detailed version information
    python cli.py neo4j-test --json          # Machine-readable output for LLMs

When LLMs Should Run This:
    - After user creates/updates .env file
    - Before generating data mapper code
    - When troubleshooting connection issues
    - As a prerequisite check before other operations

What It Tests:
    ✓ Can read .env file
    ✓ Can establish connection to Neo4j
    ✓ Credentials are valid
    ✓ Database is accessible
    ✓ Can query database version

Return Codes:
    0 - Connection successful
    1 - Connection failed (check output for details)
"""

import os
from dotenv import load_dotenv
from ...utils.formatting import print_box, print_success, print_error, print_info, Colors
from ...utils.output import print_json
from ....core.neo4j.version import get_neo4j_info


def execute(args):
    """
    Execute the neo4j-test command to validate database connectivity.

    Loads credentials from .env, attempts connection, and reports results in either
    human-friendly or JSON format based on command-line flags.

    Args:
        args: Parsed command-line arguments with attributes:
              - json (bool): Output as JSON instead of formatted text
              - verbose (bool): Show detailed version information

    Returns:
        int: Exit code - 0 for success, 1 for failure

    Behavior:
        1. Loads .env file credentials
        2. Displays connection test header box
        3. Calls get_neo4j_info() to attempt connection
        4. Formats and displays results based on --json or --verbose flags
        5. Provides helpful next steps on failure
    """
    load_dotenv()

    print_box("Neo4j Connection Test")

    # Get non-sensitive configuration
    uri = os.getenv('NEO4J_URI', 'Not configured')
    database = os.getenv('NEO4J_DATABASE', 'neo4j')
    user = os.getenv('NEO4J_USER', 'Not configured')

    print(f"{Colors.DIM}Testing connection to Neo4j...{Colors.RESET}\n")

    info = get_neo4j_info()

    # Add config info to response
    config_info = {
        'uri': uri,
        'database': database,
        'user': user
    }

    # JSON output
    if args.json:
        output = {**info, 'config': config_info}
        print_json(output)
        return 0 if info.get('connected') else 1

    # Pretty formatted output
    if info.get('connected'):
        print_success("Connection successful!\n")

        # Show configuration details
        print_info("URI", uri)
        print_info("Database", database)
        print_info("User", user)
        print()

        if args.verbose:
            print_info("Neo4j Version", info['neo4j_version'])
            print_info("Cypher Versions", ", ".join(info['cypher_version']))
            print_info("Edition", "Enterprise" if info['enterprise'] else "Community")
        else:
            print(f"{Colors.DIM}Connected to: Neo4j {info['neo4j_version']} ({'Enterprise' if info['enterprise'] else 'Community'}){Colors.RESET}\n")

        return 0
    else:
        print_error("Connection failed!\n")

        # Show what config was attempted
        print_info("URI", uri)
        print_info("Database", database)
        print_info("User", user)
        print()

        print(f"{Colors.DIM}Error: {info.get('error', 'Unknown error')}{Colors.RESET}\n")
        return 1


def setup_parser(subparsers):
    """Setup argument parser for neo4j-test command"""
    parser = subparsers.add_parser(
        'neo4j-test',
        help='Validate Neo4j database connection using credentials from .env file'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON format instead of formatted text'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed version and configuration information'
    )
    parser.set_defaults(func=execute)
    return parser

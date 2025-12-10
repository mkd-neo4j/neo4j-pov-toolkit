"""
neo4j-test command

Test Neo4j database connection.
"""

import os
from dotenv import load_dotenv
from ...utils.formatting import print_box, print_success, print_error, print_info, Colors
from ...utils.output import print_json
from ....core.neo4j.version import get_neo4j_info


def execute(args):
    """Execute neo4j-test command"""
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

        print(f"{Colors.YELLOW}Next steps:{Colors.RESET}")
        print("  1. Create .env file: cp .env.example .env")
        print("  2. Edit .env with your Neo4j credentials")
        print("  3. Run this test again\n")
        return 1


def setup_parser(subparsers):
    """Setup argument parser for neo4j-test command"""
    parser = subparsers.add_parser(
        'neo4j-test',
        help='Test Neo4j database connection'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed connection information'
    )
    parser.set_defaults(func=execute)
    return parser

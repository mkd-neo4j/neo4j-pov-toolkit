"""
neo4j-info command

Show comprehensive Neo4j connection information.
"""

import os
from ...utils.formatting import print_box, print_success, print_error, print_info, Colors
from ...utils.output import print_json
from ....core.neo4j.version import get_neo4j_info


def execute(args):
    """Execute neo4j-info command"""
    info = get_neo4j_info()

    # JSON output
    if args.json:
        # Add connection details to JSON output
        info_extended = info.copy()
        info_extended['uri'] = os.getenv('NEO4J_URI', 'Not set')
        info_extended['database'] = os.getenv('NEO4J_DATABASE', 'neo4j')
        print_json(info_extended)
        return 0 if info.get('connected') else 1

    # Pretty formatted output
    print_box("Neo4j Connection Information")

    if not info.get('connected'):
        print_error("Failed to connect to Neo4j")
        print(f"\n{Colors.DIM}Error: {info.get('error', 'Unknown error')}{Colors.RESET}\n")

        print(f"{Colors.YELLOW}Troubleshooting:{Colors.RESET}")
        print("  1. Ensure Neo4j is running")
        print("  2. Check your .env file exists and has correct credentials")
        print("  3. Verify NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD are set\n")
        return 1

    print_success("Connected\n")

    print_info("Neo4j Version", info['neo4j_version'])
    print_info("Cypher Versions", ", ".join(info['cypher_version']))
    print_info("Edition", "Enterprise" if info['enterprise'] else "Community")
    print_info("URI", os.getenv('NEO4J_URI', 'Not set'))
    print_info("Database", os.getenv('NEO4J_DATABASE', 'neo4j'))

    print(f"\n{Colors.GREEN}Ready to generate ingestion code!{Colors.RESET}\n")
    return 0


def setup_parser(subparsers):
    """Setup argument parser for neo4j-info command"""
    parser = subparsers.add_parser(
        'neo4j-info',
        help='Display detailed Neo4j connection and version information'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON format instead of formatted text'
    )
    parser.set_defaults(func=execute)
    return parser

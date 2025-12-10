"""
Neo4j Demo Toolkit - Main CLI Logic

Handles argument parsing, command routing, and global flags.
"""

import sys
import argparse
from .utils.formatting import Colors
from .commands.neo4j import test_setup_parser, info_setup_parser


# Toolkit version
VERSION = "0.1.0"


def main():
    """Main CLI entry point"""

    # Handle global --version flag before argument parsing
    if '--version' in sys.argv:
        print(f"Neo4j Demo Toolkit v{VERSION}")
        return 0

    # Create main parser
    parser = argparse.ArgumentParser(
        description='Neo4j Demo Toolkit - Generate Neo4j ingestion code from your data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.BOLD}Commands:{Colors.RESET}
  {Colors.CYAN}neo4j-test{Colors.RESET}          Test Neo4j database connection
  {Colors.CYAN}neo4j-info{Colors.RESET}          Show comprehensive Neo4j information

{Colors.BOLD}Examples:{Colors.RESET}
  python cli.py neo4j-test                 Test connection
  python cli.py neo4j-test --verbose       Detailed test
  python cli.py neo4j-info                 Full connection info

{Colors.BOLD}Getting Started:{Colors.RESET}
  1. Create .env file: {Colors.CYAN}cp .env.example .env{Colors.RESET}
  2. Edit .env with your Neo4j credentials
  3. Test connection: {Colors.CYAN}python cli.py neo4j-test{Colors.RESET}
  4. Start conversation with Claude Code or Cursor
        """
    )

    # Add global version flag
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show toolkit version'
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands'
    )

    # Register commands
    test_setup_parser(subparsers)
    info_setup_parser(subparsers)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.RESET}\n")
        return 130
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.RESET} Unexpected error: {e}")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

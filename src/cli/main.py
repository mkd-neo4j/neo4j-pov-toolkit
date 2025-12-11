"""
Neo4j PoV Toolkit - Main CLI Logic

Handles argument parsing, command routing, and global flags.
"""

import sys
import argparse
from .utils.formatting import Colors
from .commands.neo4j import test_setup_parser, info_setup_parser
from .commands.usecases import setup_parser as usecases_setup_parser


# Toolkit version
VERSION = "0.1.0"


def main():
    """Main CLI entry point"""

    # Handle global --version flag before argument parsing
    if '--version' in sys.argv:
        print(f"Neo4j PoV Toolkit v{VERSION}")
        return 0

    # Create main parser
    parser = argparse.ArgumentParser(
        description='Neo4j PoV Toolkit - Generate Neo4j ingestion code from your data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.BOLD}Commands:{Colors.RESET}
  {Colors.CYAN}neo4j-test{Colors.RESET} [--json] [--verbose]
      Validate Neo4j database connection using credentials from .env file
      Options:
        --json      Output as JSON format
        --verbose   Show detailed version information

  {Colors.CYAN}neo4j-info{Colors.RESET} [--json]
      Display detailed Neo4j connection and version information
      Options:
        --json      Output as JSON format

  {Colors.CYAN}list-usecases{Colors.RESET} [--json] [--urls-only] [--verbose]
      List all available Neo4j use cases by scraping neo4j.com/use-cases
      Options:
        --json        Output as JSON format
        --urls-only   Output only URLs (for LLM/scripting)
        --verbose     Show URLs in tree view

  {Colors.CYAN}get-usecase{Colors.RESET} <URL> [--output FILE]
      Fetch a Neo4j use case page from neo4j.com and convert to markdown
      Required:
        URL           Full Neo4j use case page URL (e.g., https://neo4j.com/use-cases/fraud-detection/)
      Options:
        --output, -o  Save to file instead of stdout

  {Colors.CYAN}list-datamodels{Colors.RESET} [--json] [--urls-only] [--verbose]
      List all available Neo4j data models by scraping neo4j.com/developer/industry-use-cases
      Options:
        --json        Output as JSON format
        --urls-only   Output only URLs (for LLM/scripting)
        --verbose     Show URLs in tree view

  {Colors.CYAN}get-datamodel{Colors.RESET} <URL> [--output FILE]
      Fetch a Neo4j data model page from neo4j.com and convert to markdown
      Required:
        URL           Full Neo4j data model page URL
      Options:
        --output, -o  Save to file instead of stdout

{Colors.BOLD}Examples:{Colors.RESET}
  python cli.py neo4j-test                                    Test connection
  python cli.py neo4j-test --verbose                          Detailed test
  python cli.py neo4j-info                                    Full connection info
  python cli.py list-usecases                                 Show use case hierarchy
  python cli.py list-usecases --urls-only                     Get URLs for LLM
  python cli.py get-usecase https://neo4j.com/use-cases/...   Fetch use case as markdown
  python cli.py get-usecase <URL> -o usecase.md               Save to file
  python cli.py list-datamodels                               Show data model hierarchy
  python cli.py list-datamodels --urls-only                   Get data model URLs for LLM
  python cli.py get-datamodel <URL> -o datamodel.md           Fetch data model as markdown

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
    usecases_setup_parser(subparsers)

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

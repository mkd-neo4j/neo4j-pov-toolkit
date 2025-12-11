"""
get-usecase command

Fetch a Neo4j use case page and convert it to markdown format.
"""

from ...utils.formatting import print_box, print_error, Colors
from ....core.web_utils import fetch_page_as_markdown


def execute(args):
    """Execute get-usecase command"""

    url = args.url

    print_box("Fetching Use Case")
    print(f"{Colors.DIM}URL: {url}{Colors.RESET}\n")

    # Fetch and convert the page
    markdown = fetch_page_as_markdown(url)

    if markdown is None:
        print_error("Failed to fetch or convert the page")
        print(f"\n{Colors.DIM}Please check the URL and your internet connection.{Colors.RESET}\n")
        return 1

    # Output to file or stdout
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"{Colors.GREEN}✓{Colors.RESET} Successfully saved to: {Colors.BOLD}{args.output}{Colors.RESET}\n")
            return 0
        except Exception as e:
            print_error(f"Failed to write to file: {e}")
            return 1
    else:
        # Output to stdout
        print(markdown)
        return 0


def setup_parser(subparsers):
    """Setup argument parser for get-usecase command"""
    parser = subparsers.add_parser(
        'get-usecase',
        help='Fetch a Neo4j use case page from neo4j.com and convert it to markdown format'
    )
    parser.add_argument(
        'url',
        help='Full URL of the Neo4j use case page (e.g., https://neo4j.com/use-cases/fraud-detection/)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Save markdown to file instead of printing to stdout (e.g., usecase.md)'
    )
    parser.set_defaults(func=execute)
    return parser

"""
get-datamodel CLI Command - Data Model Documentation Fetcher

Purpose:
    Fetches a specific Neo4j data model page from neo4j.com and converts it to clean markdown format.
    This markdown can then be read by LLMs to understand the graph schema, relationships, and properties
    needed to implement the data model.

Command Usage:
    python cli.py get-datamodel <URL>                        # Print to stdout
    python cli.py get-datamodel <URL> -o model.md            # Save to file

When LLMs Should Use This:
    - After running list-datamodels to get available URLs
    - When user wants to implement a specific data model
    - When generating ingestion code that follows a standard schema
    - To understand node labels, relationship types, and property structures

Use Cases:
    1. LLM reads markdown to understand the data model schema
    2. LLM maps user's data to the canonical schema
    3. LLM generates Cypher CREATE statements matching the model
    4. User gets code that follows Neo4j best practices

Why Markdown?
    - LLMs process text better than HTML
    - Removes navigation, ads, and irrelevant content
    - Preserves structure (headings, lists, code blocks)
    - Lightweight and easy to parse

Return Codes:
    0 - Successfully fetched and converted page
    1 - Failed (invalid URL, network error, conversion error)
"""

from ...utils.formatting import print_box, print_error, Colors
from ....core.web_utils import fetch_page_as_markdown


def execute(args):
    """Execute get-datamodel command"""

    url = args.url

    print_box("Fetching Data Model")
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
    """Setup argument parser for get-datamodel command"""
    parser = subparsers.add_parser(
        'get-datamodel',
        help='Fetch a Neo4j data model page from neo4j.com and convert it to markdown format'
    )
    parser.add_argument(
        'url',
        help='Full URL of the Neo4j data model page (e.g., https://neo4j.com/developer/industry-use-cases/data-models/fraud-detection/)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Save markdown to file instead of printing to stdout (e.g., datamodel.md)'
    )
    parser.set_defaults(func=execute)
    return parser

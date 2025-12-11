"""
get-usecase CLI Command - Use Case Documentation Fetcher

Purpose:
    Fetches a specific Neo4j use case page from neo4j.com and converts it to clean markdown format.
    This markdown can then be read by LLMs to understand the business problem, recommended data model,
    and implementation approach for that specific use case.

Command Usage:
    python cli.py get-usecase <URL>                          # Print to stdout
    python cli.py get-usecase <URL> -o usecase.md            # Save to file

When LLMs Should Use This:
    - After running list-usecases to get available URLs
    - When user's problem matches a specific industry use case
    - To understand the recommended data model for a use case
    - To get example queries and patterns for implementation

Use Cases:
    1. LLM reads markdown to understand the business problem
    2. LLM identifies the recommended data model referenced in the use case
    3. LLM may fetch that data model for detailed schema information
    4. LLM generates code that implements the use case pattern

What's in a Use Case Page?
    - Business problem description
    - Industry context and challenges
    - Recommended graph data model (often links to data model docs)
    - Example queries and patterns
    - Benefits of the graph approach

Why Markdown?
    - LLMs process text better than HTML
    - Removes navigation, ads, and irrelevant content
    - Preserves structure (headings, lists, code blocks)
    - Lightweight and easy to parse

Workflow Example:
    1. User: "I need to detect fraud in banking transactions"
    2. LLM: list-usecases --urls-only → finds fraud detection URL
    3. LLM: get-usecase <fraud-url> → reads problem description
    4. LLM: Sees reference to "Transaction Graph" data model
    5. LLM: get-datamodel <transaction-graph-url> → gets schema
    6. LLM: Generates code following the use case + data model

Return Codes:
    0 - Successfully fetched and converted page
    1 - Failed (invalid URL, network error, conversion error)
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

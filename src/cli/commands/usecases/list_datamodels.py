"""
list-datamodels CLI Command - Data Model Discovery

Purpose:
    Lists all available Neo4j data models from the official Neo4j website. Data models are
    reusable graph schemas that represent common patterns (like transactions, fraud detection, etc.)
    that can be applied across different use cases and industries.

Command Usage:
    python cli.py list-datamodels                    # Pretty tree view
    python cli.py list-datamodels --json             # JSON output for programmatic use
    python cli.py list-datamodels --urls-only        # Just URLs, one per line
    python cli.py list-datamodels --verbose          # Show URLs in tree view

When LLMs Should Use This:
    - When user asks "what data models are available?"
    - When exploring reusable graph schemas
    - To get URLs for fetching specific data model documentation
    - When the user needs a canonical data model for their domain

Output Modes:
    1. Tree View (default): Hierarchical display with colors
       - Shows categories and individual data models
       - Color-coded by level (category vs. data model)
    2. JSON: Machine-readable hierarchical structure
    3. URLs Only: Flat list of URLs for feeding to LLMs or scripts

Difference from Use Cases:
    - Use Cases: Industry-specific problem scenarios (e.g., "Fraud Detection in Banking")
    - Data Models: Generic graph schemas that can be reused (e.g., "Transaction Graph")
    - Data models are referenced BY use cases but are more abstract and reusable

Return Codes:
    0 - Successfully fetched and displayed data models
    1 - Failed to fetch from website (network error, parsing error)
"""

import json
from ...utils.formatting import print_box, print_error, Colors
from ....core.usecases import scrape_data_models, get_all_data_model_urls, UseCaseNode


def execute(args):
    """Execute list-datamodels command"""

    print_box("Neo4j Data Models")
    print(f"{Colors.DIM}Fetching data models from neo4j.com...{Colors.RESET}\n")

    # Scrape the data models
    root = scrape_data_models()

    if root is None:
        print_error("Failed to fetch data models from the website")
        print(f"\n{Colors.DIM}Please check your internet connection and try again.{Colors.RESET}\n")
        return 1

    # URLs only mode - for feeding to LLM
    if args.urls_only:
        urls = get_all_data_model_urls(root)
        # Skip the root URL
        urls = [url for url in urls if url != root.url]

        if args.json:
            print(json.dumps({"urls": urls}, indent=2))
        else:
            for url in urls:
                print(url)
        return 0

    # JSON output mode
    if args.json:
        output = root.to_dict()
        print(json.dumps(output, indent=2))
        return 0

    # Default: Pretty tree output
    print(f"{Colors.BOLD}Available Data Models:{Colors.RESET}\n")
    _print_tree_markdown(root, show_urls=args.verbose)

    # Summary
    urls = get_all_data_model_urls(root)

    print(f"\n{Colors.DIM}Total data model pages: {len(urls) - 1}{Colors.RESET}")  # -1 for root
    print(f"\n{Colors.CYAN}Tip:{Colors.RESET} Use {Colors.BOLD}--urls-only{Colors.RESET} to get a list of URLs for the LLM\n")

    return 0


def _print_tree_markdown(node: UseCaseNode, indent: int = 0, show_urls: bool = False):
    """
    Print the data model tree in markdown format without icons

    Args:
        node: The node to print
        indent: Current indentation level
        show_urls: Whether to show URLs (ignored, URLs always shown for leaf nodes)
    """
    if node.level >= 0:  # Skip root node
        prefix = "  " * indent

        # Different colors for different levels
        if node.level == 0:
            color = Colors.CYAN
            marker = "-"
        elif node.level == 1:
            color = Colors.YELLOW
            marker = "-"
        else:
            color = Colors.GREEN
            marker = "-"

        # Check if this is a leaf node (no children = actual data model)
        is_leaf = len(node.children) == 0

        if is_leaf:
            # Leaf nodes: show name with URL on same line
            print(f"{prefix}{marker} {color}{node.name}{Colors.RESET} - {node.url}")
        else:
            # Non-leaf nodes: just show the name
            name_display = f"{prefix}{marker} {color}{node.name}{Colors.RESET}"
            print(name_display)

    for child in node.children:
        _print_tree_markdown(child, indent + 1, show_urls)


def setup_parser(subparsers):
    """Setup argument parser for list-datamodels command"""
    parser = subparsers.add_parser(
        'list-datamodels',
        help='List all available Neo4j data models by scraping neo4j.com/developer/industry-use-cases'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON format instead of tree view'
    )
    parser.add_argument(
        '--urls-only',
        action='store_true',
        help='Output only URLs, one per line (useful for passing to LLM or scripting)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show URLs alongside data model names in tree view'
    )
    parser.set_defaults(func=execute)
    return parser

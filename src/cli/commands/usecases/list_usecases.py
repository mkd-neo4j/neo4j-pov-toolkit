"""
list-usecases command

List Neo4j use cases from the website in various formats.
"""

import json
from ...utils.formatting import print_box, print_error, Colors
from ....core.usecases import scrape_use_cases, get_all_use_case_urls, UseCaseNode


def execute(args):
    """Execute list-usecases command"""

    print_box("Neo4j Use Cases")
    print(f"{Colors.DIM}Fetching use cases from neo4j.com...{Colors.RESET}\n")

    # Scrape the use cases
    root = scrape_use_cases()

    if root is None:
        print_error("Failed to fetch use cases from the website")
        print(f"\n{Colors.DIM}Please check your internet connection and try again.{Colors.RESET}\n")
        return 1

    # URLs only mode - for feeding to LLM
    if args.urls_only:
        urls = get_all_use_case_urls(root)
        # Skip the root URL
        urls = [url for url in urls if 'industry-use-cases/' in url and not url.endswith('industry-use-cases/')]

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
    print(f"{Colors.BOLD}Available Use Cases:{Colors.RESET}\n")
    _print_tree_markdown(root, show_urls=args.verbose)

    # Summary
    urls = get_all_use_case_urls(root)

    print(f"\n{Colors.DIM}Total industries: {len(root.children)}{Colors.RESET}")
    print(f"{Colors.DIM}Total use case pages: {len(urls) - 1}{Colors.RESET}")  # -1 for root
    print(f"\n{Colors.CYAN}Tip:{Colors.RESET} Use {Colors.BOLD}--urls-only{Colors.RESET} to get a list of URLs for the LLM\n")

    return 0


def _print_tree_markdown(node: UseCaseNode, indent: int = 0, show_urls: bool = False):
    """
    Print the use case tree in markdown format without icons

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

        # Check if this is a leaf node (no children = actual use case)
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
    """Setup argument parser for list-usecases command"""
    parser = subparsers.add_parser(
        'list-usecases',
        help='List all available Neo4j use cases by scraping neo4j.com/use-cases'
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
        help='Show URLs alongside use case names in tree view'
    )
    parser.set_defaults(func=execute)
    return parser

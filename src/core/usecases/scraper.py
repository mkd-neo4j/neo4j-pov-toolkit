"""
Neo4j Use Case Hierarchy Scraper

Purpose:
    Scrapes the Neo4j Industry Use Cases website and builds a hierarchical
    data structure representing all available use cases organized by industry
    and subcategory.

Why This Module Exists:
    The LLM needs to know what use cases are available so it can:
    1. Show users what patterns they can leverage
    2. Guide users to the right use case for their problem
    3. Fetch specific use case documentation when generating code

    Instead of hard-coding use case lists, we scrape the live website to always
    have the latest use cases as Neo4j adds new ones.

Architecture Context:
    This is part of the use case discovery system:
    1. This scraper builds the hierarchy of use cases (industries → subcategories → use cases)
    2. list-usecases CLI command displays the hierarchy or outputs URLs
    3. LLM uses URLs to fetch specific use case pages via web_utils.py
    4. LLM reads use case markdown to understand data models
    5. LLM generates appropriate ingestion code

Data Structure:
    Builds a tree structure:
    Root
    ├── Financial Services (Industry)
    │   ├── Retail Banking (Subcategory)
    │   │   ├── Synthetic Identity Fraud (Use Case)
    │   │   └── Account Takeover Fraud (Use Case)
    │   └── Investment Banking (Subcategory)
    │       └── Mutual Fund Dependency Analytics (Use Case)
    └── Insurance (Industry)
        ├── Claims Fraud (Use Case)
        └── Quote Fraud (Use Case)

Key Components:
    - UseCaseNode: Dataclass representing a node in the hierarchy
    - scrape_use_cases(): Main function that builds the tree
    - get_all_use_case_urls(): Flattens tree into list of URLs

Used By:
    - list-usecases CLI command
    - LLM when discovering available use cases
    - Any code that needs the use case catalog
"""

from dataclasses import dataclass, field
from typing import List, Optional
import requests
from bs4 import BeautifulSoup


@dataclass
class UseCaseNode:
    """Represents a node in the use case hierarchy"""
    name: str
    url: str
    level: int  # 0=industry, 1=subcategory, 2=use case
    children: List['UseCaseNode'] = field(default_factory=list)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'url': self.url,
            'level': self.level,
            'children': [child.to_dict() for child in self.children]
        }

    def get_all_urls(self) -> List[str]:
        """Recursively get all URLs from this node and its children"""
        urls = [self.url]
        for child in self.children:
            urls.extend(child.get_all_urls())
        return urls


def scrape_use_cases(base_url: str = "https://neo4j.com/developer/industry-use-cases/") -> Optional[UseCaseNode]:
    """
    Scrape the Neo4j use cases page and build a hierarchical structure

    Args:
        base_url: The URL of the use cases page

    Returns:
        Root UseCaseNode containing the entire hierarchy, or None on error
    """
    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Create root node
        root = UseCaseNode(
            name="Neo4j Industry Use Cases",
            url=base_url,
            level=-1
        )

        # Extract industries and their hierarchies from the navigation menu
        industries = _extract_industries(soup, base_url)
        root.children = industries

        return root

    except requests.RequestException as e:
        print(f"Error fetching use cases: {e}")
        return None
    except Exception as e:
        print(f"Error parsing use cases: {e}")
        return None


def _extract_industries(soup: BeautifulSoup, base_url: str) -> List[UseCaseNode]:
    """Extract industry nodes from the page by parsing the navigation menu"""
    from urllib.parse import urljoin

    # Find the navigation menu
    nav = soup.find('nav', class_='nav-menu')
    if not nav:
        return []

    # Find all nav items
    nav_items = nav.find_all('li', class_='nav-item')

    # Build a hierarchy using a stack to track parents at each depth
    industries = []
    depth_stack = {}  # depth -> current node at that depth

    for item in nav_items:
        # Get depth from data attribute
        depth_str = item.get('data-depth', '0')
        try:
            depth = int(depth_str)
        except (ValueError, TypeError):
            continue

        # Skip root level (depth 0)
        if depth == 0:
            continue

        # Find the link in this item (direct child only, not nested)
        link = item.find('a', class_='nav-link', recursive=False)
        if not link:
            continue

        name = link.get_text(strip=True)
        href = link.get('href', '')

        # If we hit "Whitepapers" or "Data Models" at depth 1, stop processing entirely
        if depth == 1 and name in {'Whitepapers', 'Data Models'}:
            break

        # Skip section headers, overview, and items with no meaningful href
        if not href or href == './' or name == 'Overview' or name.startswith('Neo4j Industry'):
            continue

        # Convert relative URL to absolute
        full_url = urljoin(base_url, href)

        # Determine level: depth 1 = industry (level 0), depth 2 = subcategory (level 1), depth 3+ = use case (level 2)
        level = depth - 1

        # Create the node
        node = UseCaseNode(
            name=name,
            url=full_url,
            level=level
        )

        # Add to appropriate parent
        if level == 0:
            # This is an industry (top level)
            industries.append(node)
            depth_stack[depth] = node
        elif depth > 1:
            # This is a child of the previous level
            parent_depth = depth - 1
            if parent_depth in depth_stack:
                depth_stack[parent_depth].children.append(node)
                depth_stack[depth] = node

    return industries


def get_all_use_case_urls(root: Optional[UseCaseNode] = None) -> List[str]:
    """
    Get a flat list of all use case URLs

    Args:
        root: Root node (if None, will scrape fresh)

    Returns:
        List of all URLs in the hierarchy
    """
    if root is None:
        root = scrape_use_cases()
        if root is None:
            return []

    return root.get_all_urls()

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


def scrape_data_models(base_url: str = "https://neo4j.com/developer/industry-use-cases/") -> Optional[UseCaseNode]:
    """
    Scrape the Neo4j data models section and build a hierarchical structure

    Purpose:
        Extracts the "Data Models" section from the Neo4j website, which contains
        reusable graph schemas that can be applied across different use cases and industries.
        Unlike use cases (which are industry/problem-specific), data models are abstract
        patterns like "Transaction Graph" or "Knowledge Graph".

    How It Differs from scrape_use_cases():
        - scrape_use_cases(): Extracts everything BEFORE "Data Models" section
        - scrape_data_models(): Extracts everything WITHIN "Data Models" section
        - Both use the same navigation menu but filter differently

    Data Model Hierarchy:
        Root
        ├── Transaction Graph (Category)
        │   ├── Base Model (Data Model)
        │   └── Fraud Event Sequence (Data Model)
        └── Knowledge Graph (Category)
            └── Entity Resolution (Data Model)

    Args:
        base_url: The URL of the use cases page (data models are a subsection)

    Returns:
        Root UseCaseNode containing the data models hierarchy, or None on error

    Used By:
        - list-datamodels CLI command
        - LLMs discovering available graph schemas
        - Code generation that needs to follow standard models
    """
    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Create root node
        root = UseCaseNode(
            name="Neo4j Data Models",
            url=base_url,
            level=-1
        )

        # Extract data models from the navigation menu
        data_models = _extract_data_models(soup, base_url)
        root.children = data_models

        return root

    except requests.RequestException as e:
        print(f"Error fetching data models: {e}")
        return None
    except Exception as e:
        print(f"Error parsing data models: {e}")
        return None


def _extract_data_models(soup: BeautifulSoup, base_url: str) -> List[UseCaseNode]:
    """
    Extract data model nodes from the page by parsing the navigation menu

    Purpose:
        Scans through the navigation menu and extracts only items within the "Data Models"
        section. Uses a flag-based approach to know when we've entered the section.

    Algorithm:
        1. Iterate through all navigation items
        2. When we hit "Data Models" at depth 1, set flag in_data_models=True
        3. Collect all items until we hit another depth 1 item (exit section)
        4. Build hierarchy: depth 2 = categories, depth 3+ = individual models

    Why Flag-Based?
        The navigation menu is flat HTML with depth markers. We need state tracking
        to know when we're "inside" the Data Models section vs. Use Cases section.

    Depth Mapping:
        - depth 1: Top-level sections (Use Cases, Data Models, Whitepapers)
        - depth 2: Categories within Data Models (Transaction Graph, etc.)
        - depth 3+: Individual data models

    Contrast with _extract_industries():
        - _extract_industries: STOPS when it sees "Data Models"
        - _extract_data_models: STARTS when it sees "Data Models"

    Args:
        soup: BeautifulSoup object of the page
        base_url: Base URL for converting relative links

    Returns:
        List of UseCaseNode objects representing data model categories and models
    """
    from urllib.parse import urljoin

    # Find the navigation menu
    nav = soup.find('nav', class_='nav-menu')
    if not nav:
        return []

    # Find all nav items
    nav_items = nav.find_all('li', class_='nav-item')

    # Track whether we've entered the Data Models section
    in_data_models = False
    data_models = []
    depth_stack = {}  # depth -> current node at that depth

    for item in nav_items:
        # Get depth from data attribute
        depth_str = item.get('data-depth', '0')
        try:
            depth = int(depth_str)
        except (ValueError, TypeError):
            continue

        # Find the link in this item (direct child only, not nested)
        link = item.find('a', class_='nav-link', recursive=False)
        if not link:
            continue

        name = link.get_text(strip=True)
        href = link.get('href', '')

        # Check if we've entered the Data Models section
        if depth == 1 and name == 'Data Models':
            in_data_models = True
            continue  # Skip the Data Models header itself

        # If we've entered Data Models section, process items until we hit another depth 1 item
        if in_data_models:
            # If we hit another depth 1 item, we've left the Data Models section
            if depth == 1:
                break

            # Skip items with no meaningful href
            if not href or href == './' or name == 'Overview':
                continue

            # Convert relative URL to absolute
            full_url = urljoin(base_url, href)

            # Determine level: depth 2 = category (level 0), depth 3+ = data model (level 1+)
            level = depth - 2

            # Create the node
            node = UseCaseNode(
                name=name,
                url=full_url,
                level=level
            )

            # Add to appropriate parent
            if level == 0:
                # This is a top-level data model or category
                data_models.append(node)
                depth_stack[depth] = node
            elif depth > 2:
                # This is a child of the previous level
                parent_depth = depth - 1
                if parent_depth in depth_stack:
                    depth_stack[parent_depth].children.append(node)
                    depth_stack[depth] = node

    return data_models


def get_all_data_model_urls(root: Optional[UseCaseNode] = None) -> List[str]:
    """
    Get a flat list of all data model URLs

    Purpose:
        Flattens the hierarchical data model tree into a simple list of URLs.
        Useful for LLMs that need to iterate through all available models.

    Usage Pattern:
        # Get all URLs for batch processing
        urls = get_all_data_model_urls()
        for url in urls:
            markdown = fetch_page_as_markdown(url)
            # Process each data model...

    Args:
        root: Root node (if None, will scrape fresh from website)

    Returns:
        List of all URLs in the hierarchy, including category pages and individual models

    Note:
        Callers typically filter out the root URL and category URLs to get only
        the individual data model URLs (leaf nodes).
    """
    if root is None:
        root = scrape_data_models()
        if root is None:
            return []

    return root.get_all_urls()

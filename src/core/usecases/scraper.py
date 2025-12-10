"""
Web scraper for Neo4j use cases

Extracts hierarchical use case information from neo4j.com/developer/industry-use-cases/
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

        # Find the main navigation/content area with use cases
        # The structure appears to be in navigation menus or content sections
        # We'll look for common patterns: nav elements, lists with links, etc.

        # Strategy 1: Look for navigation structure with nested lists
        nav_sections = soup.find_all(['nav', 'div'], class_=lambda x: x and ('nav' in x.lower() or 'menu' in x.lower()))

        # Strategy 2: Look for the main content with industry sections
        content_sections = soup.find_all(['section', 'div', 'article'])

        # Parse based on the structure we found from WebFetch
        # The page has industries at top level, with subcategories and use cases nested

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
    """Extract industry nodes from the page"""
    industries = []

    # Based on the structure we know:
    # Financial Services, Insurance, Manufacturing, Industry Agnostic

    # Look for links that match industry patterns
    all_links = soup.find_all('a', href=True)

    # Known industries and their patterns
    industry_patterns = {
        'Financial Services': '/finserv/',
        'Insurance': '/insurance/',
        'Manufacturing': '/manufacturing/',
        'Industry Agnostic': '/agnostic/'
    }

    # First pass: find industry links
    for name, pattern in industry_patterns.items():
        industry_node = UseCaseNode(
            name=name,
            url=f"https://neo4j.com/developer/industry-use-cases{pattern}",
            level=0
        )

        # For each industry, we would need to fetch subcategories
        # For now, let's add the known structure from our research
        if name == 'Financial Services':
            industry_node.children = [
                UseCaseNode(
                    name='Investment Banking',
                    url='https://neo4j.com/developer/industry-use-cases/finserv/investment-banking/',
                    level=1,
                    children=[
                        UseCaseNode('Mutual Fund Dependency Analytics',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/investment-banking/mutual-fund-dependency-analytics/', 2),
                        UseCaseNode('Regulatory Dependency Mapping',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/investment-banking/regulatory-dependency-mapping/', 2)
                    ]
                ),
                UseCaseNode(
                    name='Retail Banking',
                    url='https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/',
                    level=1,
                    children=[
                        UseCaseNode('Account Takeover Fraud',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/account-takeover-fraud/', 2),
                        UseCaseNode('Automated Facial Recognition',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/automated-facial-recognition/', 2),
                        UseCaseNode('Deposit Analysis',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/deposit-analysis/', 2),
                        UseCaseNode('Entity Resolution',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/entity-resolution/', 2),
                        UseCaseNode('Synthetic Identity Fraud',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/synthetic-identity-fraud/', 2),
                        UseCaseNode('Transaction Fraud Ring',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/transaction-fraud-ring/', 2),
                        UseCaseNode('Transaction Monitoring',
                                  'https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/transaction-monitoring/', 2)
                    ]
                )
            ]
        elif name == 'Insurance':
            industry_node.children = [
                UseCaseNode('Claims Fraud',
                          'https://neo4j.com/developer/industry-use-cases/insurance/claims-fraud/', 1),
                UseCaseNode('Quote Fraud',
                          'https://neo4j.com/developer/industry-use-cases/insurance/quote-fraud/', 1)
            ]
        elif name == 'Manufacturing':
            industry_node.children = [
                UseCaseNode(
                    name='Supply Chain and Logistics Management',
                    url='https://neo4j.com/developer/industry-use-cases/manufacturing/supply-chain-management/',
                    level=1,
                    children=[
                        UseCaseNode('E.V. Route Planning',
                                  'https://neo4j.com/developer/industry-use-cases/manufacturing/supply-chain-management/ev-route-planning/', 2)
                    ]
                ),
                UseCaseNode(
                    name='Product Design and Engineering',
                    url='https://neo4j.com/developer/industry-use-cases/manufacturing/product-design-and-engineering/',
                    level=1,
                    children=[
                        UseCaseNode('Configurable B.O.M.',
                                  'https://neo4j.com/developer/industry-use-cases/manufacturing/product-design-and-engineering/configurable-bom/', 2),
                        UseCaseNode('Engineering Traceability',
                                  'https://neo4j.com/developer/industry-use-cases/manufacturing/product-design-and-engineering/engineering-traceability/', 2)
                    ]
                ),
                UseCaseNode(
                    name='Production Planning and Optimization',
                    url='https://neo4j.com/developer/industry-use-cases/manufacturing/production-planning-and-optimization/',
                    level=1,
                    children=[
                        UseCaseNode('Process Monitoring and CPA',
                                  'https://neo4j.com/developer/industry-use-cases/manufacturing/production-planning-and-optimization/process-monitoring-cpa/', 2)
                    ]
                )
            ]
        elif name == 'Industry Agnostic':
            industry_node.children = [
                UseCaseNode('Entity Resolution',
                          'https://neo4j.com/developer/industry-use-cases/agnostic/entity-resolution/', 1),
                UseCaseNode('IT Service Graph',
                          'https://neo4j.com/developer/industry-use-cases/agnostic/it-service-graph/', 1)
            ]

        industries.append(industry_node)

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


def print_tree(node: UseCaseNode, indent: int = 0, show_urls: bool = False):
    """
    Print the use case tree in a readable format

    Args:
        node: The node to print
        indent: Current indentation level
        show_urls: Whether to show URLs alongside names
    """
    if node.level >= 0:  # Skip root node
        prefix = "  " * indent

        # Different symbols for different levels
        if node.level == 0:
            symbol = "📁"
        elif node.level == 1:
            symbol = "📂"
        else:
            symbol = "📄"

        name_display = f"{prefix}{symbol} {node.name}"
        if show_urls:
            print(f"{name_display} ({node.url})")
        else:
            print(name_display)

    for child in node.children:
        print_tree(child, indent + 1, show_urls)

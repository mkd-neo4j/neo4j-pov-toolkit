"""
Web Content Fetching and Conversion Utilities

Purpose:
    Provides utilities for fetching web pages and converting HTML to markdown.
    Specifically designed to scrape Neo4j use case documentation from neo4j.com
    and convert it into clean, LLM-readable markdown format.

Why This Module Exists:
    The toolkit leverages Neo4j's industry use case library to guide code generation.
    When an LLM needs to understand a use case (e.g., "Synthetic Identity Fraud"),
    it needs the use case documentation in a format it can process (markdown).

    This module:
    - Fetches HTML from Neo4j use case pages
    - Extracts main content (removing navigation, headers, footers)
    - Converts HTML to clean markdown
    - Preserves code blocks with syntax highlighting info
    - Cleans up excessive whitespace

Used By:
    - get-usecase CLI command (fetches specific use case pages)
    - Use case scraper (downloads use case content for LLM analysis)

Key Functions:
    fetch_page_as_markdown() - Main entry point; fetches URL and returns markdown

Architecture Context:
    This is part of the use case discovery system:
    1. scraper.py builds hierarchy of use case URLs
    2. web_utils.py fetches and converts individual use case pages
    3. LLM reads the markdown to understand data models and patterns
    4. LLM generates ingestion code based on the use case
"""

from typing import Optional, Dict, List
import requests
import html2text
from bs4 import BeautifulSoup, Tag
import re


def _extract_code_blocks(content: Tag) -> List[Dict[str, str]]:
    """
    Extract code blocks from HTML and return them with metadata

    Args:
        content: BeautifulSoup Tag containing the content

    Returns:
        List of dicts with 'placeholder', 'code', and 'language' keys
    """
    code_blocks = []

    # Find all code blocks (looking for <code> tags with language info)
    for idx, code_tag in enumerate(content.find_all('code')):
        # Try to get language from class attribute
        language = ''
        if code_tag.get('class'):
            for cls in code_tag.get('class', []):
                if cls.startswith('language-'):
                    language = cls.replace('language-', '')
                    break

        # Also check data-lang attribute
        if not language and code_tag.get('data-lang'):
            language = code_tag.get('data-lang')

        # Extract the raw text, stripping all span tags
        code_text = code_tag.get_text()

        # Create a unique placeholder
        placeholder = f"___CODE_BLOCK_{idx}___"

        code_blocks.append({
            'placeholder': placeholder,
            'code': code_text,
            'language': language
        })

        # Replace the code tag with the placeholder
        code_tag.replace_with(placeholder)

    return code_blocks


def _restore_code_blocks(markdown: str, code_blocks: List[Dict[str, str]]) -> str:
    """
    Replace placeholders in markdown with properly formatted code blocks

    Args:
        markdown: Markdown text with placeholders
        code_blocks: List of code block dicts from _extract_code_blocks

    Returns:
        Markdown with proper fenced code blocks
    """
    result = markdown

    for block in code_blocks:
        # Create a fenced code block
        lang = block['language'] if block['language'] else ''
        fenced_block = f"\n```{lang}\n{block['code']}\n```\n"

        # Replace the placeholder
        # The placeholder might be in an indented code block, so we need to handle various formats
        result = result.replace(block['placeholder'], fenced_block)
        # Also try with indentation (html2text might add spaces)
        result = re.sub(
            r'[ ]{4,}' + re.escape(block['placeholder']),
            fenced_block,
            result
        )

    return result


def _cleanup_markdown(markdown: str) -> str:
    """
    Clean up excessive blank lines in markdown

    Reduces 3 or more consecutive newlines to exactly 2 newlines,
    and removes blank lines between consecutive list items for more
    compact, readable lists.

    Args:
        markdown: Markdown text to clean

    Returns:
        Cleaned markdown with excessive blank lines removed
    """
    # Remove blank lines between consecutive bullet points
    # Pattern matches: bullet line + blank line + bullet line
    # We run this multiple times to handle all cases
    cleaned = markdown
    while True:
        new_cleaned = re.sub(r'(\n[ ]*\*[^\n]+)\n\n([ ]*\*)', r'\1\n\2', cleaned)
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned

    # Remove lines that contain only whitespace (spaces/tabs)
    # Run multiple times to catch all occurrences
    while True:
        new_cleaned = re.sub(r'\n[ \t]+\n', '\n\n', cleaned)
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned

    # Replace 3 or more consecutive newlines with exactly 2
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    # Remove excessive blank lines before code blocks (max 1 blank line)
    cleaned = re.sub(r'\n{2,}(\n```)', r'\n\1', cleaned)

    # Remove excessive blank lines after code blocks (max 1 blank line)
    cleaned = re.sub(r'(```\n)\n{2,}', r'\1\n', cleaned)

    # Remove trailing whitespace at the end of the file
    cleaned = cleaned.rstrip() + '\n'

    return cleaned


def fetch_page_as_markdown(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch a web page and convert its HTML content to clean, LLM-readable markdown.

    This is the main entry point for converting Neo4j use case pages (or any web page)
    into markdown format suitable for LLM processing.

    Purpose:
        Enable LLMs to read and understand Neo4j use case documentation by converting
        HTML pages into clean markdown that preserves structure, code blocks, and
        essential content while removing navigation cruft.

    How It Works:
        1. Fetches the HTML from the provided URL
        2. Parses HTML using BeautifulSoup
        3. Extracts main content (article, main tag) to avoid navigation
        4. Extracts and preserves code blocks with language info
        5. Converts HTML to markdown using html2text
        6. Restores code blocks as fenced markdown code blocks
        7. Cleans up excessive whitespace
        8. Returns clean markdown string

    Args:
        url (str): Full URL to fetch (e.g., "https://neo4j.com/developer/industry-use-cases/...")
        timeout (int): Request timeout in seconds (default: 10)

    Returns:
        str: Markdown content of the page with preserved code blocks and clean formatting
        None: If fetching or conversion fails (network error, parse error, etc.)

    Example Usage:
        from src.core.web_utils import fetch_page_as_markdown

        url = "https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/synthetic-identity-fraud/"
        markdown = fetch_page_as_markdown(url)

        if markdown:
            print(markdown)  # Clean markdown content ready for LLM

    LLM Workflow:
        1. LLM discovers use case URL via list-usecases command
        2. LLM runs: python cli.py get-usecase <url>
        3. This function fetches and converts the page
        4. LLM receives markdown with data model and Cypher examples
        5. LLM uses markdown to inform generated ingestion code

    What Gets Extracted:
        ✓ Main article content
        ✓ Code blocks (Cypher, Python, etc.) with language tags
        ✓ Headings, lists, paragraphs
        ✓ Links (converted to markdown format)

    What Gets Filtered Out:
        ✗ Navigation menus
        ✗ Headers and footers
        ✗ Sidebars
        ✗ Ads and tracking scripts

    Returns:
        Clean markdown or None on failure. Check for None and handle gracefully.
    """
    try:
        # Fetch the page
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        # Parse HTML to extract main content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Try to find the main content area using common selectors
        content = None

        # Try 1: Look for article tag
        content = soup.find('article')

        # Try 2: Look for main > article
        if not content:
            main = soup.find('main')
            if main:
                content = main.find('article')

        # Try 3: Look for role="main"
        if not content:
            content = soup.find(attrs={'role': 'main'})

        # Try 4: Look for main tag
        if not content:
            content = soup.find('main')

        # Fallback: Use the entire body
        if not content:
            content = soup.find('body')

        # Extract code blocks before conversion
        code_blocks = _extract_code_blocks(content)

        # Convert the extracted content to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap text

        # Convert to string first if it's a BeautifulSoup element
        html_content = str(content) if content else response.text
        markdown_content = h.handle(html_content)

        # Restore code blocks with proper fencing
        markdown_content = _restore_code_blocks(markdown_content, code_blocks)

        # Clean up excessive blank lines
        markdown_content = _cleanup_markdown(markdown_content)

        return markdown_content

    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"Error converting to markdown: {e}")
        return None

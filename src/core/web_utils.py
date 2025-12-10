"""
Web utilities for fetching and converting web pages

Provides generic utilities for web scraping and content conversion.
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
    Fetch a web page and convert its HTML content to markdown

    Attempts to extract only the main content area (article/main) to avoid
    navigation, headers, and sidebars. Falls back to full page if no main
    content is found. Code blocks are converted to fenced code blocks with
    language identifiers.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds (default: 10)

    Returns:
        Markdown content of the page, or None if fetching/conversion fails
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

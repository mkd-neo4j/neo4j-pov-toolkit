"""
CLI Terminal Formatting Utilities

Purpose:
    Provides a consistent visual language for the CLI through ANSI color codes,
    box drawing, and formatted output helpers. Makes CLI output professional,
    readable, and easy to scan.

Why This Module Exists:
    Command-line tools benefit from visual hierarchy and color coding:
    - Colors draw attention to important information
    - Boxes create clear section boundaries
    - Consistent formatting builds user confidence
    - Symbols (✓ ✗ ⚠) provide instant visual feedback

Used By:
    All CLI commands (neo4j-test, neo4j-info, list-usecases, etc.) use these
    utilities to format their output consistently.

Design Philosophy:
    - Simple functions that do one thing well
    - Consistent color meanings (green=success, red=error, etc.)
    - Professional appearance without being flashy
    - Works on all modern terminals (ANSI escape codes)
"""


class Colors:
    """
    ANSI color codes for terminal output.

    These are standard ANSI escape sequences that work on:
    - macOS Terminal
    - Linux terminals (bash, zsh, etc.)
    - Windows Terminal (Windows 10+)
    - VS Code integrated terminal
    - Most other modern terminal emulators

    Color Semantics:
        GREEN:  Success, completion, positive outcomes
        RED:    Errors, failures, problems
        BLUE:   Informational, neutral data
        YELLOW: Warnings, cautions, helpful tips
        CYAN:   Commands, labels, headers, highlights
        BOLD:   Emphasis, labels, section headers
        DIM:    Secondary information, metadata, timestamps
        RESET:  Return to default terminal colors

    Usage:
        from src.cli.utils.formatting import Colors

        print(f"{Colors.GREEN}Success!{Colors.RESET}")
        print(f"{Colors.BOLD}Important:{Colors.RESET} {Colors.DIM}details{Colors.RESET}")

    Note:
        Always use RESET after coloring text to avoid color bleeding into
        subsequent output. Format strings make this easy:
        f"{Colors.GREEN}text{Colors.RESET}"
    """
    GREEN = '\033[92m'    # Success messages, checkmarks
    RED = '\033[91m'      # Error messages, X marks
    BLUE = '\033[94m'     # Informational text
    YELLOW = '\033[93m'   # Warnings, tips
    CYAN = '\033[96m'     # Commands, labels, box drawing
    BOLD = '\033[1m'      # Section headers, emphasis
    RESET = '\033[0m'     # Return to default colors
    DIM = '\033[2m'       # Secondary information, timestamps


def print_box(title, width=65):
    """
    Print a decorative box header to visually separate sections.

    Creates a professional-looking box using Unicode box-drawing characters:
    ╔═══════════════════════╗
    ║       Title Here       ║
    ╚═══════════════════════╝

    Purpose:
        Provides visual separation between different sections of CLI output.
        Draws the user's eye to the start of a new command's output.

    Args:
        title (str): Text to display centered in the box
        width (int): Total width of the box in characters (default 65)

    Example:
        print_box("Neo4j Connection Test")

        Output:
        ╔═══════════════════════════════════════════════════════════════╗
        ║                     Neo4j Connection Test                     ║
        ╚═══════════════════════════════════════════════════════════════╝

    Used By:
        - neo4j-test command (shows "Neo4j Connection Test")
        - neo4j-info command (shows "Neo4j Connection Information")
        - list-usecases command (shows "Neo4j Use Cases")
        - get-usecase command (shows "Fetching Use Case")
    """
    # Top border with box-drawing characters
    print(f"\n{Colors.CYAN}╔{'═' * (width - 2)}╗{Colors.RESET}")

    # Title line with centered text
    padding = (width - len(title) - 2) // 2  # Calculate left padding for centering
    # Note: Right padding calculated to handle odd widths correctly
    print(f"{Colors.CYAN}║{' ' * padding}{Colors.BOLD}{title}{Colors.RESET}{Colors.CYAN}{' ' * (width - len(title) - padding - 2)}║{Colors.RESET}")

    # Bottom border
    print(f"{Colors.CYAN}╚{'═' * (width - 2)}╝{Colors.RESET}\n")


def print_success(message):
    """
    Print a success message with a green checkmark symbol.

    Purpose:
        Provides instant positive feedback that an operation succeeded.
        The green color and ✓ symbol are universally understood success indicators.

    Args:
        message (str): Success message to display

    Example:
        print_success("Connection successful!")

        Output:
        ✓ Connection successful!

    Used For:
        - Successful Neo4j connection
        - Successful file operations
        - Completed data loading
        - Any positive outcome worth highlighting
    """
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message):
    """
    Print an error message with a red X mark symbol.

    Purpose:
        Provides instant negative feedback that an operation failed.
        The red color and ✗ symbol immediately communicate an error.

    Args:
        message (str): Error message to display

    Example:
        print_error("Connection failed!")

        Output:
        ✗ Connection failed!

    Used For:
        - Failed Neo4j connection
        - Failed file operations
        - Missing required data
        - Any failure that needs user attention
    """
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_warning(message):
    """
    Print a warning message with a yellow warning triangle symbol.

    Purpose:
        Draws attention to potential issues or important information without
        indicating complete failure. User should take note but may continue.

    Args:
        message (str): Warning message to display

    Example:
        print_warning("Database version is outdated")

        Output:
        ⚠ Database version is outdated

    Used For:
        - Deprecated features
        - Sub-optimal configurations
        - Missing optional data
        - Situations that work but aren't ideal
    """
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(label, value, width=20):
    """
    Print a formatted key-value pair in label: value format.

    Purpose:
        Displays structured information in a consistent, easy-to-read format.
        Labels are bold and left-aligned, values are cyan and right-aligned.

    Args:
        label (str): The field name/label (e.g., "URI", "Database", "Version")
        value (str): The field value (e.g., "neo4j://localhost:7687")
        width (int): Width to allocate for the label column (default 20)

    Example:
        print_info("URI", "neo4j://localhost:7687")
        print_info("Database", "neo4j")
        print_info("Version", "6.0.3")

        Output:
        URI                 : neo4j://localhost:7687
        Database            : neo4j
        Version             : 6.0.3

    Used For:
        - Displaying connection details
        - Showing database information
        - Formatting configuration output
        - Any structured key-value data

    Note:
        The width parameter should be set to accommodate the longest label
        in a group of related print_info() calls for proper alignment.
    """
    print(f"{Colors.BOLD}{label:<{width}}{Colors.RESET}: {Colors.CYAN}{value}{Colors.RESET}")

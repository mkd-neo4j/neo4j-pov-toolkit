"""
CLI Formatting Utilities

Provides colors, box drawing, and formatted output helpers.
"""


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    DIM = '\033[2m'


def print_box(title, width=65):
    """Print a nice box header"""
    print(f"\n{Colors.CYAN}╔{'═' * (width - 2)}╗{Colors.RESET}")
    padding = (width - len(title) - 2) // 2
    print(f"{Colors.CYAN}║{' ' * padding}{Colors.BOLD}{title}{Colors.RESET}{Colors.CYAN}{' ' * (width - len(title) - padding - 2)}║{Colors.RESET}")
    print(f"{Colors.CYAN}╚{'═' * (width - 2)}╝{Colors.RESET}\n")


def print_success(message):
    """Print success message with checkmark"""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message):
    """Print error message with X mark"""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(label, value, width=20):
    """Print formatted info line (label: value)"""
    print(f"{Colors.BOLD}{label:<{width}}{Colors.RESET}: {Colors.CYAN}{value}{Colors.RESET}")

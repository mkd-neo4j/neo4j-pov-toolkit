#!/usr/bin/env python3
"""
Neo4j PoV Toolkit - CLI Entry Point

A professional CLI for LLM-powered Neo4j data ingestion code generation.

Usage:
    python cli.py neo4j-test                 Test connection
    python cli.py neo4j-info                 Full connection info
    python cli.py --help                     Show help
    python cli.py --version                  Show toolkit version
"""

import sys
import os
from pathlib import Path


def auto_detect_venv():
    """
    Automatically detect and activate a virtual environment if not already in one.

    Purpose:
        Provides a seamless user experience by automatically activating the virtual
        environment when the CLI is run. Users don't need to remember to activate venv.

    Why This Exists:
        Common user problem: "I ran the CLI and got ModuleNotFoundError"
        Solution: Automatically find and activate venv if present

    How It Works:
        1. Checks if already in a venv (sys.prefix != sys.base_prefix)
        2. If not, searches for venv folders (venv/, env/, .venv/)
        3. Validates it's a real venv (checks for pyvenv.cfg)
        4. Adds site-packages to sys.path
        5. Sets VIRTUAL_ENV environment variable
        6. Updates PATH to include venv bin directory

    This runs before any imports, ensuring toolkit modules are available.
    """
    # Check if already in a virtual environment
    if sys.prefix != sys.base_prefix:
        return  # Already in a venv, nothing to do

    # Get the script directory
    script_dir = Path(__file__).parent.resolve()

    # Common venv directory names to search for
    venv_names = ['venv', 'env', '.venv']

    # Try to find a venv
    venv_path = None
    for name in venv_names:
        candidate = script_dir / name
        if candidate.is_dir():
            # Check if it's actually a venv by looking for pyvenv.cfg
            if (candidate / 'pyvenv.cfg').exists():
                venv_path = candidate
                break

    if not venv_path:
        return  # No venv found, proceed without it

    # Determine the site-packages path based on platform
    if sys.platform == 'win32':
        site_packages = venv_path / 'Lib' / 'site-packages'
    else:
        # Unix-like systems (Linux, macOS)
        python_version = f'python{sys.version_info.major}.{sys.version_info.minor}'
        site_packages = venv_path / 'lib' / python_version / 'site-packages'

    # Verify site-packages exists
    if not site_packages.exists():
        return

    # Add to sys.path at the beginning (high priority)
    site_packages_str = str(site_packages)
    if site_packages_str not in sys.path:
        sys.path.insert(0, site_packages_str)

    # Set environment variables to mimic activation
    os.environ['VIRTUAL_ENV'] = str(venv_path)

    # Update PATH to include venv bin/Scripts directory
    if sys.platform == 'win32':
        venv_bin = venv_path / 'Scripts'
    else:
        venv_bin = venv_path / 'bin'

    if venv_bin.exists():
        os.environ['PATH'] = f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}"

    # Update sys.prefix to reflect venv (cosmetic, but makes tools think we're in venv)
    sys.prefix = str(venv_path)

    # Optional: Print info message (only if not silenced)
    if os.environ.get('NEO4J_TOOLKIT_SILENT_VENV') != '1':
        print(f"✓ Auto-detected virtual environment: {venv_path.name}", file=sys.stderr)


if __name__ == '__main__':
    # Attempt to auto-detect and activate venv before importing anything
    auto_detect_venv()

    from src.cli.main import main
    sys.exit(main())

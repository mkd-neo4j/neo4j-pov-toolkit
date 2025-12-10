#!/usr/bin/env python3
"""
Neo4j Demo Toolkit - CLI Entry Point

A professional CLI for LLM-powered Neo4j data ingestion code generation.

Usage:
    python cli.py neo4j-test                 Test connection
    python cli.py neo4j-info                 Full connection info
    python cli.py --help                     Show help
    python cli.py --version                  Show toolkit version
"""

if __name__ == '__main__':
    from src.cli.main import main
    import sys
    sys.exit(main())

"""
Neo4j Integration Module - Version Detection and Query Execution

This module provides the core Neo4j integration for the toolkit, enabling both
version-aware code generation and version-agnostic query execution.

Public API:
    get_neo4j_info() - Detect Neo4j and Cypher versions from live database
    get_query() - Get a Neo4jQuery instance for executing Cypher
    Neo4jQuery - Query runner class (prefer get_query() for most use cases)

LLM Usage Patterns:

    Pattern 1: Detect Version Before Code Generation
        from src.core.neo4j import get_neo4j_info

        info = get_neo4j_info()
        if info['connected']:
            # Generate code appropriate for info['neo4j_version']

    Pattern 2: Execute Queries in Generated Code
        from src.core.neo4j import get_query

        query = get_query()
        query.run_batched(cypher, data, batch_size=1000)

Two-Layer Architecture:
    Layer 1 (Code Generation): Use get_neo4j_info() to detect version
    Layer 2 (Runtime Execution): Use get_query() to execute Cypher

This separation keeps generated code simple while handling complexity in pre-built utilities.
"""

from .version import get_neo4j_info, get_query
from .query import Neo4jQuery

__all__ = ['get_neo4j_info', 'get_query', 'Neo4jQuery']

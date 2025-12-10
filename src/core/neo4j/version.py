"""
Neo4j version detection and query runner provider.

This module provides:
1. get_neo4j_info() - Detects Neo4j and Cypher versions from the database
2. get_query() - Returns Cypher query runner for running queries
"""

import json
from .query import Neo4jQuery


def get_neo4j_info():
    """
    Detects Neo4j version information from the database.

    Returns:
        dict: Version information
            {
              "connected": True/False,
              "neo4j_version": "2025.06.2",
              "cypher_version": ["5", "25"],
              "enterprise": True/False
            }

    Usage:
        # As Python API
        info = get_neo4j_info()
        if info['connected']:
            print(f"Neo4j {info['neo4j_version']}")
            print(f"Cypher versions: {info['cypher_version']}")

        # As CLI tool (for LLMs)
        python -m src.core.neo4j.version
    """
    try:
        # Use the query runner to detect version from database
        # Query runner handles all .env loading and connection details
        query = Neo4jQuery()

        result = query.run("""
            CALL dbms.components()
            YIELD name, versions, edition
            WHERE name IN ['Neo4j Kernel', 'Cypher']
            RETURN name, versions, edition
        """)

        neo4j_version = None
        cypher_version = None
        enterprise = None

        for record in result:
            if record['name'] == 'Neo4j Kernel':
                neo4j_version = record['versions'][0]
                enterprise = record['edition'] == 'enterprise'
            elif record['name'] == 'Cypher':
                # Cypher returns list of supported versions like [5, 25]
                # Convert to list of strings for JSON serialization
                cypher_version = [str(v) for v in record['versions']]

        query.close()

        if not neo4j_version or not cypher_version:
            return {
                "connected": False,
                "error": "Unable to detect Neo4j or Cypher version from database"
            }

        return {
            "connected": True,
            "neo4j_version": neo4j_version,
            "cypher_version": cypher_version,
            "enterprise": enterprise
        }

    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


def get_query():
    """
    Returns a Neo4j query runner.

    The query runner is version-agnostic - it just runs Cypher queries.
    The LLM generates version-appropriate Cypher based on version
    detected via get_neo4j_info().

    Returns:
        Neo4jQuery: Query runner instance

    Example:
        from src.core.neo4j.version import get_query

        query = get_query()

        # Run single query
        query.run("MATCH (n) RETURN count(n)")

        # Run batched query
        cypher = '''
        UNWIND $batch AS row
        MERGE (c:Customer {id: row.id})
        SET c += row
        '''
        query.run_batched(cypher, customers, batch_size=1000)
    """
    return Neo4jQuery()


if __name__ == '__main__':
    # When run as CLI tool, output JSON
    result = get_neo4j_info()
    print(json.dumps(result, indent=2))

"""
Neo4j Version Detection and Query Runner Provider

Purpose:
    Provides two critical functions for the toolkit's two-layer version handling strategy:
    1. get_neo4j_info() - Detects Neo4j and Cypher versions from the live database
    2. get_query() - Returns a query runner instance for executing Cypher

Why This Module Exists:
    The toolkit must generate code that works with any Neo4j version (4.x, 5.x, 6.x).
    Different versions support different Cypher syntax, features, and patterns.

    Traditional approaches:
    ❌ Hard-code for one version → breaks on other versions
    ❌ Include complex version detection in generated code → messy, error-prone
    ✅ Our approach: Detect version upfront, generate version-appropriate code

Architecture: Two-Layer Version Handling

    Layer 1: Code Generation Time (LLM uses get_neo4j_info())
        1. User runs: python cli.py neo4j-info
        2. LLM calls get_neo4j_info() to detect database version
        3. LLM learns: "This is Neo4j 6.0 with Cypher 25"
        4. LLM generates Cypher using Neo4j 6.0 syntax (MERGE, SET, etc.)
        5. Generated code saved to workspace/generated/data_mapper.py

    Layer 2: Code Execution Time (Generated code uses get_query())
        1. User runs: python workspace/generated/data_mapper.py
        2. Generated code imports: from src.core.neo4j.version import get_query
        3. Generated code calls: query = get_query()
        4. Generated code uses: query.run_batched(cypher, data)
        5. Query runner handles session management, transactions, batching

Used By:
    - LLM (indirectly via CLI commands) to detect version and generate appropriate code
    - CLI commands (neo4j-test, neo4j-info) to show version information
    - Generated data mapper code to get a query runner instance

Key Design Principles:
    - Simple interface: Two functions, clear purposes
    - LLM-friendly: JSON output, CLI-callable, clear documentation
    - Separation of concerns: Version detection separate from query execution
    - Zero configuration: Reads .env automatically via query runner
"""

import json
from .query import Neo4jQuery


def get_neo4j_info():
    """
    Detect Neo4j and Cypher version information from the live database.

    This function connects to the Neo4j database specified in your .env file
    and queries the database to determine its version, Cypher version, and
    edition (Community vs Enterprise).

    Purpose:
        Enables the LLM to generate version-appropriate Cypher syntax by first
        understanding what version of Neo4j it's targeting. This is Layer 1 of
        the two-layer version handling strategy.

    Why This Matters:
        Different Neo4j versions support different Cypher features:
        - Neo4j 4.x: Basic MERGE, CREATE, MATCH patterns
        - Neo4j 5.x: Improved query performance, new functions
        - Neo4j 6.x: Advanced features, vector indexes, etc.

        By detecting the version first, the LLM can generate code that will
        work correctly on the user's specific database.

    How It Works:
        1. Creates a query runner (which reads .env and connects)
        2. Runs: CALL dbms.components()
        3. Extracts Neo4j Kernel version (e.g., "6.0.3")
        4. Extracts Cypher version (e.g., ["5", "25"])
        5. Extracts edition (enterprise or community)
        6. Returns all info as a dictionary

    Returns:
        dict: Version information with one of two shapes:

        Success shape:
            {
                "connected": True,
                "neo4j_version": "6.0.3",
                "cypher_version": ["5", "25"],
                "enterprise": True
            }

        Failure shape:
            {
                "connected": False,
                "error": "Unable to connect to Neo4j at neo4j://localhost:7687"
            }

    Usage as Python API:
        from src.core.neo4j.version import get_neo4j_info

        info = get_neo4j_info()

        if info['connected']:
            print(f"Connected to Neo4j {info['neo4j_version']}")
            print(f"Cypher versions: {', '.join(info['cypher_version'])}")
            if info['enterprise']:
                print("Enterprise edition detected")
        else:
            print(f"Connection failed: {info['error']}")

    Usage as CLI Tool (for LLMs):
        The LLM should run this as a CLI command to detect version:

        $ python -m src.core.neo4j.version

        Output (JSON):
        {
          "connected": true,
          "neo4j_version": "6.0.3",
          "cypher_version": ["5", "25"],
          "enterprise": true
        }

        The LLM can then parse this JSON and use it to inform code generation.

    LLM Decision Making:
        Based on the version info, the LLM should:

        If Neo4j 6.x:
            - Use modern Cypher syntax
            - Leverage vector indexes if needed
            - Use latest query patterns

        If Neo4j 5.x:
            - Use stable Cypher syntax
            - Avoid 6.x-only features
            - Use proven query patterns

        If Neo4j 4.x:
            - Use conservative Cypher syntax
            - Avoid newer features
            - Stick to basics (MERGE, MATCH, CREATE)

    Example - LLM Workflow:
        1. User: "Help me load customer data into Neo4j"
        2. LLM: Runs `python -m src.core.neo4j.version`
        3. LLM: Sees Neo4j 6.0.3 with Cypher 25
        4. LLM: Generates code using Neo4j 6.0-compatible syntax
        5. LLM: Writes workspace/generated/data_mapper.py
        6. User: Runs generated code successfully

    Raises:
        No exceptions raised - errors are captured and returned in the dict
        with connected=False and an error message.

    Connection Details:
        - Reads credentials from .env file automatically
        - Uses Neo4jQuery to handle connection
        - Automatically closes connection after detection
    """
    try:
        # Create a query runner instance
        # This automatically loads credentials from .env and connects to Neo4j
        query = Neo4jQuery()

        # Query the database for component information
        # dbms.components() is a built-in procedure that returns metadata about
        # the Neo4j installation, including versions and edition
        result = query.run("""
            CALL dbms.components()
            YIELD name, versions, edition
            WHERE name IN ['Neo4j Kernel', 'Cypher']
            RETURN name, versions, edition
        """)

        # Initialize variables to store parsed version info
        neo4j_version = None
        cypher_version = None
        enterprise = None

        # Parse the results - we expect two records:
        # 1. Neo4j Kernel with versions like ['6.0.3'] and edition 'enterprise' or 'community'
        # 2. Cypher with versions like [5, 25] (supported Cypher versions)
        for record in result:
            if record['name'] == 'Neo4j Kernel':
                # Extract the first (and typically only) version number
                neo4j_version = record['versions'][0]
                # Check if this is enterprise edition (vs community)
                enterprise = record['edition'] == 'enterprise'
            elif record['name'] == 'Cypher':
                # Cypher returns list of supported versions like [5, 25]
                # Convert numbers to strings for consistent JSON serialization
                cypher_version = [str(v) for v in record['versions']]

        # Clean up the connection
        query.close()

        # Validate that we got the information we need
        if not neo4j_version or not cypher_version:
            return {
                "connected": False,
                "error": "Unable to detect Neo4j or Cypher version from database"
            }

        # Return success with all version information
        return {
            "connected": True,
            "neo4j_version": neo4j_version,
            "cypher_version": cypher_version,
            "enterprise": enterprise
        }

    except Exception as e:
        # Catch any connection errors, authentication failures, etc.
        # Return a failure dict with the error message for debugging
        return {
            "connected": False,
            "error": str(e)
        }


def get_query():
    """
    Get a Neo4j query runner instance for executing Cypher queries.

    This is the primary entry point for LLM-generated code to execute queries
    against Neo4j. It's Layer 2 of the two-layer version handling strategy.

    Purpose:
        Provides a simple, version-agnostic interface for running Cypher queries.
        The generated code doesn't need to worry about:
        - Connection management
        - Session handling
        - Transaction patterns
        - Batching logic
        - Resource cleanup

        All of that is handled by the Neo4jQuery class this function returns.

    Why Use This Instead of Direct Neo4jQuery():
        This function serves as a clean API boundary. It:
        1. Provides a single import point for generated code
        2. Makes generated code more readable
        3. Allows future enhancements without breaking generated code
        4. Matches the pattern used throughout toolkit documentation

    Returns:
        Neo4jQuery: A query runner instance ready to execute Cypher.
                   Automatically configured with credentials from .env file.

    Example - Simple Query:
        from src.core.neo4j.version import get_query

        query = get_query()
        result = query.run("MATCH (n:Customer) RETURN count(n) as count")
        print(f"Found {result[0]['count']} customers")

    Example - Batch Loading (Most Common Pattern):
        from src.core.neo4j.version import get_query

        query = get_query()

        # Load customer nodes in batches
        cypher = '''
        UNWIND $batch AS row
        MERGE (c:Customer {id: row.id})
        SET c += row
        '''
        query.run_batched(cypher, customers, batch_size=1000)

    Example - With Context Manager:
        from src.core.neo4j.version import get_query

        with get_query() as query:
            query.run("MATCH (n) RETURN count(n)")
        # Automatically closed

    LLM Code Generation Pattern:
        When generating data_mapper.py, the LLM should:

        1. Import at the top:
           from src.core.neo4j.version import get_query
           from src.core.logger import log

        2. Create query runner in each function:
           def load_customers():
               query = get_query()
               # ... use query.run_batched()

        3. Let the query runner handle all connection details

    Note on Version Handling:
        This function returns a version-agnostic query runner. The runner
        doesn't know about Neo4j versions - it just executes whatever Cypher
        you give it. The LLM's job is to generate version-appropriate Cypher
        based on what get_neo4j_info() reported.

    Connection Configuration:
        The query runner automatically reads from .env:
        - NEO4J_URI (required)
        - NEO4J_USER (required)
        - NEO4J_PASSWORD (required)
        - NEO4J_DATABASE (optional, defaults to 'neo4j')

    Raises:
        No direct exceptions from this function. The Neo4jQuery constructor
        may raise connection errors if credentials are invalid or database
        is not running - those will propagate to the caller.
    """
    return Neo4jQuery()


if __name__ == '__main__':
    """
    CLI Entry Point for Version Detection

    When run as a module (python -m src.core.neo4j.version), this script
    detects the Neo4j version and outputs JSON to stdout.

    This is designed for LLMs to run as a CLI command to discover version info
    before generating code.

    Usage:
        $ python -m src.core.neo4j.version

    Output (on success):
        {
          "connected": true,
          "neo4j_version": "6.0.3",
          "cypher_version": ["5", "25"],
          "enterprise": true
        }

    Output (on failure):
        {
          "connected": false,
          "error": "Unable to connect to Neo4j at neo4j://localhost:7687"
        }

    LLM Workflow:
        1. LLM runs: python -m src.core.neo4j.version
        2. LLM parses the JSON output
        3. LLM uses version info to generate appropriate Cypher syntax
        4. LLM writes generated code to workspace/generated/data_mapper.py
    """
    result = get_neo4j_info()
    print(json.dumps(result, indent=2))

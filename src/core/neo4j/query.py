"""
Neo4j Query Runner - Version-Agnostic Cypher Execution Engine

Purpose:
    Provides a simple, reliable interface for executing Cypher queries against
    Neo4j. Handles connection management, batching, and transactions without
    needing to know about Neo4j versions, node schemas, or relationship types.

Why This Module Exists:
    The toolkit follows a clean separation of concerns:
    - This module: Runs Cypher queries (the "how")
    - LLM-generated code: Provides the Cypher queries (the "what")
    - Version detection: Determines Neo4j capabilities (the "context")

    By keeping query execution separate from query generation, we get:
    - Simple, testable code that's easy to maintain
    - LLM can focus on domain logic (mapping CSV → Cypher)
    - All connection management, batching, and error handling pre-built

Architecture Context:
    This is Layer 2 of the two-layer version handling strategy:

    Layer 1 (Code Generation):
        - LLM detects Neo4j version using get_neo4j_info()
        - Generates version-appropriate Cypher syntax
        - Writes data_mapper.py with correct Cypher for your database

    Layer 2 (Runtime Execution):
        - Generated code imports Neo4jQuery from this module
        - Calls run() or run_batched() with the Cypher
        - This class handles driver patterns, sessions, transactions

Used By:
    - CLI commands (neo4j-test, neo4j-info) for querying database info
    - Version detection (version.py) for discovering Neo4j capabilities
    - LLM-generated data mapper code (workspace/generated/*.py)

Key Design Decision:
    This class is intentionally "dumb" - it doesn't know about:
    - Node labels or relationship types
    - Data schemas or property names
    - Constraints or indexes
    - Version-specific Cypher syntax

    All that intelligence lives in the LLM-generated code. This class just
    provides reliable Cypher execution with batching.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from ..logger import log


class Neo4jQuery:
    """
    Version-agnostic Cypher query runner for Neo4j.

    This class provides a simple, reliable interface for executing Cypher queries
    without needing to know about Neo4j versions, schemas, or domain models.

    Responsibilities:
        - Load connection credentials from .env file
        - Create and manage Neo4j driver connection
        - Execute single Cypher queries
        - Execute batched Cypher queries (for bulk data loading)
        - Execute multiple queries in a transaction
        - Clean up resources (close connections)

    What This Class Does NOT Do:
        - Generate Cypher queries (that's the LLM's job)
        - Validate data schemas or types
        - Handle version-specific syntax (LLM generates correct syntax)
        - Cache results or manage state

    Usage Pattern for LLMs:
        When generating data_mapper.py code, instruct the LLM to:

        1. Import this class:
           from src.core.neo4j.version import get_query

        2. Get a query runner instance:
           query = get_query()

        3. Use run() for single queries:
           result = query.run("MATCH (n:Customer) RETURN count(n) as count")

        4. Use run_batched() for bulk loading:
           cypher = '''
           UNWIND $batch AS row
           MERGE (c:Customer {id: row.id})
           SET c += row
           '''
           query.run_batched(cypher, customers, batch_size=1000)

    Attributes:
        uri (str): Neo4j connection URI from NEO4J_URI env variable
        user (str): Neo4j username from NEO4J_USER env variable
        password (str): Neo4j password from NEO4J_PASSWORD env variable
        database (str): Neo4j database name from NEO4J_DATABASE env variable
                       (defaults to 'neo4j' if not specified)
        driver: Neo4j Python driver instance managing the connection pool
    """

    def __init__(self):
        """
        Initialize the query runner and establish connection to Neo4j.

        Loads credentials from .env file and creates a Neo4j driver instance.
        The driver maintains a connection pool and handles reconnection automatically.

        Environment Variables Required:
            NEO4J_URI: Connection URI (e.g., neo4j://localhost:7687)
            NEO4J_USER: Database username (typically 'neo4j')
            NEO4J_PASSWORD: Database password

        Environment Variables Optional:
            NEO4J_DATABASE: Target database name (defaults to 'neo4j')

        Raises:
            DriverError: If connection fails (wrong credentials, database not running, etc.)
        """
        # Load environment variables from .env file in project root
        # This reads NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
        load_dotenv()

        # Read connection parameters from environment
        # These are set by the user in their .env file
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')  # Default to 'neo4j' database

        # Create Neo4j driver connection
        # The driver manages a connection pool and handles reconnection
        # It works with all Neo4j versions (4.x, 5.x, 6.x)
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )

    def run(self, cypher, params=None):
        """
        Execute a single Cypher query and return all results.

        Use this method for:
        - Queries that return data (MATCH, RETURN)
        - Database introspection (CALL dbms.components())
        - Schema operations (CREATE CONSTRAINT, CREATE INDEX)
        - Small data operations (single node creation, updates)

        Do NOT use for bulk data loading - use run_batched() instead.

        Args:
            cypher (str): Cypher query to execute. Can be any valid Cypher statement.
            params (dict, optional): Query parameters as key-value pairs.
                                    Parameters are referenced in Cypher with $paramName.

        Returns:
            list: List of neo4j.Record objects containing query results.
                 Each record behaves like a dict with column names as keys.
                 Results are fully materialized before returning (safe to use after
                 this method returns, even though the session is closed).

        Example - Simple Query:
            query = Neo4jQuery()
            result = query.run("MATCH (n:Customer) RETURN count(n) as count")
            print(f"Found {result[0]['count']} customers")

        Example - Parameterized Query:
            result = query.run(
                "MATCH (c:Customer {id: $customerId}) RETURN c",
                params={'customerId': 'C001'}
            )
            if result:
                customer = result[0]['c']

        Example - Database Introspection:
            result = query.run("CALL dbms.components() YIELD name, versions")
            for record in result:
                print(f"{record['name']}: {record['versions']}")

        Note:
            Results are materialized (converted to a list) before the session closes.
            This means you can safely iterate over results after this method returns,
            but it also means all results are loaded into memory at once.

        Raises:
            ServiceUnavailable: If Neo4j is not running or connection fails
            CypherSyntaxError: If the Cypher query has syntax errors
            ConstraintError: If query violates constraints
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params or {})
            # Materialize results before session closes
            # This ensures the returned list is valid even after we exit the session context
            return list(result)

    def run_batched(self, cypher, data, batch_size=1000):
        """
        Execute a Cypher query repeatedly with batched data for efficient bulk loading.

        This is THE method to use for loading large amounts of data into Neo4j.
        It automatically chunks your data into manageable batches and executes
        the Cypher query once per batch, significantly improving performance.

        Why Batching Matters:
            Loading 100,000 records one at a time = 100,000 database round-trips (slow!)
            Loading in batches of 1000 = 100 database round-trips (fast!)

        How It Works:
            1. Takes your full dataset (e.g., 10,000 customer records)
            2. Splits it into batches (e.g., 10 batches of 1,000 records each)
            3. For each batch:
               - Passes batch as $batch parameter to your Cypher
               - Cypher uses UNWIND to process all records in the batch
               - One transaction per batch (efficient and safe)

        Critical Requirement:
            Your Cypher query MUST use $batch as the parameter name and
            start with UNWIND $batch. The toolkit will automatically pass
            each batch slice as the $batch parameter.

        Args:
            cypher (str): Cypher query that uses UNWIND $batch to process records.
                         Must reference $batch parameter and use UNWIND pattern.
            data (list): List of dictionaries to process. Each dict represents
                        one record (e.g., one CSV row, one customer, etc.).
            batch_size (int, optional): Number of records per batch. Default 1000.
                                       Larger batches = fewer round-trips but more memory.
                                       Typical range: 500-5000 depending on record size.

        Returns:
            None. Check logs for batch processing progress.

        Example - Loading Customer Nodes:
            customers = [
                {'id': 'C001', 'name': 'John Doe', 'email': 'john@example.com'},
                {'id': 'C002', 'name': 'Jane Smith', 'email': 'jane@example.com'},
                # ... 10,000 more customers
            ]

            cypher = '''
            UNWIND $batch AS row
            MERGE (c:Customer {id: row.id})
            SET c.name = row.name,
                c.email = row.email
            '''

            query = Neo4jQuery()
            query.run_batched(cypher, customers, batch_size=1000)
            # This executes 10 batches of 1000 customers each

        Example - Creating Relationships:
            relationships = [
                {'customer_id': 'C001', 'email': 'john@example.com'},
                {'customer_id': 'C002', 'email': 'jane@example.com'},
                # ... more relationships
            ]

            cypher = '''
            UNWIND $batch AS row
            MATCH (c:Customer {id: row.customer_id})
            MATCH (e:Email {address: row.email})
            MERGE (c)-[:HAS_EMAIL]->(e)
            '''

            query.run_batched(cypher, relationships, batch_size=1000)

        Logging:
            Logs batch progress at DEBUG level:
            "Processed batch 5/10 (1000 records)"

        Performance Notes:
            - Batch size of 1000 works well for most use cases
            - Increase to 2000-5000 for simple records (few properties)
            - Decrease to 500 for complex records (many properties, relationships)
            - Each batch is one transaction (atomic, consistent)

        Common Mistake:
            ❌ cypher = "MERGE (c:Customer {id: $id})"  # Wrong! No UNWIND $batch
            ✅ cypher = "UNWIND $batch AS row MERGE (c:Customer {id: row.id})"

        Raises:
            Warning: Logs warning if data list is empty
            ServiceUnavailable: If Neo4j connection fails during execution
            CypherSyntaxError: If Cypher query has syntax errors
        """
        if not data:
            log.warning("No data provided to run_batched")
            return

        # Calculate total number of batches for progress logging
        total_batches = (len(data) + batch_size - 1) // batch_size

        # Open a session for all batches (more efficient than session-per-batch)
        with self.driver.session(database=self.database) as session:
            # Process data in batches
            for i in range(0, len(data), batch_size):
                # Extract this batch's slice of data
                batch = data[i:i + batch_size]
                batch_num = i // batch_size + 1

                # Execute the Cypher with this batch as the $batch parameter
                # The Cypher query will UNWIND $batch and process all records
                session.run(cypher, {'batch': batch})

                # Log progress (only at DEBUG level to avoid clutter)
                log.debug(f"Processed batch {batch_num}/{total_batches} ({len(batch)} records)")

    def run_transaction(self, cypher_list):
        """
        Execute multiple Cypher statements as a single atomic transaction.

        Use this method when you need to ensure multiple operations succeed or
        fail together. All statements execute within one transaction - if any
        statement fails, the entire transaction rolls back automatically.

        When to Use This:
            - Setting up database schema (constraints + indexes together)
            - Multi-step data operations that must be atomic
            - Operations where you need all-or-nothing behavior

        When NOT to Use This:
            - Single queries → use run() instead
            - Bulk data loading → use run_batched() instead
            - Independent operations → run separately for better error isolation

        Args:
            cypher_list (list): List of (cypher, params) tuples to execute.
                              Each tuple is (str, dict) where:
                              - str is the Cypher query
                              - dict is the parameters (can be empty {})

        Returns:
            list: List of result objects, one per query in cypher_list.
                 Note: Results may not be fully materialized; consume
                 within the transaction if needed.

        Example - Schema Setup:
            query = Neo4jQuery()
            query.run_transaction([
                ("CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE", {}),
                ("CREATE INDEX customer_name IF NOT EXISTS FOR (n:Customer) ON (n.name)", {}),
                ("CREATE CONSTRAINT email_address IF NOT EXISTS FOR (e:Email) REQUIRE e.address IS UNIQUE", {})
            ])
            # All constraints created together, or none if any fails

        Example - Atomic Data Operation:
            query.run_transaction([
                ("MATCH (a:Account {id: $from_id}) SET a.balance = a.balance - $amount",
                 {'from_id': 'A001', 'amount': 100}),
                ("MATCH (a:Account {id: $to_id}) SET a.balance = a.balance + $amount",
                 {'from_id': 'A002', 'amount': 100})
            ])
            # Money transfer: both updates succeed or both fail (no partial transfer)

        Transaction Behavior:
            - All statements execute in order
            - If any statement fails, entire transaction rolls back
            - No partial state changes are visible to other connections
            - Automatic retry on transient failures (Neo4j driver handles this)

        Performance Note:
            Transactions lock resources. Keep transactions short and fast.
            Don't mix large data loads with transactions - use run_batched() instead.

        Raises:
            ServiceUnavailable: If Neo4j connection fails
            CypherSyntaxError: If any Cypher query has syntax errors
            ConstraintError: If any query violates constraints
            TransientError: Retried automatically by driver, but may eventually fail
        """
        def transaction_function(tx):
            """
            Inner function that executes within the transaction context.
            The Neo4j driver manages the transaction lifecycle automatically.
            """
            results = []
            for cypher, params in cypher_list:
                # Execute each query in sequence within the same transaction
                result = tx.run(cypher, params or {})
                results.append(result)
            return results

        with self.driver.session(database=self.database) as session:
            # execute_write ensures the transaction is a write transaction
            # and handles retries on transient failures
            return session.execute_write(transaction_function)

    def close(self):
        """
        Close the Neo4j driver connection and release all resources.

        This should be called when you're completely done with the query runner.
        The driver manages a connection pool, so closing it releases all pooled
        connections back to the database.

        When to Call This:
            - At the end of your data mapper script
            - In cleanup/finally blocks
            - When using the query runner as a context manager (automatic)

        Example - Manual Cleanup:
            query = Neo4jQuery()
            try:
                query.run("MATCH (n) RETURN count(n)")
            finally:
                query.close()  # Always clean up, even if query fails

        Example - Context Manager (Preferred):
            with Neo4jQuery() as query:
                query.run("MATCH (n) RETURN count(n)")
            # Automatically closed when exiting the 'with' block

        Note:
            You don't need to close sessions - those are managed automatically
            by the with statements in run(), run_batched(), etc.
        """
        if self.driver:
            self.driver.close()

    def __enter__(self):
        """
        Context manager entry point - enables 'with' statement usage.

        This allows using the query runner in a 'with' block, which
        automatically handles cleanup when the block exits.

        Returns:
            self: The query runner instance

        Example:
            with Neo4jQuery() as query:
                query.run("MATCH (n) RETURN count(n)")
                query.run_batched(cypher, data)
            # query.close() called automatically
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point - automatically closes the connection.

        Called automatically when exiting a 'with' block, even if an exception
        occurs. Ensures resources are always cleaned up properly.

        Args:
            exc_type: Exception type if an exception occurred, None otherwise
            exc_val: Exception value if an exception occurred, None otherwise
            exc_tb: Exception traceback if an exception occurred, None otherwise

        Returns:
            None: Allows exceptions to propagate normally
        """
        self.close()

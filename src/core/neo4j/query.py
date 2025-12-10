"""
Neo4j Query Runner
Version-agnostic Cypher query execution with batching support.

This module doesn't build Cypher queries - it just runs them.
The LLM-generated data_mapper.py provides the Cypher queries.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from ..logger import log


class Neo4jQuery:
    """
    Runs Cypher queries against Neo4j.

    This class is intentionally simple - it doesn't know about nodes,
    relationships, labels, or properties. It just runs Cypher.

    The LLM generates version-appropriate Cypher based on detected version.
    """

    def __init__(self):
        load_dotenv()
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )

    def run(self, cypher, params=None):
        """
        Execute a single Cypher query.

        Args:
            cypher: Cypher query string
            params: Optional dict of parameters

        Returns:
            list: List of records (materialized before session closes)

        Example:
            records = query.run("MATCH (n) RETURN count(n) as count")
            for record in records:
                print(record['count'])
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params or {})
            return list(result)  # Materialize before session closes

    def run_batched(self, cypher, data, batch_size=1000):
        """
        Execute Cypher query with batched data.

        The Cypher MUST use $batch as the parameter name.
        Data will be chunked and passed as $batch for each execution.

        Args:
            cypher: Cypher query that uses UNWIND $batch
            data: List of dicts to process
            batch_size: Number of records per batch (default 1000)

        Example:
            cypher = '''
            UNWIND $batch AS row
            MERGE (c:Customer {id: row.id})
            SET c += row
            '''
            query.run_batched(cypher, customers, batch_size=1000)
        """
        if not data:
            log.warning("No data provided to run_batched")
            return

        total_batches = (len(data) + batch_size - 1) // batch_size

        with self.driver.session(database=self.database) as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                batch_num = i // batch_size + 1

                session.run(cypher, {'batch': batch})

                log.debug(f"Processed batch {batch_num}/{total_batches} ({len(batch)} records)")

    def run_transaction(self, cypher_list):
        """
        Execute multiple Cypher statements in a single transaction.

        Args:
            cypher_list: List of (cypher, params) tuples

        Example:
            query.run_transaction([
                ("CREATE CONSTRAINT ...", {}),
                ("CREATE INDEX ...", {}),
                ("MATCH (n) DELETE n", {})
            ])
        """
        def transaction_function(tx):
            results = []
            for cypher, params in cypher_list:
                result = tx.run(cypher, params or {})
                results.append(result)
            return results

        with self.driver.session(database=self.database) as session:
            return session.execute_write(transaction_function)

    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.close()

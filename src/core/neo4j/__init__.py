"""Neo4j version detection and query execution utilities"""

from .version import get_neo4j_info, get_query
from .query import Neo4jQuery

__all__ = ['get_neo4j_info', 'get_query', 'Neo4jQuery']

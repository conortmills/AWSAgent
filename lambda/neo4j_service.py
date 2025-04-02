import os
import logging

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Neo4jService:
    _driver = None

    # ------ #
    # DRIVER #
    # ------ #
    @classmethod
    def initialize(cls):
        if cls._driver is not None:
            logger.warning("Neo4jService.initialize(): driver is already initialized.")
            return
        try:
            uri = os.environ.get('NEO4J_URI')
            username = os.environ.get('NEO4J_USERNAME')
            password = os.environ.get('NEO4J_PASSWORD')
            cls._driver = GraphDatabase.driver(uri, auth = (username, password))
            logger.info("Neo4jService.initialize(): driver initialized.")
        except Exception as e:
            logger.error(f"Neo4jService.initialize(): failed to initialize driver { str(e) }")
            raise

    @classmethod
    def close(cls):
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
            logger.info("Neo4jService.close(): driver closed.")
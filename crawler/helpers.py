# FILE: crawler/helpers.py
import logging
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance."""
    return logging.getLogger(name)

def get_utc_now_iso() -> str:
    """
    Returns current UTC date in ISO format (YYYY-MM-DD).
    Fixes DeprecationWarning for datetime.utcnow().
    """
    return datetime.now(timezone.utc).date().isoformat()

def transform_repo_node(node: Dict, query_context: str) -> Tuple:
    """
    Pure function: Transforms a raw GitHub GraphQL node into a clean DB tuple.
    
    Args:
        node: The dictionary returned by GitHub API.
        query_context: The query string used to find this repo (provenance).
    
    Returns:
        Tuple: (id, full_name, url, created_at, stars, source_slice)
    """
    return (
        node.get('databaseId'),
        node.get('nameWithOwner'),
        node.get('url'),
        node.get('createdAt'),
        node.get('stargazerCount'),
        query_context
    )
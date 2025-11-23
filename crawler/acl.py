# FILE: crawler/acl.py
import os
import time
import requests
from typing import Optional
from crawler.helpers import get_logger

logger = get_logger("ACL")

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

GQL_URL = "https://api.github.com/graphql"
MAX_RETRIES = 10 

class GraphQLError(Exception):
    pass

def _handle_rate_limit_headers(response):
    if 'retry-after' in response.headers:
        wait = int(response.headers.get('retry-after')) + 2
        logger.warning(f"🛑 Secondary Rate Limit. Sleeping {wait}s...")
        time.sleep(wait)
        return True

    remaining = response.headers.get('x-ratelimit-remaining')
    reset_at = response.headers.get('x-ratelimit-reset')

    if remaining and int(remaining) == 0 and reset_at:
        wait = int(reset_at) - int(time.time()) + 2
        if wait > 0:
            logger.warning(f"📉 Rate Limit Exhausted. Sleeping {wait}s...")
            time.sleep(wait)
            return True
    return False

def run_graphql(query: str, variables: dict):
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(GQL_URL, json={'query': query, 'variables': variables}, headers=HEADERS, timeout=60)
        except requests.RequestException as e:
            logger.error(f"Network error: {e}. Retrying...")
            time.sleep(2 ** attempt)
            continue

        if r.status_code == 200:
            payload = r.json()
            if 'errors' in payload and payload['errors'][0].get('type') == 'RATE_LIMITED':
                logger.warning("GraphQL 200 OK but body contains RATE_LIMITED.")
                time.sleep(60) 
                continue
            return payload

        elif r.status_code in (403, 429):
            if not _handle_rate_limit_headers(r):
                backoff = (2 ** attempt) + 5
                logger.warning(f"⚠️ Received {r.status_code}. Backoff {backoff}s...")
                time.sleep(backoff)
            continue

        elif r.status_code in (502, 503, 504):
            backoff = (2 ** attempt) + 1
            logger.warning(f"⚠️ Server error {r.status_code}. Backoff {backoff}s...")
            time.sleep(backoff)
            continue
            
        elif r.status_code == 401:
            raise GraphQLError("Unauthorized: check GITHUB_TOKEN")
        else:
            r.raise_for_status()

    raise GraphQLError("GraphQL query failed after MAX_RETRIES")

def ensure_rate_limit_sleep(rate_limit_dict: Optional[dict]):
    if not rate_limit_dict:
        return
    
    remaining = rate_limit_dict.get('remaining')
    if remaining is not None and remaining < 50:
        logger.info(f"⏳ Proactive sleep (Remaining: {remaining})")
        time.sleep(2)
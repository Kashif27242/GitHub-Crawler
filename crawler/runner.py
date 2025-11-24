# FILE: crawler/runner.py

import os
import math
from dotenv import load_dotenv

# Load env before imports
load_dotenv()

from crawler.acl import run_graphql, ensure_rate_limit_sleep
from crawler.graphql_queries import SEARCH_QUERY
from crawler.slicer import split_date_range
from crawler.db import get_conn, insert_staging_batch, upsert_from_staging
from crawler.config import RUN_MODE, TARGET, BATCH_SIZE
from crawler.helpers import get_logger, get_utc_now_iso, transform_repo_node

logger = get_logger("Runner")

def estimate_count(query_string):
    """Estimate total repositories for a query."""
    resp = run_graphql(SEARCH_QUERY, {"queryString": query_string, "cursor": None})
    if not resp or 'data' not in resp:
        return 0, None
    
    search = resp['data'].get('search') or {}
    rate = resp['data'].get('rateLimit')
    return search.get('repositoryCount', 0), rate

def paginate_slice_and_collect(query_string, conn):
    """Fetch repositories using cursor-based pagination."""
    cursor = None
    total = 0
    batch = []

    while True:
        resp = run_graphql(SEARCH_QUERY, {"queryString": query_string, "cursor": cursor})
        
        # Rate Limit Check
        rate = resp.get('data', {}).get('rateLimit') if resp.get('data') else None
        ensure_rate_limit_sleep(rate)

        if 'errors' in resp:
            logger.error(f"GraphQL Errors: {resp['errors']}")
            break

        nodes = resp.get('data', {}).get('search', {}).get('nodes', [])
        if not nodes:
            break

        for n in nodes:
            repo_tuple = transform_repo_node(n, query_string)
            batch.append(repo_tuple)
            total += 1
            
            if len(batch) >= BATCH_SIZE:
                insert_staging_batch(conn, batch)
                batch = []

        if batch:
            insert_staging_batch(conn, batch)
            batch = []

        pageInfo = resp['data']['search']['pageInfo']
        if not pageInfo.get('hasNextPage'):
            break
        cursor = pageInfo.get('endCursor')

    return total

def run():
    target = min(200, TARGET) if RUN_MODE == 'preview' else TARGET
    logger.info(f"🚀 Starting Crawler. Mode: {RUN_MODE}, Target: {target}")

    conn = get_conn()
    
    start = '2008-01-01'
    end = get_utc_now_iso()
    
    queue = [(start, end)]
    
    # --- METRICS DASHBOARD VARIABLES ---
    collected = 0
    total_points = 0
    total_requests = 0
    current_remaining = "Unknown" 

    while queue and collected < target:
        s, e = queue.pop(0)
        query_str = f"is:public created:{s}..{e}"
        
        # 1. SCOUT STEP (Costs 1 Point)
        count, rate = estimate_count(query_str)
        
        # Update Metrics
        total_points += 1
        total_requests += 1
        if rate:
            current_remaining = rate.get('remaining', 'Unknown')
            
        ensure_rate_limit_sleep(rate)

        if count == 0:
            continue

        if count > 1000:
            # Just log the overhead here
            logger.info(f"✂️ Splitting range {s}..{e} ({count} repos) | 💸 Cost: 1pt")
            split = split_date_range(s, e)
            if not split:
                # Fallback collection
                n = paginate_slice_and_collect(query_str, conn)
                
                # Calculate Cost (100 items = 1 Page = 1 Point)
                pages_cost = math.ceil(n / 100) if n > 0 else 1
                total_points += pages_cost
                total_requests += pages_cost
                
                collected += n
                upsert_from_staging(conn)
                continue
            
            left, right = split
            queue.insert(0, right)
            queue.insert(0, left)
            continue

        # 2. COLLECTION STEP
        n = paginate_slice_and_collect(query_str, conn)
        
        # Calculate Cost for this batch
        pages_cost = math.ceil(n / 100) if n > 0 else 1
        
        total_points += pages_cost
        total_requests += pages_cost
        collected += n
        
        upsert_from_staging(conn)
        
        # --- LIVE DASHBOARD LOG ---
        logger.info(
            f"📥 Collected: {collected}/{target} | "
            f"💸 Points Burned: {total_points} | "
            f"⛽ Fuel Remaining: {current_remaining}"
        )

    # FINAL SUMMARY REPORT
    logger.info("="*50)
    logger.info(f"🏁 RUN COMPLETE")
    logger.info(f"📚 Total Repos Collected: {collected}")
    logger.info(f"💳 Total API Points:      {total_points}")
    logger.info(f"📡 Total HTTP Requests:   {total_requests}")
    
    efficiency = collected / total_points if total_points > 0 else 0
    logger.info(f"⚡ Efficiency Score:      {efficiency:.2f} repos per point")
    logger.info("="*50)

if __name__ == '__main__':
    run()
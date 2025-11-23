GitHub Star Crawler

A clean-architecture Python crawler that retrieves repository star counts using GitHub's GraphQL API. It is designed for reliability, rate-limit handling, and efficient upserts into PostgreSQL.

Assignment Overview

This project fulfills the main assignment requirements:

* Uses the GraphQL API to fetch up to 100 repositories per request.
* Handles rate limits and network failures using exponential backoff.
* Ensures data consistency through an upsert strategy that prevents duplicates during repeated crawls.
* Includes a CI/CD pipeline with a PostgreSQL service container and CSV artifact uploads.


scaling to 500 Million Repositories

If this crawler needed to process 500 million repositories instead of 100,000, the current single-threaded architecture would be insufficient. Here is the re-architecture strategy:

  * **Decoupled Producer/Consumer:**
      * **Producer:** A single node runs the "Date Slicer" logic, pushing safe date ranges (e.g., "created:2020-01-01..2020-01-02") into a message queue (e.g., Kafka or AWS SQS).
      * **Consumers:** A fleet of worker nodes (Kubernetes Pods) pull date ranges from the queue and crawl them in parallel.
  * **Proxy Rotation & Token Pooling:**
      * GitHub limits are per-token/IP. We would manage a pool of authenticated tokens and route requests through a rotating proxy service to maximize throughput without hitting global rate limits.
  * **Database Sharding:**
      * A single Postgres writer cannot handle the write IOPS for 500M rows. We would shard the database horizontally based on `repo_id` (e.g., `repo_id % N`) or partition by time (`created_at`).
  * **Async I/O:**
      * Strict usage of `asyncio` / `aiohttp` to ensure workers are not blocked by network latency.

#### 2\. Schema Evolution for High-Frequency Metadata

To incorporate high-churn metadata like Issues, Pull Requests, and Comments (where a PR can get 10 comments today and 20 tomorrow), I would evolve the schema from a simple "Snapshot" model to an **Append-Only / Event-Sourcing** model to minimize row locking.

  * **Vertical Partitioning:**
      * **Static Data:** `repositories` table (Name, Created Date). Rarely updates.
      * **Volatile Data:** `repo_metrics` table (Stars, Forks). Updates daily.
  * **Append-Only Strategy for Activity:**
      * Instead of `UPDATE pull_requests SET comment_count = 20`, I would use an activity log table: `pr_events (id, pr_id, event_type, payload, created_at)`.
      * **Benefit:** `INSERT` is significantly faster than `UPDATE` in Postgres (no MVCC overhead or dead tuples), and it never locks the parent PR row.
      * **Reads:** Counts are aggregated asynchronously via Materialized Views.
  * **Hybrid Storage:**
      * For unstructured data like CI logs or large PR bodies, I would offload the content to Blob Storage (S3) or NoSQL, keeping Postgres lean for relational metadata.


Architecture and Design

The project is built using Clean Architecture principles with clear separation of responsibilities.

Module Structure

* crawler/acl.py
  Contains the Anti-Corruption Layer. Manages GitHub API interaction, authentication, retry logic, and standardized error handling.

* crawler/slicer.py
  Implements a date-slicing algorithm that recursively splits date ranges to avoid the 1000-result limit imposed by GitHub search.

* crawler/transformers.py
  Includes pure functions that transform API responses into database-ready rows.

* crawler/runner.py
  Coordinates the workflow between the API layer, the slicer, and the database using a memory-efficient generator pattern.

Database Strategy

A staging-table approach is used for reliable and fast writes:

1. Extract: Insert crawled data into the repo_staging table in batches.
2. Load: Upsert data from repo_staging into the repositories and repo_stars tables in a single transaction.
3. Clean: Truncate the staging table after successful completion.

Here is a **clean, simple, step-by-step “How to Run Locally”** section for your README.
No emojis, no markdown clutter, no unnecessary formatting — just clear steps.

---

## How to Run Locally

### Requirements

* Python 3.11 or newer
* PostgreSQL (version 13+ recommended)

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/github-crawler-assignment.git
   cd github-crawler-assignment
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Linux/Mac
   venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a PostgreSQL database**

   ```bash
   createdb github
   ```

   Or using psql:

   ```sql
   CREATE DATABASE github;
   ```

5. **Set environment variables**
   Create a file named `.env` in the project root:

   ```
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/github
   GITHUB_TOKEN=ghp_your_personal_token_here
   RUN_MODE=preview        # Use 'prod' for full crawling
   TARGET=1000             # Number of repositories to crawl
   ```

6. **Run database migrations**
   On the first run, the crawler will automatically detect that tables are missing and load `sql/migrations.sql`.
   You do not need to run anything manually unless you want to.

7. **Run the crawler**

   ```bash
   python -m crawler.runner
   ```

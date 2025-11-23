GitHub Star Crawler

A clean-architecture Python crawler that retrieves repository star counts using GitHub's GraphQL API. It is designed for reliability, rate-limit handling, and efficient upserts into PostgreSQL.

Assignment Overview

This project fulfills the main assignment requirements:

* Uses the GraphQL API to fetch up to 100 repositories per request.
* Handles rate limits and network failures using exponential backoff.
* Ensures data consistency through an upsert strategy that prevents duplicates during repeated crawls.
* Includes a CI/CD pipeline with a PostgreSQL service container and CSV artifact uploads.

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

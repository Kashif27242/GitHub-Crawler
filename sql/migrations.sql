-- Repositories table: stores basic repo metadata
CREATE TABLE IF NOT EXISTS repositories (
    id BIGINT PRIMARY KEY,                      -- GitHub databaseId
    full_name TEXT NOT NULL,                     -- owner/name
    created_at TIMESTAMP WITH TIME ZONE,        -- repo creation date
    updated_at TIMESTAMP WITH TIME ZONE,        -- last updated in GitHub
    last_crawled TIMESTAMP WITH TIME ZONE,      -- last time crawled
    language TEXT,                              -- primary language
    is_fork BOOLEAN,                            -- forked repo?
    is_archived BOOLEAN                          -- archived repo?
);

-- Index on repo full_name for faster lookups
CREATE INDEX IF NOT EXISTS idx_repositories_fullname ON repositories(full_name);

-- Current star count table
CREATE TABLE IF NOT EXISTS repo_stars (
    repo_id BIGINT PRIMARY KEY REFERENCES repositories(id) ON DELETE CASCADE,
    stars INTEGER NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Historical star counts over time
CREATE TABLE IF NOT EXISTS repo_star_history (
    id BIGSERIAL PRIMARY KEY,
    repo_id BIGINT REFERENCES repositories(id) ON DELETE CASCADE,
    stars INTEGER NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Staging table for batch inserts
CREATE TABLE IF NOT EXISTS repo_staging (
    repo_id BIGINT,
    full_name TEXT,
    url TEXT,
    created_at TIMESTAMPTZ,
    stars INTEGER,
    source_slice TEXT
);

# FILE: crawler/graphql_queries.py

SEARCH_QUERY = """
query ($queryString: String!, $cursor: String) {
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
  search(query: $queryString, type: REPOSITORY, first: 100, after: $cursor) {
    repositoryCount
    pageInfo { endCursor hasNextPage }
    nodes {
      ... on Repository {
        id
        databaseId
        nameWithOwner
        url
        stargazerCount
        createdAt
      }
    }
  }
}
"""

REPO_QUERY = """
query ($owner: String!, $name: String!) {
  rateLimit { limit cost remaining resetAt }
  repository(owner: $owner, name: $name) {
    id
    databaseId
    nameWithOwner
    url
    stargazerCount
    createdAt
    updatedAt
  }
}
"""

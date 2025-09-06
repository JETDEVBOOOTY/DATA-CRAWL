# API usage examples (curl)

# Start crawl (requires API_KEY in Authorization header)
curl -X POST https://your.domain.tld/api/crawl/start \\
  -H "Authorization: Bearer <API_KEY>" \\
  -H "Content-Type: application/json" \\
  -d '{ "starts": ["https://example.com"], "allow_domains": ["example.com"], "max_pages": 50 }'

# Check status
curl https://your.domain.tld/api/crawl/status -H "Authorization: Bearer <API_KEY>"

# List items (public or protected depending on server config)
curl https://your.domain.tld/api/items?limit=50 -H "Authorization: Bearer <API_KEY>"

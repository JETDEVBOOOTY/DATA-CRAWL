# backend/app/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class CrawlRequest(BaseModel):
    starts: Optional[List[str]] = []
    allow_domains: List[str]
    max_pages: Optional[int] = 200
    max_depth: Optional[int] = 2
    concurrency: Optional[int] = 6
    delay: Optional[float] = 1.0
    include_regex: Optional[str] = None
    exclude_regex: Optional[str] = None

class CrawlStatus(BaseModel):
    running: bool
    pages_fetched: int
    total_items: int

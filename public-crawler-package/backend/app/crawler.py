# backend/app/crawler.py
import asyncio, time, re
from urllib.parse import urlparse, urljoin, urldefrag
import aiohttp
from html.parser import HTMLParser
from datetime import datetime, timezone
from .db import DB

USER_AGENT = "PublicCrawler/1.0 (+https://example.org; polite; contact=you@example.org)"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.buf = []
        self.in_script = 0
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript"): self.in_script += 1
        if tag == "title": self._in_title = True

    def handle_endtag(self, tag):
        if tag in ("script","style","noscript") and self.in_script>0: self.in_script -= 1
        if tag == "title": self._in_title = False

    def handle_data(self, data):
        if self.in_script: return
        if self._in_title:
            if self.title is None: self.title = data.strip()[:300]
            return
        text = data.strip()
        if text: self.buf.append(text+" ")

    def get_text(self):
        import re
        text = ''.join(self.buf)
        return re.sub(r"\\s+"," ", text).strip()

def html_to_text(html: str):
    p = TextExtractor()
    p.feed(html)
    return p.title, p.get_text()

class SimpleRobots:
    def __init__(self):
        self.cache = {}

    async def can_fetch(self, session, url, user_agent=USER_AGENT):
        # Simplified: attempt to fetch robots.txt but don't block strongly on parse errors.
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base in self.cache:
            return True
        robots_url = urljoin(base, "/robots.txt")
        try:
            async with session.get(robots_url, timeout=8, headers={"User-Agent": user_agent}) as r:
                if r.status == 200:
                    txt = await r.text()
                    self.cache[base] = txt
        except Exception:
            pass
        return True

class DomainLimiter:
    def __init__(self, delay=1.0):
        self.delay = max(0.0, delay)
        self.last = {}
        self.locks = {}

    async def wait(self, host):
        if host not in self.locks:
            self.locks[host] = asyncio.Lock()
        async with self.locks[host]:
            now = time.time()
            last = self.last.get(host, 0.0)
            need = self.delay - (now - last)
            if need > 0:
                await asyncio.sleep(need)
            self.last[host] = time.time()

class PublicCrawler:
    def __init__(self, db: DB, starts, allow_domains, max_pages=200, max_depth=2,
                 concurrency=6, delay=1.0, timeout=15, include_re=None, exclude_re=None):
        if not allow_domains:
            raise ValueError("allow_domains required")
        self.db = db
        self.starts = starts
        self.allow_domains = {d.lower() for d in allow_domains}
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.delay = delay
        self.timeout = timeout
        self.include_re = re.compile(include_re) if include_re else None
        self.exclude_re = re.compile(exclude_re) if exclude_re else None
        self.seen = set()
        self.queue = asyncio.Queue()
        self.robots = SimpleRobots()
        self.limiter = DomainLimiter(delay)
        self.pages_fetched = 0
        self._stop = False

    def _normalize(self, url: str):
        url, _ = urldefrag(url)
        p = urlparse(url)
        if not p.scheme:
            url = "http://" + url
        if url.endswith("/") and "?" not in url:
            url = url[:-1]
        return url

    def _allowed_domain(self, url):
        try:
            host = urlparse(url).netloc.lower()
            return any(host == d or host.endswith("." + d) for d in self.allow_domains)
        except Exception:
            return False

    def _passes_filters(self, url):
        if self.include_re and not self.include_re.search(url): return False
        if self.exclude_re and self.exclude_re.search(url): return False
        return True

    async def _enqueue(self, url, depth):
        url = self._normalize(url)
        if url in self.seen: return
        if depth > self.max_depth: return
        if not self._allowed_domain(url): return
        if not self._passes_filters(url): return
        self.seen.add(url)
        await self.queue.put((url, depth))

    async def _fetch(self, session, url):
        if not await self.robots.can_fetch(session, url):
            return None
        p = urlparse(url)
        await self.limiter.wait(p.netloc)
        try:
            async with session.get(url, timeout=self.timeout, headers={"User-Agent": USER_AGENT}) as r:
                ctype = r.headers.get("Content-Type","")
                if r.status != 200 or "text/html" not in ctype:
                    return None
                body = await r.text(errors="ignore")
                return r.url, r.status, ctype, body
        except Exception:
            return None

    def _extract_links(self, base, html):
        hrefs = re.findall(r'href=[\\'\\\"](.*?)[\\'\\\"]', html, re.IGNORECASE)
        links = []
        for h in hrefs:
            if h.startswith("mailto:") or h.startswith("javascript:"): continue
            links.append(urljoin(base, h))
        return links

    async def _worker(self, session):
        while not self._stop and self.pages_fetched < self.max_pages:
            try:
                url, depth = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                return
            res = await self._fetch(session, url)
            if not res:
                continue
            fetched_url, status, ctype, html = res
            title, text = html_to_text(html)
            item = {
                "url": str(fetched_url),
                "status": status,
                "content_type": ctype,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "title": title,
                "text": text[:20000]
            }
            await self.db.insert_item(item)
            self.pages_fetched += 1
            links = self._extract_links(str(fetched_url), html)
            next_depth = depth + 1
            if next_depth <= self.max_depth:
                for h in links:
                    try:
                        await self._enqueue(h, next_depth)
                    except Exception:
                        pass

    async def run(self):
        async with aiohttp.ClientSession() as session:
            for s in self.starts:
                await self._enqueue(s, 0)
            workers = [asyncio.create_task(self._worker(session)) for _ in range(self.concurrency)]
            await asyncio.gather(*workers)

# backend/app/main.py
import os, asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from .db import DB
from .crawler import PublicCrawler
from .schemas import CrawlRequest, CrawlStatus
from starlette.responses import JSONResponse

app = FastAPI(title="Public Crawler API")

# Load config from env
API_KEY = os.getenv("API_KEY", "changeme")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["*"], allow_headers=["*"])

db = DB(path=os.getenv("DATABASE_PATH", "/data/data.db"))
asyncio.get_event_loop().run_until_complete(db.init())

_crawler_task = None
_crawler_obj = None

def require_api_key(request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    token = auth.split(" ",1)[1].strip()
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

@app.post("/api/crawl/start", response_model=CrawlStatus, dependencies=[Depends(require_api_key)])
async def start_crawl(req: CrawlRequest):
    global _crawler_task, _crawler_obj
    if _crawler_task and not _crawler_task.done():
        raise HTTPException(status_code=400, detail="A crawl is already running")
    if not req.allow_domains:
        raise HTTPException(status_code=400, detail="allow_domains required")
    _crawler_obj = PublicCrawler(db=db,
                                 starts=req.starts or [],
                                 allow_domains=req.allow_domains,
                                 max_pages=req.max_pages or 200,
                                 max_depth=req.max_depth or 2,
                                 concurrency=req.concurrency or 6,
                                 delay=req.delay or 1.0,
                                 include_re=req.include_regex,
                                 exclude_re=req.exclude_regex)
    async def runner():
        try:
            await _crawler_obj.run()
        except Exception as e:
            print("Crawler error:", e)
    _crawler_task = asyncio.create_task(runner())
    return CrawlStatus(running=True, pages_fetched=0, total_items=await db.count())

@app.get("/api/crawl/status", response_model=CrawlStatus)
async def crawl_status():
    global _crawler_task, _crawler_obj
    running = _crawler_task is not None and not _crawler_task.done()
    pages = getattr(_crawler_obj, "pages_fetched", 0) if _crawler_obj else 0
    total = await db.count()
    return CrawlStatus(running=running, pages_fetched=pages, total_items=total)

@app.post("/api/crawl/stop", dependencies=[Depends(require_api_key)])
async def stop_crawl():
    global _crawler_task, _crawler_obj
    if _crawler_task and not _crawler_task.done():
        _crawler_obj._stop = True
        await _crawler_task
    return {"stopped": True}

@app.get("/api/items")
async def list_items(limit: int = 100, offset: int = 0, q: str = None):
    items = await db.list_items(limit=limit, offset=offset, q=q)
    return {"items": items, "count": await db.count()}

@app.get("/api/items/download")
async def download_all():
    rows = await db.list_items(limit=1000000, offset=0, q=None)
    import json
    content = "\\n".join(json.dumps(r["raw"], ensure_ascii=False) for r in rows)
    return JSONResponse(content=content)

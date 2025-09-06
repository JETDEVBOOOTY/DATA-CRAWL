# backend/app/db.py
import aiosqlite, json, os

class DB:
    def __init__(self, path="/data/data.db"):
        self.path = path
        self._init_done = False
        self.conn = None

    async def init(self):
        if self._init_done: return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._init_done = True
        self.conn = await aiosqlite.connect(self.path)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                fetched_at TEXT,
                content_type TEXT,
                title TEXT,
                text TEXT,
                raw JSON
            )
        """)
        await self.conn.commit()

    async def insert_item(self, item: dict):
        await self.conn.execute(
            "INSERT INTO items(url,fetched_at,content_type,title,text,raw) VALUES (?,?,?,?,?,?)",
            (item.get("url"), item.get("fetched_at"), item.get("content_type"),
             item.get("title"), item.get("text"), json.dumps(item, ensure_ascii=False))
        )
        await self.conn.commit()

    async def list_items(self, limit=100, offset=0, q=None):
        sql = "SELECT id,url,fetched_at,content_type,title,text,raw FROM items"
        params = []
        if q:
            sql += " WHERE url LIKE ? OR title LIKE ? OR text LIKE ?"
            qparam = f"%{q}%"
            params.extend([qparam,qparam,qparam])
        sql += " ORDER BY fetched_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur = await self.conn.execute(sql, params)
        rows = await cur.fetchall()
        return [dict(id=r[0], url=r[1], fetched_at=r[2], content_type=r[3], title=r[4], text=r[5], raw=json.loads(r[6])) for r in rows]

    async def count(self):
        cur = await self.conn.execute("SELECT COUNT(*) FROM items")
        r = await cur.fetchone()
        return r[0] if r else 0

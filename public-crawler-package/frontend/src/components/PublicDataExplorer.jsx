// frontend/src/components/PublicDataExplorer.jsx
import React, { useState, useMemo, useRef } from "react";

export default function PublicDataExplorer({ apiBase=null }) {
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState("");
  const [domainFilter, setDomainFilter] = useState("");
  const [groupBy, setGroupBy] = useState("none");
  const [regexMode, setRegexMode] = useState(false);
  const fileInputRef = useRef(null);

  function parseJSONL(text) {
    const lines = text.split(/\\r?\\n/).map(l=>l.trim()).filter(Boolean);
    const parsed = [];
    for (const l of lines) {
      try { parsed.push(JSON.parse(l)); } catch (e) {}
    }
    return parsed;
  }

  function handleFile(e) {
    const f = e.target.files?.[0]; if (!f) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = String(ev.target.result || "");
      let parsed = [];
      try {
        const j = JSON.parse(text);
        if (Array.isArray(j)) parsed = j; else parsed = [j];
      } catch (err) {
        parsed = parseJSONL(text);
      }
      const normalized = parsed.map((it, idx)=>({...it, __id:(it.url||'item')+'::'+idx}));
      setItems(normalized);
    };
    reader.readAsText(f);
  }

  const filtered = useMemo(()=>{
    let res = items;
    if (domainFilter) res = res.filter(it=>{ try{ return new URL(it.url).hostname.includes(domainFilter);}catch(e){return false}});
    if (query) {
      if (regexMode) {
        try { const r = new RegExp(query,'i'); res = res.filter(it=>r.test(it.text||'')||r.test(it.title||'')||r.test(it.url||'')); } catch(e){}
      } else {
        const q = query.toLowerCase(); res = res.filter(it=>((it.text||'')+' '+(it.title||'')+' '+(it.url||'')).toLowerCase().includes(q));
      }
    }
    return res;
  }, [items, domainFilter, query, regexMode]);

  function exportCSV() {
    const rows = filtered.map(it=>({url: it.url, title: it.title, text: it.text, fetched_at: it.fetched_at, content_type: it.content_type}));
    if (!rows.length) return;
    const header = Object.keys(rows[0]).join(',') + '\\n';
    const csv = header + rows.map(r=>Object.values(r).map(v=>'\"'+String(v||'').replace(/\"/g,'\"\"')+'\"').join(',')).join('\\n');
    const blob = new Blob([csv], {type: 'text/csv;charset=utf-8;'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'export.csv'; a.click(); URL.revokeObjectURL(url);
  }

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Explorateur de données publiques</h1>
        <div className="flex gap-2">
          <label className="flex items-center gap-2 bg-white border rounded px-3 py-2 shadow-sm cursor-pointer">
            <input ref={fileInputRef} type="file" accept=".json,.jsonl,.txt" onChange={handleFile} className="hidden" />
            <span>Load JSON / JSONL</span>
          </label>
          <button onClick={exportCSV} className="bg-slate-800 text-white px-3 py-2 rounded">Export CSV</button>
        </div>
      </header>
      <section className="grid grid-cols-4 gap-4">
        <aside className="col-span-1 bg-white p-3 rounded shadow-sm">
          <div className="mb-3">
            <label className="text-sm font-medium">Search</label>
            <input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="text or regex" className="w-full mt-1 p-2 border rounded" />
            <div className="flex items-center gap-2 mt-2 text-sm">
              <label className="flex items-center gap-1"><input type="checkbox" checked={regexMode} onChange={(e)=>setRegexMode(e.target.checked)} /> Regex</label>
            </div>
          </div>
          <div className="mb-3">
            <label className="text-sm font-medium">Domain</label>
            <input value={domainFilter} onChange={(e)=>setDomainFilter(e.target.value)} placeholder="filter by domain substring" className="w-full mt-1 p-2 border rounded" />
          </div>
          <div className="mb-3">
            <label className="text-sm font-medium">Group by</label>
            <select value={groupBy} onChange={(e)=>setGroupBy(e.target.value)} className="w-full mt-1 p-2 border rounded">
              <option value="none">None</option>
              <option value="domain">Domain</option>
            </select>
          </div>
        </aside>
        <main className="col-span-3">
          <div className="space-y-3">
            {filtered.slice(0,200).map((it,idx)=>(
              <div key={it.__id||idx} className="bg-white p-3 rounded shadow-sm flex gap-3">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <a href={it.url} target="_blank" rel="noreferrer" className="text-sky-600 font-medium">{it.title||it.url}</a>
                    <div className="text-xs text-slate-500">{it.fetched_at}</div>
                  </div>
                  <div className="text-sm text-slate-700 mt-2 line-clamp-4">{it.text}</div>
                </div>
              </div>
            ))}
            {filtered.length===0 && <div className="bg-white p-4 rounded shadow-sm text-slate-500">No items. Load a JSON/JSONL file.</div>}
          </div>
        </main>
      </section>
    </div>
  );
}

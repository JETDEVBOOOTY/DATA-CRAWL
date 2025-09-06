// frontend/src/App.jsx
import React from 'react';
import PublicDataExplorer from './components/PublicDataExplorer';

export default function App(){
  return (
    <div>
      <header className="p-4 bg-slate-900 text-white">
        <h1 className="text-xl">Public Crawler — UI</h1>
      </header>
      <main className="p-4">
        <PublicDataExplorer />
      </main>
    </div>
  );
}

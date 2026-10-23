import React, { useEffect, useState } from 'react';
import Icon from '../components/Icon.jsx';
import useScrollReveal from '../hooks/useScrollReveal.js';
import { API_BASE_URL } from '../services/api.js';

const HISTORY_API = `${API_BASE_URL}/history`;

export default function History() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [filterRisk, setFilterRisk] = useState('all');
  const [sortKey, setSortKey] = useState('created_at');
  const [sortDir, setSortDir] = useState('desc');
  const tableRef = useScrollReveal();

  useEffect(() => {
    let mounted = true;
    async function fetchHistory() {
      try {
        const res = await fetch(HISTORY_API);
        if (!res.ok) throw new Error('Failed to fetch history');
        const data = await res.json();
        if (mounted) setRecords(data);
      } catch (err) {
        if (mounted) setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchHistory();
    // Refresh every 60s
    const interval = setInterval(fetchHistory, 60000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const filtered = records
    .filter((r) => {
      const q = search.toLowerCase();
      const matchesSearch = (r.sender?.toLowerCase() || '').includes(q) || (r.prediction?.toLowerCase() || '').includes(q);
      const matchesRisk = filterRisk === 'all' || r.risk_level === filterRisk;
      return matchesSearch && matchesRisk;
    })
    .sort((a, b) => {
      const aVal = a[sortKey] || '';
      const bVal = b[sortKey] || '';
      const cmp = typeof aVal === 'string' ? aVal.localeCompare(bVal) : aVal - bVal;
      return sortDir === 'asc' ? cmp : -cmp;
    });

  function toggleSort(key) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  }

  function SortIcon({ columnKey }) {
    if (sortKey !== columnKey) return <Icon name="chevronRight" size={12} className="rotate-90 opacity-0 group-hover:opacity-40" />;
    return <Icon name="chevronRight" size={12} className={`opacity-60 transition ${sortDir === 'asc' ? '-rotate-90' : 'rotate-90'}`} />;
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 md:px-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 rounded-lg bg-surface-300" />
          <div className="h-12 rounded-xl bg-surface-300" />
          <div className="h-64 rounded-xl bg-surface-300" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 md:px-6">
        <div className="rounded-xl border border-danger-50 bg-danger-50 p-8 text-center">
          <p className="font-bold text-danger-700">Failed to load history</p>
          <p className="mt-1 text-sm text-danger-700/80">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={tableRef} className="reveal mx-auto max-w-7xl animate-fade-in-up px-4 py-16 md:px-6">
      {/* Header */}
      <div className="mb-8 animate-slide-up">
        <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-semibold text-primary-500">
          <span className="h-2 w-2 rounded-full bg-primary-500" />
          Scan History
        </span>
        <h1 className="mt-4 text-3xl font-bold text-text-primary">History</h1>
        <p className="mt-2 text-text-secondary">Browse, search, and filter all previous email scans.</p>
        <p className="mt-1 text-xs text-text-disabled">{records.length} total records</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div className="relative flex-1">
          <Icon name="search" size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-disabled" />
          <input
            type="text"
            placeholder="Search sender or prediction..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-surface-300 bg-white py-2.5 pl-10 pr-4 text-sm text-text-primary outline-none anim-standard focus:border-primary-500 focus:ring-2 focus:ring-primary-50"
          />
        </div>
        <select
          value={filterRisk}
          onChange={(e) => setFilterRisk(e.target.value)}
          className="w-full rounded-xl border border-surface-300 bg-white px-4 py-2.5 text-sm text-text-primary outline-none anim-standard focus:border-primary-500 focus:ring-2 focus:ring-primary-50 sm:w-44"
        >
          <option value="all">All Risks</option>
          <option value="high">High Risk</option>
          <option value="medium">Medium Risk</option>
          <option value="low">Low Risk</option>
        </select>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="animate-scale-in rounded-xl border border-surface-300 bg-white p-16 text-center">
          <Icon name="history" size={40} className="mx-auto text-text-disabled" />
          <p className="mt-4 font-medium text-text-secondary">
            {records.length === 0 ? 'No scans performed yet' : 'No results match your filters'}
          </p>
          <p className="mt-1 text-sm text-text-disabled">
            {records.length === 0 ? 'Scan an email on the Home page to see results here.' : 'Try adjusting your search or filter.'}
          </p>
        </div>
      ) : (
        <div className="animate-scale-in overflow-hidden rounded-xl border border-surface-300 bg-white shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] text-left text-sm">
              <thead>
                <tr className="border-b border-surface-200 bg-surface-50 text-xs font-semibold uppercase tracking-wider text-text-disabled">
                  <th className="cursor-pointer px-5 py-4 group anim-fast hover:bg-surface-100" onClick={() => toggleSort('sender')}>
                    <span className="inline-flex items-center gap-1">Sender <SortIcon columnKey="sender" /></span>
                  </th>
                  <th className="cursor-pointer px-5 py-4 group anim-fast hover:bg-surface-100" onClick={() => toggleSort('prediction')}>
                    <span className="inline-flex items-center gap-1">Prediction <SortIcon columnKey="prediction" /></span>
                  </th>
                  <th className="cursor-pointer px-5 py-4 group anim-fast hover:bg-surface-100" onClick={() => toggleSort('risk_score')}>
                    <span className="inline-flex items-center gap-1">Risk score <SortIcon columnKey="risk_score" /></span>
                  </th>
                  <th className="cursor-pointer px-5 py-4 group anim-fast hover:bg-surface-100" onClick={() => toggleSort('risk_level')}>
                    <span className="inline-flex items-center gap-1">Risk <SortIcon columnKey="risk_level" /></span>
                  </th>
                  <th className="cursor-pointer px-5 py-4 group anim-fast hover:bg-surface-100" onClick={() => toggleSort('created_at')}>
                    <span className="inline-flex items-center gap-1">Date <SortIcon columnKey="created_at" /></span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => (
                  <tr key={i} className="animate-slide-up border-b border-surface-100 text-text-primary anim-fast hover:bg-surface-50" style={{ animationDelay: `${i * 40}ms` }}>
                    <td className="max-w-[200px] truncate px-5 py-3.5 text-text-secondary">{r.sender || 'Unknown'}</td>
                    <td className="px-5 py-3.5">
                      <span className={`inline-block rounded-md px-2.5 py-0.5 text-xs font-semibold ${
                        r.prediction === 'Phishing Email' || r.prediction === 'phishing'
                          ? 'bg-danger-50 text-danger-700'
                          : r.prediction === 'Suspicious Email'
                          ? 'bg-suspicious-50 text-suspicious-700'
                          : 'bg-safe-50 text-safe-700'
                      }`}>
                        {r.prediction}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-semibold text-primary-500">{r.risk_score}%</td>
                    <td className="px-5 py-3.5">
                      <span className={`inline-block rounded-md px-2.5 py-0.5 text-xs font-semibold ${
                        r.risk_level === 'high' ? 'bg-danger-50 text-danger-700'
                        : r.risk_level === 'medium' ? 'bg-suspicious-50 text-suspicious-700'
                        : 'bg-safe-50 text-safe-700'
                      }`}>{r.risk_level}</span>
                    </td>
                    <td className="px-5 py-3.5 text-text-disabled">{r.created_at || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-surface-200 px-5 py-3 text-xs text-text-disabled">
            {filtered.length} of {records.length} records
          </div>
        </div>
      )}
    </div>
  );
}

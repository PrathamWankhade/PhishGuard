import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import useScrollReveal from '../hooks/useScrollReveal.js';
import useCountUp from '../hooks/useCountUp.js';
import Icon from '../components/Icon.jsx';


const DASHBOARD_API = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/dashboard`
  : 'http://127.0.0.1:8000/api/v1/dashboard';

const HISTORY_API = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/history`
  : 'http://127.0.0.1:8000/api/v1/history';

const FALLBACK_DATA = {
  total_scans: 12847, phishing_count: 3421, safe_count: 8156, suspicious_count: 1270,
  avg_risk_score: 94.7, risk_levels: { high: 1892, medium: 2150, low: 8805 },
  trend: { scans: 12, phishing: -3, safe: 8, risk_score: 1.2 },
  daily_trend: [
    { day: 'Mon', scans: 42, threats: 12 }, { day: 'Tue', scans: 58, threats: 18 },
    { day: 'Wed', scans: 35, threats: 9 }, { day: 'Thu', scans: 71, threats: 22 },
    { day: 'Fri', scans: 49, threats: 14 }, { day: 'Sat', scans: 28, threats: 6 },
    { day: 'Sun', scans: 63, threats: 20 },
  ],
  top_signals: [
    { name: 'Urgent Language', count: 892, severity: 'High' },
    { name: 'Suspicious URL', count: 754, severity: 'High' },
    { name: 'Credential Request', count: 621, severity: 'Critical' },
    { name: 'Spoofed Sender', count: 487, severity: 'Critical' },
    { name: 'Suspicious Attachment', count: 312, severity: 'High' },
  ],
  recent: [
    { id: 1, sender: 'security@bank-verify.com', prediction: 'Phishing Email', confidence: 97, risk_level: 'high', created_at: '2 min ago' },
    { id: 2, sender: 'support@amazon-order.net', prediction: 'Phishing Email', confidence: 92, risk_level: 'high', created_at: '15 min ago' },
    { id: 3, sender: 'hr@company-payroll.com', prediction: 'Suspicious Email', confidence: 78, risk_level: 'medium', created_at: '1 hour ago' },
    { id: 4, sender: 'newsletter@medium.com', prediction: 'Safe Email', confidence: 99, risk_level: 'low', created_at: '3 hours ago' },
  ],
  history: [
    { sender: 'security@bank-verify.com', prediction: 'Phishing Email', confidence: 97, risk_level: 'high', created_at: '2026-06-29' },
    { sender: 'support@amazon-order.net', prediction: 'Phishing Email', confidence: 92, risk_level: 'high', created_at: '2026-06-29' },
    { sender: 'hr@company-payroll.com', prediction: 'Suspicious Email', confidence: 78, risk_level: 'medium', created_at: '2026-06-28' },
    { sender: 'admin@dropbox-share.com', prediction: 'Phishing Email', confidence: 88, risk_level: 'high', created_at: '2026-06-28' },
    { sender: 'newsletter@medium.com', prediction: 'Safe Email', confidence: 99, risk_level: 'low', created_at: '2026-06-27' },
    { sender: 'no-reply@linkedin.com', prediction: 'Safe Email', confidence: 96, risk_level: 'low', created_at: '2026-06-27' },
    { sender: 'billing@netflix-support.cc', prediction: 'Phishing Email', confidence: 94, risk_level: 'high', created_at: '2026-06-26' },
    { sender: 'team@figma-notification.com', prediction: 'Safe Email', confidence: 98, risk_level: 'low', created_at: '2026-06-26' },
  ],
};

const PIE_COLORS = { phishing: '#d32f2f', suspicious: '#ff8f00', safe: '#43a047' };
const SEVERITY_COLORS = { Critical: 'bg-danger-500', High: 'bg-suspicious-500', Medium: 'bg-suspicious-50 text-suspicious-700 border border-suspicious-500/30', Low: 'bg-surface-200 text-text-secondary' };

const chartTooltipStyle = {
  backgroundColor: '#fff',
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  color: '#212121',
  fontSize: '13px',
  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
};

function StatCard({ icon, title, value, suffix = '', trend, trendLabel, color = 'primary', visible }) {
  const num = typeof value === 'number' ? value : parseFloat(String(value).replace(/[^0-9.]/g, '')) || 0;
  const count = useCountUp(num, { duration: 900, enabled: visible });
  const colorMap = { primary: 'text-primary-500 bg-primary-50', danger: 'text-danger-500 bg-danger-50', safe: 'text-safe-500 bg-safe-50', warning: 'text-suspicious-500 bg-suspicious-50' };
  const iconBg = colorMap[color] || colorMap.primary;
  const displayVal = num >= 1000 && Number.isInteger(num) ? count.toLocaleString() : count;

  return (
    <div className="hover-lift rounded-xl border border-surface-300 bg-white p-5 shadow-card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium uppercase tracking-wider text-text-disabled">{title}</p>
          <p className={`mt-2 text-3xl font-bold ${color === 'primary' ? 'text-primary-500' : color === 'danger' ? 'text-danger-500' : color === 'safe' ? 'text-safe-500' : 'text-suspicious-500'}`}>
            {displayVal}{suffix}
          </p>
        </div>
        <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${iconBg}`}>
          <Icon name={icon} size={20} />
        </div>
      </div>
      {trend !== undefined && (
        <div className="mt-3 flex items-center gap-1.5">
          <span className={`inline-flex items-center gap-0.5 rounded-md px-2 py-0.5 text-xs font-semibold ${trend >= 0 ? 'bg-safe-50 text-safe-700' : 'bg-danger-50 text-danger-700'}`}>
            <Icon name={trend >= 0 ? 'arrowUp' : 'arrowDown'} size={10} />
            {Math.abs(trend)}%
          </span>
          <span className="text-xs text-text-disabled">{trendLabel || 'vs last week'}</span>
        </div>
      )}
    </div>
  );
}

function SignalBar({ name, count, maxCount, severity }) {
  const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
  const barColor = severity === 'Critical' ? 'bg-danger-500' : severity === 'High' ? 'bg-suspicious-500' : 'bg-suspicious-50';
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 shrink-0 truncate text-sm text-text-primary">{name}</span>
      <div className="flex-1">
        <div className="h-2 overflow-hidden rounded-full bg-surface-200">
          <div className={`h-full rounded-full ${barColor} anim-slow`} style={{ width: `${pct}%` }} />
        </div>
      </div>
      <span className="w-12 text-right text-sm font-semibold text-text-secondary">{count}</span>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(FALLBACK_DATA);
  const [isLive, setIsLive] = useState(false);
  const [dataVisible, setDataVisible] = useState(false);
  const [search, setSearch] = useState('');
  const [filterRisk, setFilterRisk] = useState('all');
  const [sortKey, setSortKey] = useState('created_at');
  const [sortDir, setSortDir] = useState('desc');

  const { search: urlSearch } = useLocation();
  useEffect(() => {
    const params = new URLSearchParams(urlSearch);
    if (params.get('section') === 'history') {
      setTimeout(() => {
        document.getElementById('scan-history')?.scrollIntoView({ behavior: 'smooth' });
      }, 300);
    }
  }, [urlSearch]);

  useEffect(() => { requestAnimationFrame(() => setDataVisible(true)); }, []);

  const headerRef = useScrollReveal();
  const statsRef = useScrollReveal({ threshold: 0.15 });
  const chartRef = useScrollReveal();
  const activityRef = useScrollReveal();
  const historyRef = useScrollReveal();

  useEffect(() => {
    let mounted = true;

    async function fetchData() {
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 4000);
        const apiKey = import.meta.env.VITE_API_KEY || '';
        const headers = apiKey ? { 'X-API-Key': apiKey } : {};
        const [dr, hr] = await Promise.all([
          fetch(DASHBOARD_API, { signal: controller.signal, headers }),
          fetch(HISTORY_API, { signal: controller.signal, headers }),
        ]);
        clearTimeout(timer);
        if (!dr.ok || !hr.ok) throw new Error();
        const dj = await dr.json();
        const hj = await hr.json();
        if (!mounted) return;
        setData({ ...FALLBACK_DATA, ...dj, recent: hj.slice(0, 4), history: hj });
        setIsLive(true);
      } catch {
        if (!mounted) return;
        setIsLive(false);
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const scanHistory = data.history || [];

  const filtered = scanHistory
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

  const pieData = [
    { name: 'Phishing', value: data.phishing_count || 0 },
    { name: 'Suspicious', value: data.suspicious_count || 0 },
    { name: 'Safe', value: data.safe_count || 0 },
  ];

  const riskData = [
    { level: 'High', count: data.risk_levels?.high || 0 },
    { level: 'Medium', count: data.risk_levels?.medium || 0 },
    { level: 'Low', count: data.risk_levels?.low || 0 },
  ];

  const trend = data.trend || {};
  const daily = data.daily_trend || [];
  const signals = data.top_signals || [];
  const recent = data.recent || [];

  return (
    <div className="mx-auto max-w-7xl animate-fade-in-up px-4 py-8 md:px-6">
      {/* Header */}
      <div ref={headerRef} className="reveal mb-6">
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-semibold text-primary-500">
            <span className="h-2 w-2 rounded-full bg-primary-500" />
            Cyber Threat Analytics
          </span>
          {!isLive && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-suspicious-50 px-3 py-1 text-xs font-semibold text-suspicious-700">
              <span className="h-1.5 w-1.5 rounded-full bg-suspicious-500 animate-breathe" />
              Demo Mode
            </span>
          )}
        </div>
        <h1 className="mt-3 text-2xl font-bold text-text-primary md:text-3xl">Security Dashboard</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Monitor phishing detections, scan history, confidence scores, and system performance powered by machine learning.
        </p>
      </div>

      {/* Stat Cards */}
      <div ref={statsRef} className="reveal stagger-children mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard icon="mail" title="Emails Scanned" value={data.total_scans} trend={trend.scans} color="primary" visible={dataVisible} />
        <StatCard icon="danger" title="Phishing Detected" value={data.phishing_count} trend={trend.phishing} color="danger" visible={dataVisible} />
        <StatCard icon="check" title="Safe Emails" value={data.safe_count} trend={trend.safe} color="safe" visible={dataVisible} />
        <StatCard icon="warning" title="Suspicious" value={data.suspicious_count || 0} color="warning" visible={dataVisible} />
        <StatCard icon="analytics" title="Avg Risk Score" value={data.avg_risk_score} suffix="%" trend={trend.risk_score} color="primary" visible={dataVisible} />
        <StatCard icon="report" title="High Risk Alerts" value={data.risk_levels?.high || 0} color="danger" visible={dataVisible} />
      </div>

      {/* Charts + Threat Signals Row */}
      <div ref={chartRef} className="reveal mb-6 grid gap-6 lg:grid-cols-2">
        {/* Pie Chart */}
        <div className="hover-lift rounded-xl border border-surface-300 bg-white p-5 shadow-card">
          <h2 className="mb-1 text-base font-bold text-text-primary">Threat Distribution</h2>
          <p className="mb-3 text-xs text-text-disabled">Breakdown of all scanned emails by classification</p>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} dataKey="value" paddingAngle={3}>
                <Cell fill={PIE_COLORS.phishing} />
                <Cell fill={PIE_COLORS.suspicious} />
                <Cell fill={PIE_COLORS.safe} />
              </Pie>
              <Tooltip contentStyle={chartTooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 flex justify-center gap-5 text-xs">
            <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS.phishing }} /> Phishing</span>
            <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS.suspicious }} /> Suspicious</span>
            <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS.safe }} /> Safe</span>
          </div>
        </div>

        {/* Bar Chart + Top Signals */}
        <div className="space-y-6">
          <div className="hover-lift rounded-xl border border-surface-300 bg-white p-5 shadow-card">
            <h2 className="mb-1 text-base font-bold text-text-primary">Risk Level Breakdown</h2>
            <p className="mb-3 text-xs text-text-disabled">Scans categorized by severity risk level</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={riskData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="level" stroke="#9e9e9e" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9e9e9e" allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip cursor={{ fill: 'rgba(21,101,192,0.06)' }} contentStyle={chartTooltipStyle} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  <Cell fill="#d32f2f" />
                  <Cell fill="#ff8f00" />
                  <Cell fill="#43a047" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          {/* Top Threat Signals */}
          <div className="rounded-xl border border-surface-300 bg-white p-5 shadow-card">
            <h2 className="mb-1 text-base font-bold text-text-primary">Top Threat Signals</h2>
            <p className="mb-3 text-xs text-text-disabled">Most frequently detected phishing indicators</p>
            <div className="space-y-3">
              {signals.map((s, i) => (
                <SignalBar key={i} name={s.name} count={s.count} maxCount={signals[0]?.count || 1} severity={s.severity} />
              ))}
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-surface-50 p-3">
              {[
                { label: 'Critical', count: signals.filter(s => s.severity === 'Critical').reduce((a, b) => a + b.count, 0), color: 'bg-danger-500' },
                { label: 'High', count: signals.filter(s => s.severity === 'High').reduce((a, b) => a + b.count, 0), color: 'bg-suspicious-500' },
                { label: 'Total', count: signals.reduce((a, b) => a + b.count, 0), color: 'bg-primary-500' },
              ].map(({ label, count, color }) => (
                <div key={label} className="text-center">
                  <p className="text-base font-bold text-text-primary">{count.toLocaleString()}</p>
                  <p className="text-xs text-text-disabled">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Detections Cards */}
      <div className="reveal mb-6" ref={activityRef}>
        <h2 className="mb-3 text-lg font-bold text-text-primary">Latest Detections</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {recent.slice(0, 4).map((item, i) => {
            const isPhishing = item.prediction === 'Phishing Email' || item.prediction === 'phishing';
            const isSuspicious = item.prediction === 'Suspicious Email';
            const borderColor = isPhishing ? 'border-l-danger-500' : isSuspicious ? 'border-l-suspicious-500' : 'border-l-safe-500';
            const badgeStyle = isPhishing ? 'bg-danger-50 text-danger-700' : isSuspicious ? 'bg-suspicious-50 text-suspicious-700' : 'bg-safe-50 text-safe-700';
            const rescanned = item.scan_count > 1;
            return (
              <div key={item.id || i} className={`hover-lift rounded-xl border border-surface-300 border-l-4 bg-white p-4 shadow-card ${borderColor}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-medium text-text-primary">{item.sender || 'Unknown'}</p>
                  {rescanned && (
                    <span className="shrink-0 rounded bg-primary-50 px-1.5 py-0.5 text-[10px] font-semibold text-primary-500">
                      x{item.scan_count}
                    </span>
                  )}
                </div>
                <span className={`mt-2 inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${badgeStyle}`}>{item.prediction}</span>
                <div className="mt-3 flex items-center justify-between text-xs text-text-disabled">
                  <span>{item.confidence}% confidence</span>
                  <span>{item.created_at}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Scan History Table */}
      <div id="scan-history" ref={historyRef} className="reveal rounded-xl border border-surface-300 bg-white shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-surface-200 px-5 py-3">
          <div>
            <h2 className="text-base font-bold text-text-primary">Scan History</h2>
            <p className="text-xs text-text-disabled">Complete record of all email scans</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Icon name="search" size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-disabled" />
              <input
                type="text"
                placeholder="Search sender or prediction..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-48 rounded-lg border border-surface-300 bg-surface-50 py-2 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-disabled focus:border-primary-500 focus:outline-none md:w-56"
              />
            </div>
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="rounded-lg border border-surface-300 bg-surface-50 px-3 py-2 text-sm text-text-primary focus:border-primary-500 focus:outline-none"
            >
              <option value="all">All Risk</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <span className="rounded-lg bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-500">
              {filtered.length} Records
            </span>
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="px-5 py-10 text-center text-text-disabled">
            <Icon name="history" size={32} className="mx-auto" />
            <p className="mt-2 text-sm font-medium">{scanHistory.length === 0 ? 'No scans performed yet' : 'No matches found'}</p>
            <p className="mt-1 text-xs">{scanHistory.length === 0 ? 'Scan an email on the Scanner page to see results here' : 'Try adjusting your search or filter'}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] text-left text-sm">
              <thead>
                <tr className="border-b border-surface-200 bg-surface-50 text-xs font-semibold uppercase tracking-wider text-text-disabled">
                  <th className="group cursor-pointer px-5 py-4 select-none" onClick={() => toggleSort('sender')}>Sender <SortIcon columnKey="sender" /></th>
                  <th className="group cursor-pointer px-5 py-4 select-none" onClick={() => toggleSort('prediction')}>Prediction <SortIcon columnKey="prediction" /></th>
                  <th className="group cursor-pointer px-5 py-4 select-none" onClick={() => toggleSort('confidence')}>Confidence <SortIcon columnKey="confidence" /></th>
                  <th className="group cursor-pointer px-5 py-4 select-none" onClick={() => toggleSort('risk_level')}>Risk <SortIcon columnKey="risk_level" /></th>
                  <th className="group cursor-pointer px-5 py-4 select-none" onClick={() => toggleSort('created_at')}>Date <SortIcon columnKey="created_at" /></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item, i) => {
                  const isPhishing = item.prediction === 'Phishing Email' || item.prediction === 'phishing';
                  const isSuspicious = item.prediction === 'Suspicious Email';
                  const rescanned = item.scan_count > 1;
                  return (
                    <tr key={item.id || i} className="animate-slide-up border-b border-surface-100 text-text-primary anim-fast hover:bg-surface-50" style={{ animationDelay: `${i * 30}ms` }}>
                      <td className="max-w-[180px] truncate px-5 py-3.5 text-text-secondary">
                        <div className="flex items-center gap-2">
                          <span className="truncate">{item.sender || 'Unknown'}</span>
                          {rescanned && (
                            <span className="shrink-0 rounded bg-primary-50 px-1.5 py-0.5 text-[10px] font-semibold text-primary-500">
                              x{item.scan_count}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-block rounded-md px-2.5 py-0.5 text-xs font-semibold ${isPhishing ? 'bg-danger-50 text-danger-700' : isSuspicious ? 'bg-suspicious-50 text-suspicious-700' : 'bg-safe-50 text-safe-700'}`}>
                          {item.prediction}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-primary-500">{item.confidence}%</td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-block rounded-md px-2.5 py-0.5 text-xs font-semibold ${item.risk_level === 'high' ? 'bg-danger-50 text-danger-700' : item.risk_level === 'medium' ? 'bg-suspicious-50 text-suspicious-700' : 'bg-safe-50 text-safe-700'}`}>
                          {item.risk_level}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-text-disabled">{item.created_at || '\u2014'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

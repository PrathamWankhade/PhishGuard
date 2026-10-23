import React, { useState, useEffect, useRef, useCallback } from 'react';
import { NavLink } from 'react-router-dom';
import Icon from './Icon.jsx';
import { API_BASE_URL } from '../services/api.js';

const HISTORY_API = `${API_BASE_URL}/history`;

const links = [
  { to: '/', label: 'Home', icon: 'shield' },
  { to: '/scanner', label: 'Scanner', icon: 'scan' },
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/analytics', label: 'Threat Signals', icon: 'analytics' },
  { to: '/contact', label: 'Contact', icon: 'contact' },
];

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadIds, setUnreadIds] = useState(new Set());
  const [scrolled, setScrolled] = useState(false);
  const notifRef = useRef(null);
  const lastSeenRef = useRef(Date.now());

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await fetch(HISTORY_API);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      const threats = data.filter(
        (item) => item.prediction === 'Phishing Email' || item.prediction === 'Suspicious Email'
      );
      const newIds = new Set(unreadIds);
      threats.forEach((item) => {
        const ts = new Date(item.created_at).getTime();
        if (ts > lastSeenRef.current) newIds.add(item.id);
      });
      setUnreadIds(newIds);
      setNotifications(threats);
    } catch {
      /* silently fail */
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const dismissNotification = (id) => {
    const next = new Set(unreadIds);
    next.delete(id);
    setUnreadIds(next);
  };

  const markAllRead = () => {
    setUnreadIds(new Set());
    lastSeenRef.current = Date.now();
  };

  useEffect(() => {
    if (!notifOpen) return;
    const handleClick = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) setNotifOpen(false);
    };
    const handleEsc = (e) => { if (e.key === 'Escape') setNotifOpen(false); };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleEsc);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleEsc);
    };
  }, [notifOpen]);

  return (
    <header
      className={`sticky top-0 z-50 border-b border-surface-300 bg-white anim-standard ${
        scrolled
          ? 'shadow-elevated-lg'
          : 'shadow-[0_1px_0_0_#e0e0e0]'
      }`}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 md:px-6">
        {/* Left: Logo */}
        <NavLink to="/" className="flex items-center gap-2.5 font-bold text-text-primary no-underline group">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-500 shadow-sm anim-fast group-hover:scale-110 group-hover:shadow-md">
            <Icon name="shieldCheck" size={18} className="text-white anim-fast group-hover:scale-110" />
          </span>
          <span className="hidden text-base tracking-tight sm:inline">PhishGuard</span>
        </NavLink>

        {/* Center: Nav Links */}
        <div className="hidden items-center gap-0.5 md:flex">
          {links.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
               className={({ isActive }) =>
                 `nav-underline flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium no-underline anim-standard ${
                   isActive
                     ? 'bg-primary-50 text-primary-500 active'
                     : 'text-text-secondary hover:bg-surface-100 hover:text-text-primary'
                 }`
               }
            >
              <Icon name={icon} size={16} />
              {label}
            </NavLink>
          ))}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className={`flex h-9 w-9 items-center justify-center rounded-lg anim-fast ${
              searchOpen ? 'bg-primary-50 text-primary-500' : 'text-text-secondary hover:bg-surface-100'
            }`}
            aria-label="Search"
          >
            <Icon name="search" size={18} />
          </button>

          <div ref={notifRef} className="relative">
            <button
              onClick={() => { setNotifOpen(!notifOpen); if (!notifOpen) lastSeenRef.current = Date.now(); }}
              className={`relative flex h-9 w-9 items-center justify-center rounded-lg anim-fast ${
                notifOpen ? 'bg-primary-50 text-primary-500' : 'text-text-secondary hover:bg-surface-100'
              }`}
              aria-label="Notifications"
            >
              <Icon name="notification" size={18} />
              {unreadIds.size > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-danger-500 px-1 text-[10px] font-bold leading-none text-white ring-2 ring-white animate-scale-in">
                  {unreadIds.size > 99 ? '99+' : unreadIds.size}
                </span>
              )}
            </button>

            {notifOpen && (
              <div className="absolute right-0 top-full mt-2 w-80 rounded-xl border border-surface-300 bg-white shadow-elevated animate-fade-in-down">
                <div className="flex items-center justify-between border-b border-surface-200 px-4 py-3">
                  <span className="text-sm font-bold text-text-primary">Notifications</span>
                  {unreadIds.size > 0 && (
                    <button onClick={markAllRead} className="text-xs font-medium text-primary-500 hover:text-primary-700 anim-fast">
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="px-4 py-8 text-center text-xs text-text-disabled">
                      No threat notifications yet
                    </div>
                  ) : (
                    notifications.slice(0, 20).map((item) => {
                      const isPhishing = item.prediction === 'Phishing Email';
                      const isUnread = unreadIds.has(item.id);
                      return (
                        <div
                          key={item.id}
                          className={`group flex items-start gap-3 border-b border-surface-100 px-4 py-3 anim-fast ${
                            isUnread ? 'bg-primary-50/40' : 'hover:bg-surface-50'
                          }`}
                        >
                          <span className={`mt-0.5 flex h-2 w-2 shrink-0 rounded-full ${isPhishing ? 'bg-danger-500' : 'bg-suspicious-500'} ${isUnread ? 'opacity-100' : 'opacity-0'} anim-fast`} />
                          <div className="min-w-0 flex-1">
                            <p className={`truncate text-sm ${isUnread ? 'font-semibold text-text-primary' : 'font-medium text-text-secondary'}`}>
                              {item.sender || 'Unknown'}
                            </p>
                            <div className="mt-0.5 flex items-center gap-2">
                              <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${isPhishing ? 'bg-danger-50 text-danger-700' : 'bg-suspicious-50 text-suspicious-700'}`}>
                                {isPhishing ? 'Phishing' : 'Suspicious'}
                              </span>
                              <span className="text-[10px] text-text-disabled">{item.created_at}</span>
                            </div>
                          </div>
                          {isUnread && (
                            <button
                              onClick={() => dismissNotification(item.id)}
                              className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-text-disabled opacity-0 transition hover:bg-surface-200 hover:text-text-secondary group-hover:opacity-100"
                              aria-label="Dismiss"
                            >
                              <Icon name="close" size={12} />
                            </button>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
                <div className="border-t border-surface-200 px-4 py-2.5 text-center">
                  <NavLink
                    to="/dashboard"
                    onClick={() => setNotifOpen(false)}
                    className="text-xs font-medium text-text-disabled hover:text-text-secondary anim-fast no-underline"
                  >
                    View all in Dashboard
                  </NavLink>
                </div>
              </div>
            )}
          </div>

          {/* Mobile menu toggle */}
          <button
            className={`flex h-9 w-9 items-center justify-center rounded-lg anim-fast md:hidden ${
              menuOpen ? 'bg-primary-50 text-primary-500' : 'text-text-secondary hover:bg-surface-100'
            }`}
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            <Icon name={menuOpen ? 'close' : 'menu'} size={18} />
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="border-t border-surface-300 bg-white px-4 py-3 md:hidden animate-slide-down">
          {links.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium no-underline transition ${
                  isActive
                    ? 'bg-primary-50 text-primary-500'
                    : 'text-text-secondary hover:bg-surface-100 hover:text-text-primary'
                }`
              }
              onClick={() => setMenuOpen(false)}
            >
              <Icon name={icon} size={18} />
              {label}
            </NavLink>
          ))}
        </div>
      )}

      {/* Search Bar */}
      {searchOpen && (
        <div className="border-t border-surface-300 bg-surface-50 px-4 py-3 animate-slide-down">
          <div className="mx-auto flex max-w-2xl items-center gap-3 rounded-xl border border-surface-300 bg-white px-4 py-2 shadow-sm">
            <Icon name="search" size={18} className="text-text-disabled" />
            <input
              type="text"
              placeholder="Search scans, URLs, or senders..."
              className="w-full border-0 bg-transparent text-sm text-text-primary outline-none placeholder:text-text-disabled"
              autoFocus
            />
            <button
              onClick={() => setSearchOpen(false)}
              className="rounded-lg p-1 text-text-disabled transition hover:bg-surface-100 hover:text-text-secondary"
            >
              <Icon name="close" size={16} />
            </button>
          </div>
        </div>
      )}
    </header>
  );
}

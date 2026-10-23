import React from 'react';

/*
 * Professional, consistent icon system for PhishGuard.
 *
 * Design rules:
 * - All icons use viewBox="0 0 24 24"
 * - Primary style: stroke="currentColor", strokeWidth="2", strokeLinecap="round", strokeLinejoin="round"
 * - No mixed fill+stroke on the same shape (avoids muddy overlap)
 * - Fill only used for solid accent dots / badges
 * - Geometric paths centered and balanced in the 24x24 grid
 */
const icons = {
  shield: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path
        d="M12 2l-7 5v5c0 4.71 6.43 8 7 8s7-3.29 7-8V7l-7-5z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  scan: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M21 21l-4.343-4.343a1 1 0 0 0-1.314 0L11 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="11" cy="11" r="1" fill="currentColor" />
      <path d="M11 8v6M8 11h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),

  dashboard: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="2" />
      <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="2" />
      <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="2" />
      <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="2" />
    </svg>
  ),

  analytics: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M4 20h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M6 16l4-6 4 4 6-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="18" cy="7" r="1" fill="currentColor" />
    </svg>
  ),

  history: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M12 6v6l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  file: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-5-5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M13 2v6h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M8 15h5M8 18h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),

  contact: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M22 6l-10 7L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  about: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M12 16v-4M8 12h.01M16 12h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  ai: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M12 2a3 3 0 0 1 3 3v2a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M8 18l4 4 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="12" cy="16" r="1" fill="currentColor" />
    </svg>
  ),

  notification: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  user: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M4 20v-2a6 6 0 0 1 12 0v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  search: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  mail: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="2" />
      <path d="M22 6l-10 7L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  check: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M9 13l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  verify: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M8 12l2 2 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  warning: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M12 2l7 12h-14z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 9v5M12 17h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),

  danger: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  arrowUp: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M12 19V5M5 12l7-7 7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  arrowDown: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M12 5v14M5 12l7 7 7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  globe: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M2 12h20M12 2a13 13 0 0 1 4 8 13 13 0 0 1-4 8 13 13 0 0 1-4-8 13 13 0 0 1 4-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  lock: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <rect x="5" y="11" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="16" r="1" fill="currentColor" />
    </svg>
  ),

  shieldLock: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M12 2l-7 5v5c0 4.71 6.43 8 7 8s7-3.29 7-8V7l-7-5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 8v3M9 11h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  shieldAlert: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M12 2l-7 5v5c0 4.71 6.43 8 7 8s7-3.29 7-8V7l-7-5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 9v5M12 17h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),

  network: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="4" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="4" cy="20" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="20" cy="20" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M12 6v3M7 18l3-4M17 18l-3-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="12" cy="10" r="1" fill="currentColor" opacity="0.4" />
    </svg>
  ),

  download: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 10l5 5 5-5M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  send: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M22 2l-7 20-4-9-9-4 20-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  close: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  menu: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M3 12h18M3 6h18M3 18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  chevronRight: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  chevronDown: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  report: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2V8l-5-5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M13 2v6h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M16 13H9M16 17H9M10 9H8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),

  speed: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  refresh: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M23 4c0-4.9-3.9-8.8-8.8-8.8c-4.8 0-8.7 3.9-8.7 8.7c0 1 0.2 2 0.5 2.9c-2.2-0.4-4.4-1.3-6-2.7c-0.9 1.8-1.4 3.8-1.4 5.9c0 4.9 3.9 8.8 8.8 8.8c1.3 0 2.6-0.3 3.7-0.9c0.4 1.5 1.4 2.6 2.9 2.9c2.3 1.1 4.9 1.7 7.6 1.7c5.3 0 9.6-4.3 9.6-9.6C24 7.3 24 5.7 23 4z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M17.5 19.5c-1.2 0-2.4-0.2-3.5-0.6c-0.5-0.2-0.8-0.7-0.8-1.3c0-0.9 0.7-1.7 1.7-1.7c0.7 0 1.4 0.4 1.7 1c0.3-0.4 0.5-0.9 0.5-1.4c0-1.9-1.6-3.5-3.5-3.5c-1.1 0-2.1 0.5-2.8 1.3c-0.4 0.4-0.6 0.9-0.6 1.5c0 2.6 2.1 4.7 4.7 4.7c1.4 0 2.7-0.6 3.6-1.6c0.4-0.4 0.5-1 0.3-1.5c-0.2-0.6-0.8-1-1.4-1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  shieldCheck: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M12 2l-7 5v5c0 4.71 6.43 8 7 8s7-3.29 7-8V7l-7-5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  github: (props) => (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.33.465-2.38 1.235-3.22-.135-.333-.55-1.593.715-2.178 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23 1.265.585 1.768 1.845.715 2.178.77.84 1.235 1.89 1.235 3.22 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222 0 1.606-.015 2.896-.015 3.286 0 .315.21.698.823.577C20.565 21.795 24 17.3 24 12.273 24 5.373 18.626 0 12 0z" />
    </svg>
  ),

  instagram: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="2" />
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2" />
      <circle cx="17" cy="7" r="1" fill="currentColor" />
    </svg>
  ),

  linkedin: (props) => (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1 2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  ),

  star: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M12 2l3 7h7l-5 5 2 7L12 16l-5-5 2-7h7l3-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  info: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M12 11h.01M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),

  external: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M21 14v-2a2 2 0 0 0-2-2H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="7 17 12 12 7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 3v4a2 2 0 0 0 2 2h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  link: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.73" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.72-1.73" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  clock: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <polyline points="12 6 12 12 16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),

  eye: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="12" cy="12" r="3" fill="currentColor" />
    </svg>
  ),

  key: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M21 2l-2 2M7.7 7.7a3 3 0 1 0 4.243 4.243L18 12l-1.414 1.414a4 4 0 0 1-5.657 0L7.7 15.6a4 4 0 0 1 0-5.657z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
};

export default function Icon({ name, className = '', size = 20, ...props }) {
  const renderIcon = icons[name];
  if (!renderIcon) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }
  return (
    <span className={`inline-block ${className}`} style={{ width: size, height: size }}>
      {renderIcon({ width: size, height: size, ...props })}
    </span>
  );
}

import React, { useEffect, useRef } from 'react';
import Icon from '../components/Icon.jsx';

export default function EmailInput({ value, sender, onEmailChange, onSenderChange, onScan, loading }) {
  const textareaRef = useRef(null);
  const isEmpty = !value || !value.trim();

  // Ctrl/Cmd + Enter to scan
  useEffect(() => {
    function onKeyDown(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!loading && !isEmpty) onScan();
      }
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [loading, isEmpty, onScan]);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!loading && !isEmpty) onScan();
      }}
      className="rounded-2xl border border-surface-300 bg-white p-6 shadow-card"
    >
      {/* Header */}      <div className="mb-6">
        <span className="inline-flex items-center gap-2 rounded-lg bg-primary-50 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-primary-500">
          <span className="h-1.5 w-1.5 rounded-full bg-primary-500" />
          Email Threat Scanner
        </span>
        <h2 className="mt-4 text-xl font-bold text-text-primary">Analyze Suspicious Email</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Paste suspicious email content and sender details to detect phishing threats using machine learning.
        </p>
        {/* Keyboard shortcut hint */}
        <p className="mt-3 text-[10px] font-medium text-text-disabled uppercase tracking-wider flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1 rounded bg-surface-100 px-1.5 py-0.5">
            <kbd className="text-text-primary">Ctrl</kbd><kbd className="text-text-primary">⌘</kbd><kbd className="text-text-primary">Enter</kbd>
          </span>
          to scan
        </p>
      </div>

      {/* Sender Email */}
      <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="sender">
        Sender Email
      </label>
      <input
        id="sender"
        value={sender}
        onChange={(e) => onSenderChange(e.target.value)}
        placeholder="support@secure-bank.example"
        className="mb-5 w-full rounded-lg border border-surface-300 bg-surface-50 px-4 py-3 text-sm text-text-primary outline-none anim-standard focus:border-primary-500 focus:ring-2 focus:ring-primary-50"
      />

      {/* Email Content */}
      <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="emailText">
        Email Content
      </label>
      <textarea
        ref={textareaRef}
        id="emailText"
        value={value}
        onChange={(e) => onEmailChange(e.target.value)}
        placeholder="Paste suspicious email subject and body here…"
        rows={10}
        required
        className="w-full resize-none rounded-lg border border-surface-300 bg-surface-50 px-4 py-3 text-sm text-text-primary outline-none anim-standard focus:border-primary-500 focus:ring-2 focus:ring-primary-50"
      />
      <p className="mt-1 text-xs text-text-disabled text-right">
        {value.length} characters
      </p>

      {/* Validation inline error */}
      {isEmpty && !loading && (
        <p className="mt-2 text-xs font-medium text-danger-700 flex items-center gap-1.5">
          <Icon name="warning" size={12} />
          Email content is required before scanning.
        </p>
      )}

      {/* Scan Button */}
      <button
        type="submit"
        disabled={loading || isEmpty}
        className="ripple-container hover-scale mt-6 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary-500 px-6 py-3 text-sm font-semibold text-white shadow-sm transition disabled:cursor-not-allowed disabled:opacity-60 hover:!bg-primary-600"
      >
        {loading ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            Scanning Email…
          </>
        ) : (
          <>
            <Icon name="scan" size={16} />
            {isEmpty ? 'Add content to scan' : 'Scan Email'}
          </>
        )}
      </button>
    </form>
  );
}

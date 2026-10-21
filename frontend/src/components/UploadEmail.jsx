import React, { useState } from 'react';

const UPLOAD_API = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/upload`
  : 'http://127.0.0.1:8000/api/v1/upload';

export default function UploadEmail({ onLoad, onSenderLoad, onHeadersLoad }) {
  const [notice, setNotice] = useState(null);
  const [uploading, setUploading] = useState(false);

  function emitHeaders(parsed) {
    onHeadersLoad?.({
      reply_to: parsed?.reply_to || '',
      return_path: parsed?.return_path || '',
      auth_results: '',
    });
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setNotice(null);
    setUploading(true);

    try {
      if (file.size > 2_000_000) {
        setNotice('File exceeds 2MB limit.');
        return;
      }

      // Prefer backend MIME parsing; fall back to plain text for .txt.
      try {
        const form = new FormData();
        form.append('file', file);
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 15000);
        const resp = await fetch(UPLOAD_API, {
          method: 'POST',
          body: form,
          signal: controller.signal,
        });
        clearTimeout(timer);
        if (resp.ok) {
          const parsed = await resp.json();
          const body = parsed.subject ? `Subject: ${parsed.subject}\n\n${parsed.body}` : parsed.body;
          onSenderLoad?.(parsed.sender || '');
          onLoad(body || '');
          emitHeaders(parsed);
          if (parsed.errors?.length) {
            setNotice(`Parsed with warnings: ${parsed.errors.join('; ')}`);
          }
          return;
        }
      } catch {
        // Fall through to local handling below.
      }

      const text = await file.text();
      let extractedSender = '';
      let extractedBody = text;

      if (file.name.endsWith('.eml')) {
        setNotice('Backend parser unavailable — showing raw content; results may be less accurate.');
        const senderMatch = text.match(/From:\s*(.+)/i);
        const bodyMatch = text.split(/\r?\n\r?\n/);
        extractedSender = senderMatch?.[1] || '';
        extractedBody = bodyMatch?.slice(1).join('\n') || text;
      } else if (file.name.endsWith('.txt')) {
        const senderMatch = text.match(/From:\s*(.+)/i);
        if (senderMatch) extractedSender = senderMatch[1];
      }

      onSenderLoad?.(extractedSender);
      onLoad(extractedBody);
      emitHeaders(null);
    } catch (err) {
      setNotice(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      // Reset the file input so the same file can be re-selected
      event.target.value = '';
    }
  }

  function dismissNotice() {
    setNotice(null);
  }

  return (
    <div className="hover-lift rounded-xl border border-surface-300 bg-white p-5 shadow-card">
      <label className="block text-sm font-medium text-text-primary">
        Upload Email (.txt / .eml)
      </label>
      <input
        type="file"
        accept=".txt,.eml"
        onChange={handleUpload}
        disabled={uploading}
        className="mt-3 block w-full cursor-pointer rounded-lg border border-surface-300 bg-surface-50 px-4 py-3 text-sm text-text-secondary file:mr-4 file:rounded-lg file:border-0 file:bg-primary-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-primary-500 hover:file:bg-primary-100 disabled:opacity-60 disabled:cursor-not-allowed"
      />
      {notice && (
        <div
          role="alert"
          className="mt-3 rounded-xl border border-suspicious-500/40 bg-suspicious-50 px-4 py-3 flex items-start gap-3"
        >
          <IconUpload name="warning" size={16} className="mt-0.5 shrink-0 text-suspicious-700" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-suspicious-700">Check before scanning</p>
            <p className="mt-0.5 text-xs leading-5 text-suspicious-700">{notice}</p>
          </div>
          <button
            onClick={dismissNotice}
            className="shrink-0 rounded-lg p-1 text-suspicious-700/60 hover:bg-suspicious-100 hover:text-suspicious-700 transition"
            aria-label="Dismiss"
          >
            <IconUpload name="close" size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

function IconUpload({ name, size = 16, className = '' }) {
  const icons = {
    warning: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} style={{ width: size, height: size }}>
        <path d="M12 2l7 12h-14z" />
        <path d="M12 9v5M12 17h.01" />
      </svg>
    ),
    close: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} style={{ width: size, height: size }}>
        <path d="M18 6L6 18M6 6l12 12" />
      </svg>
    ),
  };
  return icons[name] || null;
}

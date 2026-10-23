import React, { useCallback } from 'react';
import Icon from './Icon.jsx';

const riskStyles = {
  high: {
    border: 'border-danger-500/30',
    bg: 'bg-danger-50',
    badge: 'bg-danger-500 text-white',
    text: 'text-danger-700',
    icon: '\u26D4',
    label: 'HIGH RISK',
    bar: 'bg-danger-500',
  },
  medium: {
    border: 'border-suspicious-500/30',
    bg: 'bg-suspicious-50',
    badge: 'bg-suspicious-500 text-white',
    text: 'text-suspicious-700',
    icon: '\u26A0\uFE0F',
    label: 'MEDIUM RISK',
    bar: 'bg-suspicious-500',
  },
  low: {
    border: 'border-safe-500/30',
    bg: 'bg-safe-50',
    badge: 'bg-safe-500 text-white',
    text: 'text-safe-700',
    icon: '\u2705',
    label: 'LOW RISK',
    bar: 'bg-safe-500',
  },
};

export default function PredictionCard({ result, onRescan, onReport }) {
  if (!result) {
    return (
      <div className="animate-scale-in rounded-2xl border border-surface-300 bg-white p-8 text-center shadow-card">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-50 text-2xl">
          <svg width="28" height="28" fill="none" stroke="#1565c0" strokeWidth="1.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" d="M12 15v2m0-6v.01M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
          </svg>
        </div>
        <h3 className="text-lg font-bold text-text-primary">No Scan Results Yet</h3>
        <p className="mt-2 text-sm text-text-secondary">
          Scan an email to view phishing analysis, the policy risk score, risk level, and explainable AI insights.
        </p>
      </div>
    );
  }

  const style = riskStyles[result.risk_level] || riskStyles.medium;

  const copyResult = useCallback(() => {
    const text = [
      `Verdict: ${result.label}`,
      `Risk Score: ${result.risk_score}%`,
      `Model P(phishing): ${result.phishing_probability != null ? (result.phishing_probability * 100).toFixed(1) : 'N/A'}%`,
      `Risk Level: ${result.risk_level}`,
      `Evidence: ${(result.signals || result.reasons || []).join('; ') || 'none'}`,
    ].join('\n');
    navigator.clipboard.writeText(text).then(() => {});
  }, [result]);

  return (
    <div className={`animate-scale-in rounded-2xl border-2 ${style.border} bg-white p-6 shadow-card`}>
      {/* Header */}
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <span className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-bold uppercase tracking-wider ${style.badge}`}>
            {style.icon} {style.label}
          </span>
          <h2 className="mt-3 text-2xl font-bold text-text-primary">{result.label}</h2>
          <p className="mt-0.5 text-sm text-text-secondary">ML-powered phishing detection analysis</p>
        </div>
        <div className="text-left sm:text-right">
          <p className="text-xs font-medium text-text-disabled uppercase tracking-wider">Risk score</p>
          <p className="text-3xl font-bold text-primary-500">{result.risk_score}%</p>
          {result.phishing_probability != null && (
            <p className="mt-1 text-xs text-text-disabled">
              Model P(phishing): {(result.phishing_probability * 100).toFixed(1)}%
            </p>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mb-5 flex gap-2 sm:flex-wrap">
        <button
          onClick={onRescan}
          disabled={!onRescan}
          className="flex-1 sm:flex-auto inline-flex items-center justify-center gap-2 rounded-lg border border-surface-300 bg-white px-4 py-2.5 text-sm font-medium text-text-primary shadow-card transition hover:bg-surface-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Icon name="refresh" size={16} /> Re-scan
        </button>
        <button
          onClick={copyResult}
          className="flex-1 sm:flex-auto inline-flex items-center justify-center gap-2 rounded-lg border border-surface-300 bg-white px-4 py-2.5 text-sm font-medium text-text-primary shadow-card transition hover:bg-surface-50"
        >
          <Icon name="external" size={16} /> Copy Result
        </button>
        {onReport && (
          <button
            onClick={onReport}
            className="flex-1 sm:flex-auto inline-flex items-center justify-center gap-2 rounded-lg border border-danger-100 bg-danger-50 px-4 py-2.5 text-sm font-medium text-danger-600 transition hover:bg-danger-100"
          >
            <Icon name="shieldAlert" size={16} /> Report False Positive
          </button>
        )}
      </div>

      {/* Risk Bar */}
      <div className="mb-5">
        <div className="mb-1.5 flex justify-between text-xs text-text-secondary">
          <span>Policy risk score (heuristic, not a probability)</span>
          <span>{result.risk_score}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-surface-200">
          <div className={`h-full rounded-full transition-all duration-700 ${style.bar}`} style={{ width: `${result.risk_score}%` }} />
        </div>
      </div>

      {/* Stats */}
      <div className="mb-5 grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-surface-200 bg-surface-50 p-4">
          <p className="text-xs font-medium text-text-disabled uppercase tracking-wider">Model prediction</p>
          <p className="mt-1 truncate text-base font-semibold text-text-primary">
            {result.model_prediction || result.prediction || result.label}
            {result.model_confidence != null ? ` (${result.model_confidence}%)` : ''}
          </p>
        </div>
        <div className="rounded-xl border border-surface-200 bg-surface-50 p-4">
          <p className="text-xs font-medium text-text-disabled uppercase tracking-wider">Risk score</p>
          <p className="mt-1 text-base font-semibold text-primary-500">
            {result.risk_score}% · {result.risk_level}
          </p>
        </div>
        <div className="rounded-xl border border-surface-200 bg-surface-50 p-4">
          <p className="text-xs font-medium text-text-disabled uppercase tracking-wider">Source</p>
          <p className="mt-1 text-base font-semibold text-primary-500">{result.source || 'ML Model'}</p>
        </div>
        <div className="rounded-xl border border-surface-200 bg-surface-50 p-4">
          <p className="text-xs font-medium text-text-disabled uppercase tracking-wider">Verdict policy</p>
          <p className="mt-1 text-base font-semibold text-text-primary">{result.policy_version || 'explicit-v1'}</p>
        </div>
      </div>

      {result.warning && (
        <div className="mb-5 rounded-xl border border-suspicious-500/30 bg-suspicious-50 px-4 py-3 text-sm font-medium text-suspicious-700">
          {result.warning}
        </div>
      )}

      {/* Recommended next step — static guidance per risk level, not findings */}
      <div className="mb-5 rounded-xl border border-surface-200 bg-surface-50 px-4 py-3">
        <h3 className="mb-1 text-sm font-bold uppercase tracking-wider text-text-secondary">Recommended next step</h3>
        <p className="text-sm leading-5 text-text-primary">
          {result.risk_level === 'high' && 'Do not click links or share credentials. Verify the sender through a trusted channel and report this message to your security team.'}
          {result.risk_level === 'medium' && 'Treat links and attachments with caution. Verify unexpected requests through a separate channel before acting.'}
          {(!result.risk_level || result.risk_level === 'low') && 'No strong threat indicators. Still apply normal caution to unexpected messages.'}
        </p>
      </div>

      {/* Reasons */}
      <div>
        <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-text-secondary">Evidence signals</h3>
        <div className="space-y-2.5">
          {(result.signals || result.reasons)?.length ? (
            (result.signals || result.reasons).map((reason, i) => (
              <div key={i} className="flex items-start gap-3 rounded-xl bg-surface-50 px-4 py-3">
                <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${style.bar}`} />
                <p className="text-sm leading-5 text-text-primary">{reason}</p>
              </div>
            ))
          ) : (
            <div className="rounded-xl bg-surface-50 px-4 py-3 text-sm text-text-disabled">
              No strong phishing indicators found.
            </div>
          )}
        </div>
        {result.ai_explanation?.length > 0 && (
          <div className="mt-4">
            <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-text-secondary">
              AI summary (supplementary, does not affect verdict)
            </h3>
            <div className="space-y-2.5">
              {result.ai_explanation.map((reason, i) => (
                <div key={i} className="flex items-start gap-3 rounded-xl bg-surface-50 px-4 py-3 opacity-90">
                  <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-primary-500" />
                  <p className="text-sm leading-5 text-text-primary">{reason}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

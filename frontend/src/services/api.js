const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY || '';

function authHeaders(extra = {}) {
  return API_KEY ? { ...extra, 'X-API-Key': API_KEY } : extra;
}

const suspiciousTerms = [
  'urgent', 'verify', 'password', 'otp', 'bank', 'suspended',
  'click', 'login', 'payment', 'limited', 'account', 'immediately',
  'security', 'update', 'confirm', 'restricted', 'blocked',
  'unauthorized', 'unusual activity', 'alert', 'warning',
  'compromised', 'action required', 'credit card', 'debit card',
  'ssn', 'social security', 'wire transfer', 'cryptocurrency',
  'bitcoin', 'investment', 'guaranteed', 'prize', 'winner',
  'lottery', 'inheritance', 'overdue', 'past due', 'confidential',
  'limited time', 'expires', 'donation',
];

export function heuristicEstimate(emailText, sender = '') {
  const lower = `${emailText} ${sender}`.toLowerCase();

  const matched = suspiciousTerms.filter((term) => lower.includes(term));
  const urlCount = (emailText.match(/https?:\/\/|www\./gi) || []).length;
  const senderRisk = /\.(xyz|top|click|zip|ru|cn|tk|ml|ga|cf)\b/i.test(sender) ? 18 : 0;

  const score = Math.min(98, 12 + matched.length * 10 + urlCount * 14 + senderRisk);

  const label = score >= 70 ? 'Phishing Email' : score >= 40 ? 'Suspicious Email' : 'Safe Email';

  const reasons = [
    ...matched.slice(0, 5).map((term) => `Suspicious keyword detected: ${term}`),
    ...(urlCount ? [`${urlCount} link(s) found in the email body`] : []),
    ...(senderRisk ? ['Sender domain has a suspicious top-level domain'] : []),
  ];

  if (reasons.length === 0) reasons.push('No strong phishing indicators found in the text');

  return {
    status: 'heuristic-only',
    label,
    verdict: label,
    confidence: score,
    risk_score: score,
    risk_level: score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low',
    reasons,
    signals: reasons,
    source: 'frontend-heuristic',
    warning: 'ML detector unavailable — heuristic estimate only, not equivalent to model prediction.',
  };
}

export async function scanEmail(payload) {
  const requestBody = {
    email_text: payload.email_text || '',
    sender: payload.sender || '',
    reply_to: payload.reply_to || '',
    return_path: payload.return_path || '',
    auth_results: payload.auth_results || '',
  };

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(requestBody),
    });
  } catch (error) {
    // No silent fallback: caller must handle unavailable state explicitly.
    throw new Error(`Detection service unavailable: ${error.message}`);
  }

  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw new Error(`Backend responded with ${response.status}: ${errorText}`);
  }

  const data = await response.json();
  return { status: 'completed', ...data };
}

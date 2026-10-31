const threatSignals = [
  ['Urgent language', 'High', 'Account suspension, immediate action, limited time, expires'],
  ['Credential request', 'Critical', 'Password, OTP, banking details, login credentials'],
  ['URL anomaly', 'High', 'Shortened URL, fake domain, unusual TLD, IP-based URL'],
  ['Sender mismatch', 'Medium', 'Display name does not match sender domain'],
  ['Homograph attack', 'High', 'Lookalike characters (e.g., rn vs m, 1 vs l, 0 vs O)'],
  ['Suspicious attachment', 'High', '.exe, .zip, .docm, .js, .vbs files'],
  ['Spoofed sender', 'Critical', 'Fake domain impersonating trusted brands'],
  ['Attachment macro', 'Medium', 'Office documents with embedded macros'],
  ['Reply-to mismatch', 'Medium', 'Reply-to address differs from sender address'],
  ['Excessive recipients', 'Low', 'BCC to large number of recipients'],
  ['Generic greeting', 'Low', '"Dear Customer" instead of personal name'],
  ['Spelling / grammar', 'Low', 'Poor grammar, odd phrasing, typos'],
  ['Threat of consequences', 'High', 'Account termination, legal action, security breach'],
  ['Request for secrecy', 'High', '"Don\'t tell anyone", "Confidential request"'],
  ['Unusual sender time', 'Low', 'Email sent at odd hours (e.g., 3 AM)'],
];

const severityColors = {
  Critical: 'bg-danger-500 text-white',
  High: 'bg-suspicious-500 text-white',
  Medium: 'bg-suspicious-50 text-suspicious-700 border border-suspicious-500/30',
  Low: 'bg-surface-200 text-text-secondary',
};

export default function Analytics() {
  return (
    <div className="mx-auto max-w-7xl animate-fade-in-up px-4 py-16 md:px-6">
      <div className="mb-10 animate-slide-up">
        <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-semibold text-primary-500">
          <span className="h-2 w-2 rounded-full bg-primary-500" />
          Threat Intelligence
        </span>
        <h1 className="mt-4 text-3xl font-bold text-text-primary md:text-4xl">Threat Signal Reference</h1>
        <p className="mt-2 text-base text-text-secondary">
          Comprehensive list of phishing signals and indicators used by the AI system to detect malicious emails.
        </p>
      </div>

      <div className="stagger-children grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {threatSignals.map(([signal, severity, examples]) => (
            <div
              key={signal}
              className="hover-lift rounded-xl border border-surface-300 bg-white p-5 shadow-card"
            >
            <div className="mb-3 flex items-center justify-between gap-2">
              <h3 className="font-semibold text-text-primary">{signal}</h3>
              <span className={`shrink-0 rounded-md px-2.5 py-0.5 text-xs font-semibold ${severityColors[severity] || severityColors.Low}`}>
                {severity}
              </span>
            </div>
            <p className="text-sm leading-5 text-text-secondary">{examples}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

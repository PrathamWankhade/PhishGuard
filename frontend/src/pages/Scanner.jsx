import React, { useState } from 'react';
import Icon from '../components/Icon.jsx';
import EmailInput from '../components/EmailInput.jsx';
import PredictionCard from '../components/PredictionCard.jsx';
import UploadEmail from '../components/UploadEmail.jsx';
import { scanEmail } from '../services/api.js';

const SAMPLE_EMAIL = 'URGENT! Your online banking account will be suspended immediately. Click https://secure-bank-login.verify-now.example to verify your password and OTP.';
const SAMPLE_SENDER = 'support@sbi-security-alert.xyz';

export default function Scanner() {
  const [emailText, setEmailText] = useState('');
  const [sender, setSender] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleScan(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (!emailText.trim()) {
        setError('Please paste email content before scanning.');
        setLoading(false);
        return;
      }
      const prediction = await scanEmail({ email_text: emailText, sender });
      setResult(prediction);
    } catch (err) {
      setResult(null);
      setError(`${err.message}. The ML detector did not run — no result shown.`);
    } finally {
      setLoading(false);
    }
  }

  function loadSample() {
    setEmailText(SAMPLE_EMAIL);
    setSender(SAMPLE_SENDER);
    setResult(null);
    setError(null);
  }

  return (
    <div className="animate-fade-in-up">
      <section className="mx-auto max-w-7xl px-4 py-16 md:px-6 md:py-24">
        <div className="mb-12 text-center">
          <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-semibold text-primary-500">
            <span className="h-2 w-2 rounded-full bg-primary-500" />
            Email Threat Scanner
          </span>
          <h1 className="mt-4 text-3xl font-bold text-text-primary md:text-4xl">Analyze an email for phishing threats</h1>
          <p className="mt-2 text-text-secondary">Paste suspicious email content below or upload a .eml / .txt file.</p>
        </div>

        <div className="grid gap-10 lg:grid-cols-[1fr_0.95fr]">
          <div className="space-y-4">
            <UploadEmail onLoad={setEmailText} onSenderLoad={setSender} />
            <button
              onClick={loadSample}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-surface-300 bg-white px-4 py-3 text-sm font-medium text-text-secondary shadow-card transition hover:shadow-card-hover sm:w-auto sm:px-5"
            >
              <Icon name="download" size={16} />
              Load Sample Email
            </button>
          </div>
          <div className="grid gap-6">
            <EmailInput
              value={emailText}
              sender={sender}
              onEmailChange={setEmailText}
              onSenderChange={setSender}
              onScan={handleScan}
              loading={loading}
            />
            {error && (
              <div className="rounded-xl border border-danger-50 bg-danger-50 px-5 py-4 text-sm font-medium text-danger-700">
                {error}
              </div>
            )}
            <PredictionCard result={result} />
          </div>
        </div>
      </section>
    </div>
  );
}

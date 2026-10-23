import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import useScrollReveal from '../hooks/useScrollReveal.js';
import useCountUp from '../hooks/useCountUp.js';

const features = [
  { icon: 'shield', title: 'Lexical URL Analysis', desc: 'Flags shortened links, IP-based hosts, punycode/homograph tricks, and suspicious TLDs. URLs are never fetched, so analysis is SSRF-safe by design.' },
  { icon: 'mail', title: 'Email Analysis', desc: 'Scans email content for phishing keywords, urgency language, credential harvesting attempts, and spoofed senders.' },
  { icon: 'network', title: 'ML Classification', desc: 'Soft-voting LogisticRegression + RandomForest over TF-IDF (50k features, 1–3 grams), trained on 195,740 labeled emails.' },
  { icon: 'globe', title: 'Header & Auth Evidence', desc: 'Scores sender domain, Reply-To/Return-Path mismatches, authentication results, and BEC/fraud language as bounded, evidence-tagged risk.' },
  { icon: 'speed', title: 'Fast, Deterministic Scans', desc: 'Single-pass analysis with lazy-loaded model artifacts and SHA-256 content-hash dedup. Deterministic signals never depend on an external service.' },
  { icon: 'report', title: 'Traceable Verdicts', desc: 'Every verdict is backed by inspectable evidence; the policy risk score is kept separate from the model probability. Optional AI summaries need an API key.' },
];

const workflow = [
  { icon: 'mail', label: 'Input Email' },
  { icon: 'ai', label: 'AI Processing' },
  { icon: 'scan', label: 'Feature Extraction' },
  { icon: 'network', label: 'ML Classification' },
  { icon: 'warning', label: 'Threat Analysis' },
  { icon: 'shield', label: 'Security Report' },
];

export default function Home() {
  const [statsVisible, setStatsVisible] = useState(false);

  const featureRef = useScrollReveal();
  const workflowRef = useScrollReveal();
  const statsRef = useScrollReveal({ threshold: 0.3 });

  useEffect(() => {
    if (statsRef.current) {
      const obs = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) { setStatsVisible(true); obs.unobserve(entry.target); } },
        { threshold: 0.3 }
      );
      obs.observe(statsRef.current);
      return () => obs.disconnect();
    }
  }, [statsRef]);

  function StatValue({ num, prefix = '', suffix = '', visible }) {
    const count = useCountUp(num, { duration: 900, enabled: visible });
    const display = num >= 1000 && Number.isInteger(num) ? count.toLocaleString() : count;
    return <p className="text-3xl font-bold text-white md:text-4xl">{prefix}{display}{suffix}</p>;
  }

  return (
    <div className="animate-fade-in-up">
      {/* ======================== */}
      {/* HERO                       */}
      {/* ======================== */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -left-20 -top-20 h-80 w-80 rounded-full bg-white blur-3xl" />
          <div className="absolute -bottom-20 -right-20 h-96 w-96 rounded-full bg-white blur-3xl" />
          <div className="absolute left-1/3 top-1/4 h-40 w-40 rounded-full bg-white blur-2xl" />
        </div>
        <div className="relative mx-auto flex max-w-7xl flex-col items-center gap-10 px-4 py-20 md:flex-row md:py-28 lg:px-6">
          <div className="flex-1 text-center md:text-left">
            <span className="inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1.5 text-sm font-semibold text-white/90 backdrop-blur-sm">
              <span className="h-2 w-2 rounded-full bg-white" />
              AI-Powered Cybersecurity
            </span>
            <h1 className="mt-6 text-4xl font-bold leading-tight text-white md:text-5xl lg:text-6xl">
              AI-Based Phishing<br />Email Detection System
            </h1>
            <p className="mt-4 max-w-xl text-lg leading-7 text-white/80 md:text-xl">
              Detect phishing threats before they reach your inbox. Paste or upload an email and our AI analyzes language, links, sender patterns, and more.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                to="/scanner"
                className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 text-sm font-bold text-primary-600 shadow-lg transition hover:shadow-xl active:scale-[0.97]"
              >
                <Icon name="scan" size={18} />
                Start Scanning
              </Link>
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 rounded-xl border border-white/30 px-7 py-3.5 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                <Icon name="dashboard" size={18} />
                View Dashboard
              </Link>
            </div>
          </div>
          <div className="hidden shrink-0 md:block">
            <div className="flex h-72 w-72 items-center justify-center rounded-3xl bg-white/10 backdrop-blur-sm lg:h-80 lg:w-80">
              <div className="text-center text-white/90">
                <div className="animate-float">
                <Icon name="shieldCheck" size={120} className="mx-auto opacity-80" />
              </div>
              <p className="mt-4 text-sm font-medium text-white/70">AI Scanning Shield</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ======================== */}
      {/* FEATURES                   */}
      {/* ======================== */}
      <section ref={featureRef} className="reveal border-t border-surface-300 bg-surface-50">
        <div className="mx-auto max-w-7xl px-4 py-16 md:px-6 md:py-24">
          <div className="mx-auto mb-12 max-w-2xl text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-semibold text-primary-500">
              <span className="h-2 w-2 rounded-full bg-primary-500" />
              Features
            </span>
            <h2 className="mt-4 text-3xl font-bold text-text-primary">How PhishGuard protects you</h2>
            <p className="mt-2 text-text-secondary">Every layer of analysis works together to catch phishing attempts.</p>
          </div>
          <div className="stagger-children grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon, title, desc }) => (
              <div key={title} className="hover-lift rounded-2xl border border-surface-300 bg-white p-6 shadow-card">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-primary-50 text-primary-500">
                  <Icon name={icon} size={22} />
                </div>
                <h3 className="text-base font-bold text-text-primary">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-text-secondary">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ======================== */}
      {/* WORKFLOW                   */}
      {/* ======================== */}
      <section ref={workflowRef} className="reveal border-t border-surface-300 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-16 md:px-6 md:py-24">
          <div className="mx-auto mb-12 max-w-2xl text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-semibold text-primary-500">
              <span className="h-2 w-2 rounded-full bg-primary-500" />
              How It Works
            </span>
            <h2 className="mt-4 text-3xl font-bold text-text-primary">Detection pipeline in action</h2>
          </div>
          <div className="relative">
            <div className="absolute left-6 top-8 hidden h-0.5 w-[calc(100%-3rem)] bg-primary-200 md:block" />
            <div className="stagger-children grid grid-cols-2 gap-6 md:grid-cols-6">
              {workflow.map(({ icon, label }, i) => (
                <div key={label} className="relative flex flex-col items-center text-center">
                  <div className="hover-scale relative z-10 flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-primary-500 ring-4 ring-white">
                    <Icon name={icon} size={20} />
                  </div>
                  <span className="mt-3 text-xs font-semibold text-text-secondary md:text-sm">{label}</span>
                  <span className="mt-1 text-[10px] font-medium text-text-disabled">Step {i + 1}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ======================== */}
      {/* STATISTICS                 */}
      {/* ======================== */}
      <section ref={statsRef} className="reveal border-t border-surface-300 bg-primary-500">
        <div className="mx-auto max-w-7xl px-4 py-16 md:px-6 md:py-20">
          <div className="stagger-children grid grid-cols-2 gap-8 text-center md:grid-cols-4">
            {[
              { label: 'Training Emails', value: 195740, suffix: '' },
              { label: 'Test Holdout', value: 39148, suffix: '' },
              { label: 'Test Accuracy', value: 98.25, suffix: '%' },
              { label: 'Phishing F1', value: 98.1, suffix: '%' },
            ].map(({ label, value, suffix, prefix }) => (
              <div key={label}>
                <StatValue num={value} prefix={prefix} suffix={suffix} visible={statsVisible} />
                <p className="mt-1.5 text-sm font-medium text-white/70">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

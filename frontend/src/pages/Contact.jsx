import React, { useState } from 'react';
import Icon from '../components/Icon.jsx';
import useScrollReveal from '../hooks/useScrollReveal.js';

const faq = [
  { q: 'How does the phishing detection work?', a: 'The system uses an ensemble ML model (Logistic Regression + Random Forest) with TF-IDF vectorization and n-gram analysis to classify emails. It also analyzes URLs, sender domains, and urgency signals for comprehensive detection.' },
  { q: 'What file formats are supported?', a: 'You can paste email text directly, upload .txt files, or .eml files. The system automatically extracts the sender from email headers when using .eml format.' },
  { q: 'Is my data stored securely?', a: 'Scan history is stored locally in SQLite with SHA-256 deduplication. If AI summaries are enabled, up to 2,000 characters of email text are sent to the configured LLM provider; with no API key (or AI_EXPLANATIONS_ENABLED=false) nothing leaves the server.' },
  { q: 'Can I use this in production?', a: 'It ships optional API-key gating (X-API-Key) and bounded in-process rate limiting, but per-user history isolation and Redis/shared rate limiting are intentionally out of scope. See docs/security.md for the trust boundaries.' },
  { q: 'How accurate is the detection?', a: 'The classifier scores 98.25% accuracy and 98.1% phishing F1 on a 39,148-mail stratified holdout, and the end-to-end policy reaches 0.4% false positives at 93.3% recall. These are holdout metrics, not a claim about unseen campaigns; see the repo reports for the raw numbers.' },
];

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });
  const [submitted, setSubmitted] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);
  const formRef = useScrollReveal();
  const infoRef = useScrollReveal();
  const faqRef = useScrollReveal();

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function handleSubmit(e) {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 4000);
  }

  return (
    <div className="mx-auto max-w-7xl animate-fade-in-up px-4 py-16 md:px-6">
      {/* Header */}
      <div className="mb-12 animate-slide-up">
        <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-semibold text-primary-500">
          <span className="h-2 w-2 rounded-full bg-primary-500" />
          Get in Touch
        </span>
        <h1 className="mt-4 text-3xl font-bold text-text-primary">Contact & Support</h1>
        <p className="mt-2 text-text-secondary">Have questions or feedback? We&apos;d love to hear from you.</p>
      </div>

      <div ref={formRef} className="reveal grid gap-10 lg:grid-cols-5">
        {/* Left: Form */}
        <div className="lg:col-span-3">
          <div className="rounded-2xl border border-surface-300 bg-white p-6 shadow-card md:p-8">
            {submitted ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-safe-50">
                  <Icon name="check" size={28} className="text-safe-500" />
                </div>
                <h3 className="text-lg font-bold text-text-primary">Message sent!</h3>
                <p className="mt-1 text-sm text-text-secondary">We&apos;ll get back to you as soon as possible.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} action="mailto:prathamwankhade124@gmail.com" encType="text/plain" method="POST" className="space-y-5">
                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-text-primary">Name</label>
                    <input
                      name="name"
                      value={form.name}
                      onChange={handleChange}
                      required
                      placeholder="Your name"
                      className="w-full rounded-lg border border-surface-300 bg-surface-50 px-4 py-3 text-sm text-text-primary outline-none transition focus:border-primary-500 focus:ring-2 focus:ring-primary-50"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-text-primary">Email</label>
                    <input
                      name="email"
                      type="email"
                      value={form.email}
                      onChange={handleChange}
                      required
                      placeholder="you@example.com"
                      className="w-full rounded-lg border border-surface-300 bg-surface-50 px-4 py-3 text-sm text-text-primary outline-none transition focus:border-primary-500 focus:ring-2 focus:ring-primary-50"
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-text-primary">Subject</label>
                  <input
                    name="subject"
                    value={form.subject}
                    onChange={handleChange}
                    required
                    placeholder="How can we help?"
                    className="w-full rounded-lg border border-surface-300 bg-surface-50 px-4 py-3 text-sm text-text-primary outline-none transition focus:border-primary-500 focus:ring-2 focus:ring-primary-50"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-text-primary">Message</label>
                  <textarea
                    name="message"
                    value={form.message}
                    onChange={handleChange}
                    required
                    rows={5}
                    placeholder="Describe your issue or question..."
                    className="w-full resize-none rounded-lg border border-surface-300 bg-surface-50 px-4 py-3 text-sm text-text-primary outline-none transition focus:border-primary-500 focus:ring-2 focus:ring-primary-50"
                  />
                </div>
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 rounded-xl bg-primary-500 px-7 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-600 active:scale-[0.97]"
                >
                <Icon name="send" size={18} />
                  Send Message
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Right: Info */}
        <div ref={infoRef} className="reveal space-y-6 lg:col-span-2">
          {[
            { icon: 'mail', label: 'Email', value: 'prathamwankhade124@gmail.com', href: 'mailto:prathamwankhade124@gmail.com' },
            { icon: 'github', label: 'GitHub', value: 'github.com/PrathamWankhade', href: 'https://github.com/PrathamWankhade' },
            { icon: 'linkedin', label: 'LinkedIn', value: 'linkedin.com/in/pratham-wankhade', href: 'https://www.linkedin.com/in/pratham-wankhade' },
            { icon: 'notification', label: 'Phone', value: '+91 7757848083', href: 'tel:+917757848083' },
          ].map(({ icon, label, value, href }) => (
            <a key={label} href={href} target="_blank" rel="noopener noreferrer" className="flex items-start gap-4 rounded-xl border border-surface-300 bg-white p-5 shadow-card no-underline hover-lift">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary-500">
                <Icon name={icon} size={18} />
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">{label}</p>
                <p className="text-sm text-text-secondary">{value}</p>
              </div>
            </a>
          ))}

          {/* Social */}
          <div className="rounded-xl border border-surface-300 bg-white p-5 shadow-card">
            <p className="mb-3 text-sm font-medium text-text-primary">Follow me</p>
            <div className="flex flex-wrap gap-2">
              <a href="https://github.com/PrathamWankhade" target="_blank" rel="noopener noreferrer" className="rounded-lg border border-surface-300 px-4 py-2 text-xs font-medium text-text-secondary anim-standard hover:border-primary-500 hover:text-primary-500">
                GitHub
              </a>
              <a href="https://www.linkedin.com/in/pratham-wankhade" target="_blank" rel="noopener noreferrer" className="rounded-lg border border-surface-300 px-4 py-2 text-xs font-medium text-text-secondary anim-standard hover:border-primary-500 hover:text-primary-500">
                LinkedIn
              </a>
              <a href="https://www.instagram.com/hey.its.me.ichi" target="_blank" rel="noopener noreferrer" className="rounded-lg border border-surface-300 px-4 py-2 text-xs font-medium text-text-secondary anim-standard hover:border-primary-500 hover:text-primary-500">
                Instagram
              </a>
              <a href="mailto:prathamwankhade124@gmail.com" className="rounded-lg border border-surface-300 px-4 py-2 text-xs font-medium text-text-secondary anim-standard hover:border-primary-500 hover:text-primary-500">
                Email
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div ref={faqRef} className="reveal mt-16">
        <div className="mb-8 text-center">
          <h2 className="text-2xl font-bold text-text-primary">Frequently Asked Questions</h2>
        </div>
        <div className="mx-auto max-w-3xl space-y-3">
          {faq.map(({ q, a }, i) => (
            <div key={i} className="hover-lift rounded-xl border border-surface-300 bg-white shadow-card">
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="flex w-full items-center justify-between px-5 py-4 text-left text-sm font-medium text-text-primary anim-fast hover:bg-surface-50"
              >
                {q}
                <Icon name="chevronDown" size={16} className={`text-text-disabled anim-standard ${openFaq === i ? 'rotate-180' : ''}`} />
              </button>
              {openFaq === i && (
                <div className="animate-slide-up border-t border-surface-200 px-5 py-4 text-sm leading-6 text-text-secondary">{a}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

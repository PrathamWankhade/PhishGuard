import React from 'react';

export default function About() {
  return (
    <div className="mx-auto max-w-7xl animate-fade-in-up px-4 py-16 md:px-6">
      <div className="mb-10 animate-slide-up">
        <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-1.5 text-sm font-semibold text-primary-500">
          <span className="h-2 w-2 rounded-full bg-primary-500" />
          Architecture
        </span>
        <h1 className="mt-4 text-3xl font-bold text-text-primary md:text-4xl">About the Project</h1>
        <p className="mt-2 text-base text-text-secondary">
          Understanding how the AI-based phishing detection system works.
        </p>
      </div>

      <div className="stagger-children grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {[
          { title: 'Machine Learning Model', desc: 'Soft-voting LogisticRegression + RandomForest trained on 195,740 labeled emails with TF-IDF vectorization (50k features, n-grams 1–3). Reported on a 39,148-mail stratified holdout.' },
          { title: 'NLP Preprocessing', desc: 'Text cleaning, tokenization, stopword removal, and stemming to normalize email content before feature extraction.' },
          { title: 'URL Analysis', desc: 'Purely lexical detection of suspicious TLDs, shortened URLs, IP-based links, punycode/homograph attacks, and phishing keywords in domain names — no outbound fetches.' },
          { title: 'Sender Analysis', desc: 'Scores the sender domain against suspicious TLDs, impersonation keywords, and header mismatches (Reply-To / Return-Path).' },
          { title: 'Explainable AI', desc: 'Deterministic, inspectable evidence signals are the source of truth; an optional LLM summary (OpenRouter, requires a key) may be layered on and can never change the verdict.' },
          { title: 'Tech Stack', desc: 'React 19 + Tailwind CSS frontend, FastAPI backend, scikit-learn ML pipeline, SQLite database, and Docker deployment.' },
        ].map(({ title, desc }) => (
            <div key={title} className="hover-lift rounded-xl border border-surface-300 bg-white p-6 shadow-card">
            <h3 className="font-semibold text-text-primary">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-text-secondary">{desc}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-xl border border-surface-300 bg-white p-6 shadow-card">
        <h3 className="font-semibold text-text-primary">System Architecture</h3>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          {['React UI', 'FastAPI', 'ML Pipeline', 'SQLite DB', 'Optional LLM Summaries'].map((item) => (
            <span key={item} className="rounded-lg border border-surface-300 bg-surface-50 px-4 py-2 text-sm font-medium text-text-secondary">
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

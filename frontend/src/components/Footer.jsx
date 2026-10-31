import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import Icon from './Icon.jsx';

const footerLinks = {
  Platform: [
    { to: '/', label: 'Home' },
    { to: '/scanner', label: 'Email Scanner' },
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/analytics', label: 'Threat Signals' },
  ],
  Resources: [
    { to: '/contact', label: 'Contact' },
    { to: '/', label: 'Privacy Policy' },
  ],
};

export default function Footer() {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  function handleSubscribe(e) {
    e.preventDefault();
    if (email) {
      setSubscribed(true);
      setEmail('');
      setTimeout(() => setSubscribed(false), 3000);
    }
  }

  return (
    <footer className="relative border-t border-surface-300 bg-white">
      {/* Top gradient accent */}
      <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-primary-500 via-primary-400 to-primary-500" />

      <div className="mx-auto max-w-7xl px-4 py-12 md:px-6 lg:py-16">
        {/* Top section: Brand + Links */}
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-5">
          {/* Brand column */}
          <div className="lg:col-span-2">
            <NavLink to="/" className="flex items-center gap-2.5 font-bold text-text-primary no-underline">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-500 shadow-sm">
                <Icon name="shieldCheck" size={18} className="text-white" />
              </span>
              <span className="text-lg tracking-tight">PhishGuard</span>
            </NavLink>
            <p className="mt-4 max-w-sm text-sm leading-6 text-text-secondary">
              AI-powered phishing email detection system using machine learning, natural language processing, and explainable AI to protect against email-based cyber threats.
            </p>

            {/* Social */}
            <div className="mt-6 flex gap-2.5">
              <a href="https://github.com/PrathamWankhade" target="_blank" rel="noopener noreferrer" className="hover-social flex h-10 w-10 items-center justify-center rounded-xl border border-surface-300 text-text-secondary anim-standard hover:border-primary-500 hover:bg-primary-50 hover:text-primary-500" aria-label="GitHub">
                <Icon name="github" size={16} />
              </a>
              <a href="https://www.linkedin.com/in/pratham-wankhade" target="_blank" rel="noopener noreferrer" className="hover-social flex h-10 w-10 items-center justify-center rounded-xl border border-surface-300 text-text-secondary anim-standard hover:border-primary-500 hover:bg-primary-50 hover:text-primary-500" aria-label="LinkedIn">
                <svg viewBox="0 0 24 24" fill="none" width="16" height="16" stroke="currentColor" strokeWidth="1.5"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-4 0v7h-4v-7a6 6 0 016-6zM2 9h4v12H2z" strokeLinecap="round" strokeLinejoin="round" /><circle cx="4" cy="4" r="2" fill="currentColor" /></svg>
              </a>
              <a href="https://www.instagram.com/hey.its.me.ichi" target="_blank" rel="noopener noreferrer" className="hover-social flex h-10 w-10 items-center justify-center rounded-xl border border-surface-300 text-text-secondary anim-standard hover:border-primary-500 hover:bg-primary-50 hover:text-primary-500" aria-label="Instagram">
                <Icon name="instagram" size={16} />
              </a>
              <a href="mailto:prathamwankhade124@gmail.com" className="hover-social flex h-10 w-10 items-center justify-center rounded-xl border border-surface-300 text-text-secondary anim-standard hover:border-primary-500 hover:bg-primary-50 hover:text-primary-500" aria-label="Email">
                <Icon name="mail" size={16} />
              </a>
            </div>
          </div>

          {/* Link Groups */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h4 className="mb-4 text-xs font-bold uppercase tracking-widest text-text-disabled">{title}</h4>
              <ul className="space-y-3">
                {links.map(({ to, label }) => (
                  <li key={label}>
                    <NavLink
                      to={to}
                      end={to === '/'}
                      className={({ isActive }) =>
                        `text-sm no-underline anim-standard ${
                          isActive ? 'text-primary-500 font-semibold' : 'text-text-secondary hover:text-primary-500'
                        }`
                      }
                    >
                      {label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Middle: Newsletter */}
        <div className="mt-10 rounded-2xl border border-surface-300 bg-gradient-to-br from-surface-50 to-white p-6 shadow-sm md:p-8">
          <div className="flex flex-col items-start gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-4">
              <div className="hidden shrink-0 rounded-xl bg-primary-50 p-3 sm:block">
                <Icon name="mail" size={20} className="text-primary-500" />
              </div>
              <div>
                <h4 className="text-base font-bold text-text-primary">Stay updated</h4>
                <p className="mt-1 text-sm text-text-secondary">Get notified about new phishing threats and feature updates.</p>
              </div>
            </div>
            <form onSubmit={handleSubscribe} className="flex w-full shrink-0 gap-2 sm:w-auto">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="min-w-0 flex-1 rounded-xl border border-surface-300 bg-white px-4 py-2.5 text-sm text-text-primary outline-none anim-standard focus:border-primary-500 focus:ring-2 focus:ring-primary-50 sm:w-56"
              />
              <button
                type="submit"
                className="hover-scale inline-flex items-center gap-2 rounded-xl bg-primary-500 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-600"
              >
                {subscribed ? (
                  <><Icon name="check" size={14} /> Subscribed</>
                ) : (
                  <><Icon name="send" size={14} /> Subscribe</>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-surface-200 pt-6 text-sm sm:flex-row">
          <div className="flex flex-col items-center gap-2 sm:flex-row sm:gap-4">
            <p className="text-text-disabled">
              &copy; {new Date().getFullYear()} PhishGuard. Built by{' '}
              <a href="https://github.com/PrathamWankhade" target="_blank" rel="noopener noreferrer" className="font-medium text-text-secondary hover:text-primary-500">
                Pratham Wankhade
              </a>
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-text-disabled">
            <span className="flex items-center gap-1">
              <Icon name="star" size={12} />
              Open Source
            </span>
            <span className="hidden text-surface-300 sm:inline">&middot;</span>
            <span>v2.0</span>
            <span className="hidden text-surface-300 sm:inline">&middot;</span>
            <span>React + FastAPI</span>
            <span className="hidden text-surface-300 sm:inline">&middot;</span>
            <span>MIT License</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

# Frontend — React Phishing Detection UI

React 19 SPA built with Vite, Tailwind CSS (CDN), and Recharts. Features lazy-loaded pages, scroll-reveal animations, and an inline SVG icon system — zero external icon or animation libraries.

## Directory Layout

```
frontend/
└── src/
    ├── components/            # 10 reusable UI components
    │   ├── Navbar.jsx         # Sticky nav with live notification dropdown
    │   ├── Footer.jsx         # Site footer with social links
    │   ├── EmailInput.jsx     # Text area + Ctrl/Cmd+Enter scan form
    │   ├── PredictionCard.jsx # Verdict, risk score, P(phishing), evidence
    │   ├── UploadEmail.jsx    # Drag-and-drop .txt/.eml uploader
    │   ├── Icon.jsx           # 44 inline SVG icons (single source of truth)
    │   ├── Toast.jsx          # Toast provider + renderer
    │   ├── Skeleton.jsx       # Loading placeholder
    │   ├── Loader.jsx         # Spinner overlay
    │   └── ScrollToTop.jsx    # Scrolls to top on route change
    ├── pages/                 # 7 lazy-loaded route pages
    │   ├── Home.jsx           # Landing page (hero, features, stats)
    │   ├── Scanner.jsx        # Dedicated email scanner
    │   ├── Dashboard.jsx      # KPI cards, charts, scan history table
    │   ├── History.jsx        # Sortable/filterable scan history
    │   ├── Analytics.jsx      # Threat-signal reference table
    │   ├── About.jsx          # Architecture / how it works
    │   └── Contact.jsx        # Contact form + FAQ accordion
    ├── hooks/
    │   ├── useScrollReveal.js # IntersectionObserver-based reveal
    │   └── useCountUp.js      # Animated number counter
    ├── services/
    │   └── api.js             # API client (`scanEmail`) + opt-in heuristic helper
    └── styles/
        ├── global.css         # Base styles, fonts, selection colors
        └── animations.css     # 21 keyframes + 41 animation utility classes
```

## Pages & Routes

| Route | Page | Description |
|---|---|---|
| `/` | Home | Hero, feature grid, workflow, stats |
| `/scanner` | Scanner | Paste/upload email for scanning |
| `/dashboard` | Dashboard | KPI cards, charts, scan history table |
| `/history` | History | Sortable/filterable scan history with evidence |
| `/analytics` | Analytics | Threat-signal reference (severity + examples) |
| `/about` | About | Architecture and how the system works |
| `/contact` | Contact | Contact form, info cards, FAQ accordion |

Routing uses `HashRouter`. All pages are lazy-loaded via `React.lazy()`.

## Styling

- **Tailwind CSS** loaded via CDN (`cdn.tailwindcss.com`) with a custom config in `index.html`
- Custom color palette: `primary`, `safe`, `suspicious`, `danger`, `surface`, `text`
- Custom shadows: `shadow-card`, `shadow-card-hover`, `shadow-elevated`, `shadow-elevated-lg`
- 21 `@keyframes` and 41 animation utility classes in `animations.css` — fade, slide, scale, float, pulse, shimmer, ripple
- Hardware-accelerated transitions via `will-change` and `transform`/`opacity`-only animations

## Development

```bash
npm run dev          # Dev server on port 3000
npm run lint         # ESLint (undefined components, hook misuse)
npm run build        # Production build → dist/
npm run preview      # Preview production build
```

## Build Output

- 10 JS chunks: shared `index` + one per page (7) + two shared hook chunks
  (`useScrollReveal`, `useCountUp`); ~262 kB initial, ~81 kB gzipped
- Single CSS file with all animation keyframes
- No external font/icon CDN dependencies in production

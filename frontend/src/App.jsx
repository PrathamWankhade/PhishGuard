import React, { Suspense, lazy } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';
import ScrollToTop from './components/ScrollToTop.jsx';
import { useToast, Toast } from './components/Toast.jsx';

const Home = lazy(() => import('./pages/Home.jsx'));
const Scanner = lazy(() => import('./pages/Scanner.jsx'));
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));
const Analytics = lazy(() => import('./pages/Analytics.jsx'));
const Contact = lazy(() => import('./pages/Contact.jsx'));

function PageLoader() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-primary-500 border-t-transparent" />
        <p className="text-sm text-text-secondary">Loading...</p>
      </div>
    </div>
  );
}

function ToastRenderer() {
  const { toasts, dismiss } = useToast();
  return (
    <div className="pointer-events-none fixed top-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onDismiss={() => dismiss(t.id)} />
      ))}
    </div>
  );
}

export default function App() {
  return (
    <HashRouter>
      <ScrollToTop />
      <div className="min-h-screen bg-surface-100 text-text-primary">
        <Navbar />
        <main>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </main>
        <ToastRenderer />
        <Footer />
      </div>
    </HashRouter>
  );
}

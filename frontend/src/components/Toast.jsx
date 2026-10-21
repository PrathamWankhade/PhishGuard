import React, { useState, useCallback, useEffect } from 'react';
import Icon from './Icon.jsx';

const TOAST_LIMIT = 5;
const TOAST_REMOVE_DELAY = 4000;

const variantStyles = {
  default: 'bg-surface-100 text-text-primary border border-surface-300',
  success: 'bg-safe-50 text-safe-700 border border-safe-200',
  destructive: 'bg-danger-50 text-danger-700 border border-danger-200',
  warning: 'bg-suspicious-50 text-suspicious-700 border border-suspicious-200',
};

function Toast({ id, title, description, variant = 'default', className, onDismiss }) {
  return (
    <div key={id} className={`fixed top-4 right-4 z-50 w-80 rounded-xl border p-4 shadow-elevated animate-slide-in-right ${variantStyles[variant]} ${className || ''}`}>
      <div className="flex items-start gap-3">
        {variant === 'success' && (
          <Icon name="check" size={16} className="mt-0.5 shrink-0" />
        )}
        {variant === 'destructive' && (
          <Icon name="danger" size={16} className="mt-0.5 shrink-0" />
        )}
        {variant === 'warning' && (
          <Icon name="warning" size={16} className="mt-0.5 shrink-0" />
        )}
        {variant === 'default' && (
          <Icon name="info" size={16} className="mt-0.5 shrink-0 text-text-disabled" />
        )}
        <div className="flex-1 min-w-0">
          {title && <h4 className="text-sm font-semibold text-text-primary">{title}</h4>}
          {description && <p className="mt-0.5 text-xs text-text-secondary">{description}</p>}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-2 shrink-0 rounded-lg p-1 text-text-disabled hover:bg-surface-200 hover:text-text-primary transition"
            aria-label="Dismiss"
          >
            <Icon name="close" size={14} />
          </button>
        )}
      </div>
    </div>
  );
}

const listeners = [];
let memoryState = [];

function dispatch() {
  listeners.forEach((l) => l(memoryState));
}

export function useToast() {
  const [toasts, setToasts] = useState(memoryState);

  useEffect(() => {
    listeners.push(setToasts);
    return () => {
      const idx = listeners.indexOf(setToasts);
      if (idx > -1) listeners.splice(idx, 1);
    };
  }, []);

  const toast = useCallback(({ title, description, variant }) => {
    const id = Math.random().toString(36).slice(2, 9);
    const newToast = { id, title, description, variant };
    memoryState = [...memoryState, newToast].slice(-TOAST_LIMIT);
    dispatch();
    setTimeout(() => {
      memoryState = memoryState.filter((t) => t.id !== id);
      dispatch();
    }, TOAST_REMOVE_DELAY);
    return id;
  }, []);

  const dismiss = useCallback((id) => {
    memoryState = id ? memoryState.filter((t) => t.id !== id) : [];
    dispatch();
  }, []);

  return { toast, dismiss, toasts };
}

export function ToastProvider({ children }) {
  return <>{children}</>;
}

export { Toast };

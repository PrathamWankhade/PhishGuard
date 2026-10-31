export function SkeletonCard({ className = '' }) {
  return (
    <div className={`rounded-2xl border border-surface-300 bg-white p-6 ${className}`}>
      <div className="mb-4 h-11 w-11 rounded-xl bg-surface-200 animate-shimmer" />
      <div className="mb-2 h-5 w-3/4 rounded bg-surface-200 animate-shimmer" />
      <div className="h-4 w-full rounded bg-surface-200 animate-shimmer" />
      <div className="mt-1 h-4 w-5/6 rounded bg-surface-200 animate-shimmer" />
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div className="rounded-xl border border-surface-300 bg-white p-6">
      <div className="mb-4 flex gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-4 flex-1 rounded bg-surface-200 animate-shimmer" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="mt-3 flex gap-4">
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="h-3 flex-1 rounded bg-surface-200 animate-shimmer" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 rounded bg-surface-200 animate-shimmer"
          style={{ width: i === lines - 1 ? '60%' : '100%' }}
        />
      ))}
    </div>
  );
}

export function SkeletonCircle({ size = 12, className = '' }) {
  return (
    <div
      className={`rounded-full bg-surface-200 animate-shimmer ${className}`}
      style={{ width: size * 4, height: size * 4 }}
    />
  );
}

export function SkeletonStat({ className = '' }) {
  return (
    <div className={`rounded-xl border border-surface-300 bg-white p-5 ${className}`}>
      <div className="mb-3 h-3 w-1/2 rounded bg-surface-200 animate-shimmer" />
      <div className="h-8 w-1/3 rounded bg-surface-200 animate-shimmer" />
    </div>
  );
}

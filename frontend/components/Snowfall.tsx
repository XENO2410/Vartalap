'use client';

import { useMemo } from 'react';

// Sprinkles ~50 snowflakes at random horizontal positions / sizes / speeds.
// The animation lives in globals.css so the SSR output stays static.
export function Snowfall({ count = 50 }: { count?: number }) {
  const flakes = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      key: i,
      left: Math.random() * 100,
      size: 8 + Math.random() * 18,
      duration: 8 + Math.random() * 14,
      delay: -Math.random() * 18,
      char: Math.random() > 0.5 ? '❄' : '❅',
      opacity: 0.5 + Math.random() * 0.4,
    }));
  }, [count]);

  return (
    <div className="snow-layer" aria-hidden="true">
      {flakes.map((f) => (
        <span
          key={f.key}
          style={{
            left: `${f.left}%`,
            fontSize: `${f.size}px`,
            animationDuration: `${f.duration}s`,
            animationDelay: `${f.delay}s`,
            opacity: f.opacity,
          }}
        >
          {f.char}
        </span>
      ))}
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';

type Flake = {
  key: number;
  left: number;
  size: number;
  duration: number;
  delay: number;
  char: string;
  opacity: number;
};

// Rendered only after mount so the random positions never diverge between
// SSR and client hydration.
export function Snowfall({ count = 50 }: { count?: number }) {
  const [flakes, setFlakes] = useState<Flake[]>([]);

  useEffect(() => {
    setFlakes(
      Array.from({ length: count }, (_, i) => ({
        key: i,
        left: Math.random() * 100,
        size: 8 + Math.random() * 18,
        duration: 8 + Math.random() * 14,
        delay: -Math.random() * 18,
        char: Math.random() > 0.5 ? '❄' : '❅',
        opacity: 0.5 + Math.random() * 0.4,
      })),
    );
  }, [count]);

  if (flakes.length === 0) return null;

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

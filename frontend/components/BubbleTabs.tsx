'use client';

import { useRef } from 'react';

export const BUBBLES = [
  'All',
  'HR',
  'Download',
  'Status',
  'Aha',
  'Law',
  'Conversational BI',
  'Axis Phone',
  'FINANCIAL ADVISOR',
  'IT Helpdesk',
  'CR',
] as const;

export type BubbleName = (typeof BUBBLES)[number];

type Props = {
  active: BubbleName;
  onSelect: (name: BubbleName) => void;
};

export function BubbleTabs({ active, onSelect }: Props) {
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  const scroll = (dir: 1 | -1) => {
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollBy({ left: dir * 240, behavior: 'smooth' });
  };

  return (
    <div className="flex w-full items-center gap-2">
      <button
        aria-label="Scroll bubbles left"
        onClick={() => scroll(-1)}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-axis/30 text-axis hover:bg-axis-soft"
      >
        «
      </button>
      <div
        ref={scrollerRef}
        className="scroll-slim flex flex-1 items-center gap-2 overflow-x-auto px-1 py-1"
      >
        {BUBBLES.map((b) => {
          const isActive = b === active;
          return (
            <button
              key={b}
              onClick={() => onSelect(b)}
              className={
                'whitespace-nowrap rounded-full border px-4 py-1.5 text-sm font-medium transition ' +
                (isActive
                  ? 'border-axis bg-axis text-white shadow-card'
                  : 'border-axis/30 bg-white text-axis hover:bg-axis-soft')
              }
            >
              {b}
            </button>
          );
        })}
      </div>
      <button
        aria-label="Scroll bubbles right"
        onClick={() => scroll(1)}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-axis/30 text-axis hover:bg-axis-soft"
      >
        »
      </button>
    </div>
  );
}

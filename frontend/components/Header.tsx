'use client';

import Link from 'next/link';

export function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-axis-softer bg-axis text-white shadow-card">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 sm:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span
            aria-label="Vartalaap logo"
            className="grid h-9 w-9 place-items-center rounded-md bg-white text-lg font-bold text-axis"
          >
            वा
          </span>
          <div className="flex flex-col leading-tight">
            <span className="deva text-lg font-semibold tracking-tight">वार्तालाप</span>
            <span className="text-[11px] uppercase tracking-widest text-white/70">
              Deep Intelligence Assistant
            </span>
          </div>
        </Link>
        <div className="hidden items-center gap-6 text-sm sm:flex">
          <a href="/docs-hub" className="text-white/85 hover:text-white">Docs</a>
          <a
            href={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/docs`}
            target="_blank"
            rel="noreferrer"
            className="text-white/85 hover:text-white"
          >
            API
          </a>
          <span
            className="grid h-8 w-8 place-items-center rounded-full bg-white/15 text-xs font-semibold"
            title="Session user"
          >
            SM
          </span>
        </div>
      </div>
    </header>
  );
}

'use client';

import Link from 'next/link';

import { initials } from '@/lib/session';
import type { SessionUser } from '@/types/chat';

type Props = {
  user: SessionUser | null;
  onSignOut: () => void;
};

export function Header({ user, onSignOut }: Props) {
  return (
    <header className="sticky top-0 z-30 border-b border-axis-softer bg-gradient-to-r from-axis-dark via-axis to-axis-bright text-white shadow-card">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 sm:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span
            aria-label="Vartalaap logo"
            className="grid h-9 w-9 place-items-center rounded-md bg-white/95 text-lg font-bold text-axis shadow-frost"
          >
            वा
          </span>
          <div className="flex flex-col leading-tight">
            <span className="deva text-lg font-semibold tracking-tight">वार्तालाप</span>
            <span className="text-[11px] uppercase tracking-widest text-white/75">
              Snow Edition · Deep Intelligence Assistant
            </span>
          </div>
        </Link>
        <div className="hidden items-center gap-5 text-sm sm:flex">
          <a
            href={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/docs`}
            target="_blank"
            rel="noreferrer"
            className="text-white/85 hover:text-white"
          >
            API
          </a>
          <a
            href={process.env.NEXT_PUBLIC_MLFLOW_URL || 'http://localhost:5000'}
            target="_blank"
            rel="noreferrer"
            className="text-white/85 hover:text-white"
            title="MLflow tracking UI"
          >
            MLflow
          </a>
          {user ? (
            <div className="flex items-center gap-3">
              <div className="flex flex-col items-end leading-tight">
                <span className="text-sm font-semibold">{user.displayName}</span>
                <span className="font-mono text-[10px] text-white/70">{user.userId}</span>
              </div>
              <span
                className="grid h-8 w-8 place-items-center rounded-full bg-white/15 text-xs font-semibold"
                title={user.userId}
              >
                {initials(user.displayName)}
              </span>
              <button
                onClick={onSignOut}
                className="rounded-full border border-white/30 px-3 py-1 text-xs font-semibold text-white/85 hover:bg-white/10"
              >
                Sign out
              </button>
            </div>
          ) : (
            <span
              className="grid h-8 w-8 place-items-center rounded-full bg-white/15 text-xs font-semibold"
              title="Not signed in"
            >
              ??
            </span>
          )}
        </div>
      </div>
    </header>
  );
}

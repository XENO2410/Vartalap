'use client';

import { FormEvent, useEffect, useState } from 'react';

import { loadSessionUser, saveSessionUser } from '@/lib/session';
import type { SessionUser } from '@/types/chat';

type Props = {
  onReady: (user: SessionUser) => void;
};

export function LoginGate({ onReady }: Props) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [name, setName] = useState('');
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const existing = loadSessionUser();
    setUser(existing);
    setHydrated(true);
    if (existing) onReady(existing);
  }, [onReady]);

  if (!hydrated) return null;
  if (user) return null;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    const created = saveSessionUser(trimmed);
    setUser(created);
    onReady(created);
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-axis-ink/40 backdrop-blur-sm">
      <form
        onSubmit={submit}
        className="w-[min(420px,calc(100vw-32px))] rounded-3xl bg-white p-6 shadow-card"
      >
        <div className="mb-4 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-axis text-white">
            <span className="deva font-bold">वा</span>
          </span>
          <div>
            <div className="deva text-lg font-semibold text-axis">वार्तालाप</div>
            <div className="text-[11px] uppercase tracking-widest text-axis-ink/60">
              Sign in to continue
            </div>
          </div>
        </div>
        <p className="mb-4 text-sm text-axis-ink/75">
          This is a demo build — no password required. Pick any display name;
          we&apos;ll assign you a stable <code className="rounded bg-axis-softer px-1">user_id</code>
          {' '}stored in your browser and attach it to every query the assistant logs.
        </p>
        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-axis-ink/70">
          Display name
        </label>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Aarav Sharma"
          className="w-full rounded-full border-2 border-axis/40 bg-white px-4 py-2 text-sm outline-none focus:border-axis"
        />
        <button
          type="submit"
          disabled={!name.trim()}
          className={
            'mt-4 w-full rounded-full px-4 py-2 text-sm font-semibold text-white transition ' +
            (name.trim() ? 'bg-axis hover:bg-axis-dark' : 'cursor-not-allowed bg-axis/30')
          }
        >
          Enter वार्तालाप
        </button>
      </form>
    </div>
  );
}

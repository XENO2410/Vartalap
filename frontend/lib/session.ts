'use client';

import type { SessionUser } from '@/types/chat';

const STORAGE_KEY = 'vartalaap.session.user.v1';

function randomUserId(): string {
  const rnd =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID().replace(/-/g, '').slice(0, 10)
      : Math.random().toString(36).slice(2, 12);
  return `u_${rnd}`;
}

export function loadSessionUser(): SessionUser | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SessionUser;
    if (!parsed?.userId || !parsed?.displayName) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function saveSessionUser(displayName: string): SessionUser {
  const trimmed = displayName.trim() || 'Guest';
  const user: SessionUser = {
    userId: randomUserId(),
    displayName: trimmed,
    createdAt: Date.now(),
  };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  return user;
}

export function clearSessionUser(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(STORAGE_KEY);
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).slice(0, 2);
  if (!parts.length) return '??';
  return parts.map((p) => p[0]?.toUpperCase() ?? '').join('') || '??';
}

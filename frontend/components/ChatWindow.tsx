'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { sendChat, sendFeedback } from '@/lib/api';
import { clearSessionUser, loadSessionUser } from '@/lib/session';
import type { ChatMessage, FeedbackValue, SessionUser } from '@/types/chat';

import { BubbleTabs, BubbleName } from './BubbleTabs';
import { Header } from './Header';
import { LandingHero } from './LandingHero';
import { LoginGate } from './LoginGate';
import { MessageBubble } from './MessageBubble';
import { QueryInput } from './QueryInput';

function makeId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}_${Date.now().toString(36)}`;
}

export function ChatWindow() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [bubble, setBubble] = useState<BubbleName>('All');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setUser(loadSessionUser());
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pendingId]);

  const hasChat = messages.length > 0 || pendingId !== null;

  const send = useCallback(
    async (raw: string) => {
      const query = raw.trim();
      if (!query || !user) return;
      setError(null);

      const userMsg: ChatMessage = {
        id: makeId('u'),
        role: 'user',
        content: query,
        createdAt: Date.now(),
      };
      const pendingAssistant: ChatMessage = {
        id: makeId('a'),
        role: 'assistant',
        content: '',
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg, pendingAssistant]);
      setPendingId(pendingAssistant.id);

      const history = messages
        .filter((m) => m.content)
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        const resp = await sendChat({
          query,
          session_id: sessionId,
          user_id: user.userId,
          bubble: bubble === 'All' ? undefined : bubble,
          history,
        });
        setSessionId(resp.session_id);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingAssistant.id
              ? {
                  ...m,
                  content: resp.answer,
                  messageId: resp.message_id,
                  sources: resp.sources,
                  suggestions: resp.suggestions,
                  useCase: resp.use_case,
                  toolUsed: resp.tool_used,
                  events: resp.events,
                  mlflowRunId: resp.mlflow_run_id ?? null,
                  mlflowTraceId: resp.mlflow_trace_id ?? null,
                  feedback: 'none',
                }
              : m,
          ),
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingAssistant.id
              ? {
                  ...m,
                  content:
                    '⚠️ Sorry — the assistant is unreachable right now. Is the backend running on ' +
                    (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') +
                    '?\n\n' +
                    '`' +
                    message +
                    '`',
                }
              : m,
          ),
        );
      } finally {
        setPendingId(null);
      }
    },
    [bubble, messages, sessionId, user],
  );

  const submitFeedback = useCallback(
    async (message: ChatMessage, feedback: FeedbackValue) => {
      if (!user || !message.messageId || !sessionId) return;
      const previous = message.feedback ?? 'none';
      setMessages((prev) =>
        prev.map((m) => (m.id === message.id ? { ...m, feedback } : m)),
      );
      try {
        await sendFeedback({
          session_id: sessionId,
          message_id: message.messageId,
          user_id: user.userId,
          feedback,
          mlflow_run_id: message.mlflowRunId ?? null,
          mlflow_trace_id: message.mlflowTraceId ?? null,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setMessages((prev) =>
          prev.map((m) => (m.id === message.id ? { ...m, feedback: previous } : m)),
        );
      }
    },
    [sessionId, user],
  );

  const startFresh = useCallback(() => {
    setMessages([]);
    setPendingId(null);
    setSessionId(undefined);
    setError(null);
  }, []);

  const signOut = useCallback(() => {
    clearSessionUser();
    startFresh();
    setUser(null);
  }, [startFresh]);

  const placeholderByBubble = useMemo(() => {
    if (bubble === 'Status') return 'Try: #status SR-123456';
    if (bubble === 'Download') return 'Type the form or document you need to download.';
    if (bubble === 'HR' || bubble === 'Law' || bubble === 'IT Helpdesk') {
      return `Ask a ${bubble} related query.`;
    }
    if (bubble === 'Conversational BI') return 'Try: how many customers opened accounts last month?';
    return 'Ask a query with relevant product and customer segment.';
  }, [bubble]);

  return (
    <>
      <Header user={user} onSignOut={signOut} />
      <LoginGate onReady={setUser} />
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-6 sm:px-8">
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs uppercase tracking-widest text-axis-ink/60">
            {hasChat ? 'Session · ' + (sessionId || 'new') : 'New chat'}
            {user && (
              <span className="ml-2 font-mono normal-case tracking-normal text-axis-ink/50">
                user: {user.userId}
              </span>
            )}
          </span>
          {hasChat && (
            <button
              onClick={startFresh}
              className="rounded-full border border-axis-softer bg-white px-3 py-1 text-xs font-semibold text-axis hover:border-axis/40"
            >
              + New Chat
            </button>
          )}
        </div>

        {!hasChat && (
          <div className="flex flex-col items-center gap-6 pt-6 text-center">
            <div className="rounded-full bg-axis-bright/10 px-4 py-1 text-xs font-semibold text-axis">
              Select to ask your law-related queries · Downloads · Status &amp; more
            </div>
            <div className="w-full max-w-3xl">
              <QueryInput
                onSubmit={send}
                disabled={!user}
                placeholder={placeholderByBubble}
              />
            </div>
            <div className="w-full max-w-3xl">
              <BubbleTabs active={bubble} onSelect={setBubble} />
            </div>
            <LandingHero />
          </div>
        )}

        {hasChat && (
          <>
            <div className="flex flex-col gap-6 rounded-3xl bg-white/70 p-4 shadow-card">
              {messages.map((m) => (
                <MessageBubble
                  key={m.id}
                  message={m}
                  isLoading={pendingId === m.id}
                  onPickSuggestion={send}
                  onFeedback={submitFeedback}
                  activeBubble={bubble}
                />
              ))}
              <div ref={bottomRef} />
            </div>

            <div className="sticky bottom-4 flex flex-col gap-3 rounded-3xl bg-white/95 p-4 shadow-card backdrop-blur">
              <BubbleTabs active={bubble} onSelect={setBubble} />
              <QueryInput
                onSubmit={send}
                disabled={pendingId !== null || !user}
                placeholder={placeholderByBubble}
              />
              {error && (
                <div className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
                  {error}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
}

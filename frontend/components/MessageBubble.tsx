'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import type { ChatMessage, FeedbackValue } from '@/types/chat';
import { SourceCard } from './SourceCard';
import { SuggestionChips } from './SuggestionChips';
import { TypingDots } from './TypingDots';

type Props = {
  message: ChatMessage;
  isLoading?: boolean;
  onPickSuggestion?: (value: string) => void;
  onFeedback?: (message: ChatMessage, feedback: FeedbackValue) => Promise<void> | void;
  activeBubble?: string;
};

export function MessageBubble({
  message,
  isLoading,
  onPickSuggestion,
  onFeedback,
  activeBubble,
}: Props) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [feedbackBusy, setFeedbackBusy] = useState<FeedbackValue | null>(null);

  if (isUser) {
    return (
      <div className="flex items-start gap-3">
        <span className="grid h-8 w-8 place-items-center rounded-full bg-slate-100 text-xs font-semibold text-slate-700">
          You
        </span>
        <div className="flex-1 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-axis-ink">
          {message.content}
        </div>
      </div>
    );
  }

  const copyAnswer = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      /* clipboard denied — ignore */
    }
  };

  const submitFeedback = async (value: FeedbackValue) => {
    if (!onFeedback || feedbackBusy) return;
    setFeedbackBusy(value);
    try {
      await onFeedback(message, value);
    } finally {
      setFeedbackBusy(null);
    }
  };

  const currentFeedback = message.feedback ?? 'none';

  const feedbackButtonClass = (value: FeedbackValue) => {
    const isActive = currentFeedback === value;
    const base = 'rounded-full border px-2.5 py-1 text-xs font-semibold transition';
    if (isActive) {
      if (value === 'up') return `${base} border-emerald-500 bg-emerald-50 text-emerald-700`;
      if (value === 'down') return `${base} border-rose-500 bg-rose-50 text-rose-700`;
      return `${base} border-axis bg-axis-soft text-axis`;
    }
    return `${base} border-axis-softer bg-white text-axis-ink/70 hover:border-axis/40`;
  };

  return (
    <div className="flex items-start gap-3">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-axis text-xs font-semibold text-white">
        वा
      </span>
      <div className="flex-1">
        <div className="mb-1 flex flex-wrap items-baseline gap-2">
          <span className="deva font-semibold text-axis">वार्तालाप</span>
          <span className="text-[11px] text-axis-ink/60">
            {new Date(message.createdAt).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
          {message.toolUsed && (
            <span className="rounded-full bg-axis-soft px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-axis">
              tool: {message.toolUsed}
            </span>
          )}
          {message.useCase && (
            <span className="rounded-full bg-axis-softer px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-axis-dark">
              {message.useCase.replaceAll('_', ' ')}
            </span>
          )}
          {message.messageId && (
            <span
              className="rounded-full bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-600"
              title={`Message ID: ${message.messageId}`}
            >
              #{message.messageId.slice(0, 8)}
            </span>
          )}
          {message.mlflowRunId && (
            <span
              className="rounded-full bg-amber-50 px-2 py-0.5 font-mono text-[10px] text-amber-700"
              title={`MLflow run: ${message.mlflowRunId}`}
            >
              mlflow: {message.mlflowRunId.slice(0, 8)}
            </span>
          )}
        </div>

        <div className="prose prose-sm max-w-none rounded-2xl bg-white px-4 py-3 text-axis-ink shadow-card">
          {isLoading ? (
            <TypingDots />
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content || ''}</ReactMarkdown>
          )}
        </div>

        {!isLoading && message.suggestions && message.suggestions.length > 0 && (
          <SuggestionChips
            suggestions={message.suggestions}
            onPick={(s) => onPickSuggestion?.(s)}
          />
        )}

        {!isLoading && message.sources && message.sources.length > 0 && (
          <div className="mt-4">
            <div className="mb-2 text-xs font-semibold text-axis-ink/70">
              वार्तालाप has generated a quick response. Refer to the sources below for
              complete information.
            </div>
            <div className="flex flex-wrap gap-3">
              {message.sources.slice(0, 4).map((src, i) => (
                <SourceCard key={`${src.title}-${i}`} source={src} index={i + 1} />
              ))}
            </div>
            {message.sources.length > 4 && (
              <details className="mt-3">
                <summary className="cursor-pointer text-xs font-semibold text-axis">
                  📎 Show more sources ({message.sources.length - 4} additional)
                </summary>
                <div className="mt-3 flex flex-wrap gap-3">
                  {message.sources.slice(4).map((src, i) => (
                    <SourceCard key={`extra-${i}`} source={src} index={i + 5} />
                  ))}
                </div>
              </details>
            )}
          </div>
        )}

        {!isLoading && (
          <div className="mt-3 flex flex-wrap items-center justify-end gap-2 text-xs text-axis-ink/70">
            {activeBubble && (
              <span className="rounded-full bg-axis px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-white">
                {activeBubble}
              </span>
            )}
            <button
              type="button"
              title="Copy answer"
              onClick={copyAnswer}
              className="rounded-full border border-axis-softer bg-white px-2.5 py-1 hover:border-axis/40"
            >
              {copied ? '✅ Copied' : '📋 Copy'}
            </button>
            {onFeedback && (
              <>
                <button
                  type="button"
                  title="Helpful"
                  onClick={() => submitFeedback('up')}
                  disabled={feedbackBusy !== null}
                  className={feedbackButtonClass('up')}
                >
                  👍
                </button>
                <button
                  type="button"
                  title="Not helpful"
                  onClick={() => submitFeedback('down')}
                  disabled={feedbackBusy !== null}
                  className={feedbackButtonClass('down')}
                >
                  👎
                </button>
                <button
                  type="button"
                  title="Clear feedback"
                  onClick={() => submitFeedback('none')}
                  disabled={feedbackBusy !== null}
                  className={feedbackButtonClass('none')}
                >
                  ⬜ None
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

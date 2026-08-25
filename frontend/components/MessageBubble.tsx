'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import type { ChatMessage } from '@/types/chat';
import { SourceCard } from './SourceCard';
import { SuggestionChips } from './SuggestionChips';
import { TypingDots } from './TypingDots';

type Props = {
  message: ChatMessage;
  isLoading?: boolean;
  onPickSuggestion?: (value: string) => void;
  activeBubble?: string;
};

export function MessageBubble({ message, isLoading, onPickSuggestion, activeBubble }: Props) {
  const isUser = message.role === 'user';

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

  return (
    <div className="flex items-start gap-3">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-axis text-xs font-semibold text-white">
        वा
      </span>
      <div className="flex-1">
        <div className="mb-1 flex items-baseline gap-2">
          <span className="deva font-semibold text-axis">वार्तालाप</span>
          <span className="text-[11px] text-axis-ink/60">
            {new Date(message.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
          <div className="mt-3 flex items-center justify-end gap-3 text-xs text-axis-ink/60">
            {activeBubble && (
              <span className="rounded-full bg-axis px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-white">
                {activeBubble}
              </span>
            )}
            <button title="Copy answer" className="hover:text-axis" onClick={() => navigator.clipboard.writeText(message.content)}>
              📋
            </button>
            <button title="Suggest edit" className="hover:text-axis">💡</button>
            <button title="Helpful" className="hover:text-axis">👍</button>
            <button title="Not helpful" className="hover:text-axis">👎</button>
          </div>
        )}
      </div>
    </div>
  );
}

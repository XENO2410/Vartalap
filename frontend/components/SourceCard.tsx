'use client';

import type { ChatSource } from '@/types/chat';

type Props = {
  source: ChatSource;
  index: number;
};

function relevancyClass(relevancy: string): string {
  switch (relevancy.toLowerCase()) {
    case 'high':
      return 'bg-axis-softer text-axis';
    case 'medium':
      return 'bg-amber-50 text-amber-800';
    default:
      return 'bg-slate-100 text-slate-600';
  }
}

export function SourceCard({ source, index }: Props) {
  return (
    <details className="group flex-1 min-w-[220px] max-w-[280px] rounded-2xl border border-axis-softer bg-white p-4 shadow-card">
      <summary className="cursor-pointer list-none">
        <div className="flex flex-col gap-2">
          <div className="text-sm font-semibold text-axis truncate" title={source.title}>
            {index}. {source.title}
          </div>
          <div className="flex items-center gap-3 text-xs">
            <div className="flex flex-col">
              <span className="text-[10px] uppercase text-axis-ink/60">Relevancy</span>
              <span className={'rounded-full px-2 py-0.5 text-[11px] font-semibold ' + relevancyClass(source.relevancy)}>
                {source.relevancy}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] uppercase text-axis-ink/60">Type</span>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-700">
                {source.type}
              </span>
            </div>
          </div>
          <span className="text-xs font-medium text-axis underline-offset-2 group-open:hidden">
            Show Content
          </span>
          <span className="hidden text-xs font-medium text-axis underline-offset-2 group-open:inline">
            Hide Content
          </span>
        </div>
      </summary>
      <div className="mt-3 whitespace-pre-wrap rounded-lg bg-axis-soft/40 p-3 text-xs text-axis-ink/85">
        {source.snippet || '(no preview available)'}
      </div>
      {source.uri && (
        <div className="mt-2 truncate text-[10px] text-axis-ink/60" title={source.uri}>
          {source.uri}
        </div>
      )}
    </details>
  );
}

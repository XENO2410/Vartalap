'use client';

import { KeyboardEvent, useState } from 'react';

type Props = {
  onSubmit: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
};

export function QueryInput({ onSubmit, disabled, placeholder }: Props) {
  const [value, setValue] = useState('');

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue('');
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex w-full items-center gap-2 rounded-full border-2 border-axis/40 bg-white px-4 py-2 shadow-card focus-within:border-axis">
      <textarea
        rows={1}
        value={value}
        disabled={disabled}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder={placeholder ?? 'Ask a query with relevant product and customer segment.'}
        className="min-h-[36px] w-full resize-none border-none bg-transparent text-sm text-axis-ink outline-none placeholder:text-axis/50"
      />
      <button
        onClick={submit}
        disabled={disabled}
        aria-label="Send message"
        className={
          'grid h-10 w-10 shrink-0 place-items-center rounded-full transition ' +
          (disabled
            ? 'cursor-not-allowed bg-axis/30 text-white/60'
            : 'bg-axis text-white hover:bg-axis-dark')
        }
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M3 12L21 3L14 21L12 13L3 12Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  );
}

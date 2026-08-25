'use client';

type Props = {
  suggestions: string[];
  onPick: (value: string) => void;
};

export function SuggestionChips({ suggestions, onPick }: Props) {
  if (!suggestions.length) return null;
  return (
    <div className="mt-3 rounded-2xl bg-axis-soft/60 p-4">
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-axis">
        <span>✨</span> You can try asking:
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="rounded-full border border-axis-softer bg-white px-3 py-1 text-xs text-axis-ink hover:border-axis/40"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

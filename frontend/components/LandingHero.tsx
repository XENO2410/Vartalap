export function LandingHero() {
  return (
    <div className="mt-8 grid gap-6 sm:mt-14 sm:grid-cols-2 sm:items-center">
      <div className="relative">
        <div className="relative inline-block rounded-3xl bg-white/80 backdrop-blur px-8 py-10 shadow-frost ring-1 ring-axis/10">
          <span className="absolute -left-3 top-6 text-5xl text-axis">❄</span>
          <div className="flex flex-col items-start gap-1">
            <span className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-axis-bright to-axis text-white shadow-frost">
              <span className="deva text-2xl font-bold">वा</span>
            </span>
            <p className="deva mt-3 text-3xl font-bold text-axis">वार्तालाप &amp; Me.</p>
            <p className="text-sm text-axis-ink/70">Snowflakes, sparkle and steady answers.</p>
          </div>
          <span className="absolute -bottom-4 right-8 text-5xl text-axis-bright">❅</span>
        </div>
      </div>
      <div className="grid gap-4">
        <InfoTile
          emoji="❄️"
          title="What&apos;s new?"
          subtitle="Latest updates &amp; features."
        />
        <InfoTile
          emoji="✨"
          title="Did you know?"
          subtitle="Trending questions this week."
        />
        <InfoTile
          emoji="🧭"
          title="Product Info"
          subtitle="Discover what वार्तालाप can do for you."
        />
      </div>
    </div>
  );
}

function InfoTile({ emoji, title, subtitle }: { emoji: string; title: string; subtitle: string }) {
  return (
    <button
      type="button"
      className="flex items-center gap-4 rounded-2xl border border-axis-softer bg-white px-5 py-4 text-left shadow-card transition hover:border-axis/40"
    >
      <span className="grid h-12 w-12 place-items-center rounded-xl bg-axis-softer text-2xl">
        {emoji}
      </span>
      <div className="flex flex-col">
        <span
          className="text-sm font-semibold text-axis"
          dangerouslySetInnerHTML={{ __html: title }}
        />
        <span
          className="text-xs text-axis-ink/70"
          dangerouslySetInnerHTML={{ __html: subtitle }}
        />
      </div>
    </button>
  );
}

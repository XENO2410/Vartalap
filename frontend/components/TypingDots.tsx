export function TypingDots() {
  return (
    <div className="flex items-center gap-1">
      <span className="h-2 w-2 animate-pulseDot rounded-full bg-axis" style={{ animationDelay: '0s' }} />
      <span className="h-2 w-2 animate-pulseDot rounded-full bg-axis" style={{ animationDelay: '0.15s' }} />
      <span className="h-2 w-2 animate-pulseDot rounded-full bg-axis" style={{ animationDelay: '0.3s' }} />
    </div>
  );
}

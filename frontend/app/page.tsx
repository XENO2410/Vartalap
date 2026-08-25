import { ChatWindow } from '@/components/ChatWindow';
import { Snowfall } from '@/components/Snowfall';

export default function HomePage() {
  return (
    <main className="relative min-h-screen">
      <Snowfall />
      <div className="relative z-10">
        <ChatWindow />
        <footer className="mt-8 pb-8 text-center text-[11px] text-axis-ink/50">
          वार्तालाप · Snow Edition · not a production system
        </footer>
      </div>
    </main>
  );
}

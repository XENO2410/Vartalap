import { ChatWindow } from '@/components/ChatWindow';

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <ChatWindow />
      <footer className="mt-8 pb-8 text-center text-[11px] text-axis-ink/50">
        वार्तालाप · dummy assistant for observability testing · not a production system
      </footer>
    </main>
  );
}

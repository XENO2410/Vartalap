import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'वार्तालाप · Snow Edition',
  description:
    'वार्तालाप (Vartalaap) — a RAG-based conversational assistant built to mirror the ADI architecture, wired for MLflow observability, dressed in a snow-themed UI.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'वार्तालाप · Deep Intelligence Assistant',
  description:
    'वार्तालाप (Vartalaap) — a RAG-based conversational assistant built to mirror the ADI architecture, ready for MLflow and Kytee observability.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

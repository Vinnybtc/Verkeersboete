import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Verkeersboete AI Agent",
  description:
    "Upload uw verkeersboete en ontvang automatisch een juridisch bezwaarschrift.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="nl">
      <body className="min-h-screen">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-5xl mx-auto px-4 py-4">
            <h1 className="text-xl font-bold text-brand-700">
              Verkeersboete AI Agent
            </h1>
            <p className="text-sm text-gray-500">
              Automatisch bezwaar maken tegen verkeersboetes
            </p>
          </div>
        </header>
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
        <footer className="border-t border-gray-200 mt-12">
          <div className="max-w-5xl mx-auto px-4 py-4 text-sm text-gray-400">
            Dit is een hulpmiddel en geen vervanging voor juridisch advies.
          </div>
        </footer>
      </body>
    </html>
  );
}

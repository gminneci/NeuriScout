import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "./components/AuthProvider";
import { BookmarksProvider } from "@/contexts/BookmarksContext";

export const metadata: Metadata = {
  title: "NeuriScout: navigate Neurips 2025",
  description: "Search and analyze NeurIPS 2025 research papers using semantic search and LLM-powered insights",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className="antialiased"
        style={{ fontFamily: "'Bond', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}
      >
        <AuthProvider>
          <BookmarksProvider>
            {children}
          </BookmarksProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

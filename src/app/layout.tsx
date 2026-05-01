import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Mock Interview Agent",
  description: "Strict, agent-driven mock interviews for system design and ML system design.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg text-text">{children}</body>
    </html>
  );
}

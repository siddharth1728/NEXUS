import type { Metadata } from "next";
import "./globals.css";
import { Shell } from "@/components/layout/Shell";

export const metadata: Metadata = {
  title: "NEXUS | Context-to-Action Engine",
  description: "NEXUS Engine Interface",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased text-sm h-screen overflow-hidden flex bg-background text-text">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}

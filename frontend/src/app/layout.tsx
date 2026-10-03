import type { Metadata } from "next";
import "./globals.css";
import { Shell } from "@/components/layout/Shell";
import { QueryProvider } from "@/components/shared/QueryProvider";

export const metadata: Metadata = {
  title: "NEXUS | Context-to-Action Engine",
  description: "Enterprise Autonomous Context-to-Action Engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased text-sm h-screen overflow-hidden flex bg-[#F7F7F5] text-[#171717]">
        <QueryProvider>
          <Shell>{children}</Shell>
        </QueryProvider>
      </body>
    </html>
  );
}

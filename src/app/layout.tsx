import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { AuthProvider } from "@/components/auth/AuthProvider";

const interSans = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Parlez — Learn French with AI",
  description: "A free, voice-powered French learning app. Complete A1–B2 courses, AI tutor conversations, and TEF/TCF mock tests.",
  keywords: ["French", "learn French", "language learning", "TEF", "TCF", "A1", "A2", "B1", "B2", "AI tutor", "CEFR"],
  authors: [{ name: "Parlez" }],
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%237C2D3F'/%3E%3Ctext x='50' y='68' font-size='58' font-family='Georgia,serif' fill='%23C19A4B' text-anchor='middle' font-style='italic'%3EP%3C/text%3E%3C/svg%3E",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${interSans.variable} ${playfair.variable} antialiased bg-background text-foreground`}
      >
        <AuthProvider>
          {children}
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  );
}

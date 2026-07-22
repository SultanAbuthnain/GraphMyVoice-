import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Voice → Mindmap",
  description: "حوّل تسجيلاتك الصوتية إلى خريطة ذهنية تفاعلية مع نوتس ومهام.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body className="min-h-screen font-sans antialiased">{children}</body>
    </html>
  );
}

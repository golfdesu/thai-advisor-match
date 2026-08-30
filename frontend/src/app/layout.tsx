import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Thai EduCenter & Advisor Match | ระบบค้นหาหลักสูตรและจับคู่อาจารย์ที่ปรึกษา AI",
  description: "แพลตฟอร์มค้นหาหลักสูตรการศึกษาและจับคู่อาจารย์ที่ปรึกษาวิทยานิพนธ์ด้วย AI สำหรับนักศึกษา ป.ตรี ป.โท ป.เอก ทั่วประเทศไทย",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="th"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var saved = localStorage.getItem('theme') || localStorage.getItem('theme_color');
                  var theme = (saved === 'crimson' || saved === 'sunrise') ? 'crimson' : 'navy';
                  document.documentElement.setAttribute('data-theme', theme);
                  document.documentElement.classList.remove('dark');
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

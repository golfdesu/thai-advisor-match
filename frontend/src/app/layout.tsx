import type { Metadata } from "next";
import { Sarabun, Geist_Mono } from "next/font/google";
import "./globals.css";

const sarabun = Sarabun({
  variable: "--font-sarabun",
  subsets: ["thai", "latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Thai EduCenter & Advisor Match | ระบบค้นหาหลักสูตรและจับคู่อาจารย์ที่ปรึกษา AI",
  description: "แพลตฟอร์มค้นหาหลักสูตรการศึกษาและจับคู่อาจารย์ที่ปรึกษาวิทยานิพนธ์ด้วย AI สำหรับนักศึกษา ป.ตรี ป.โท ป.เอก ทั่วประเทศไทย",
  other: {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="th"
      suppressHydrationWarning
      className={`${sarabun.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var savedTheme = localStorage.getItem('theme') || localStorage.getItem('theme_color') || 'navy';
                  if (savedTheme === 'sunrise') savedTheme = 'crimson';
                  if (savedTheme === 'green') savedTheme = 'emerald';
                  if (savedTheme === 'purple') savedTheme = 'amethyst';
                  if (savedTheme === 'orange') savedTheme = 'amber';
                  if (savedTheme === 'dark' || savedTheme === 'midnight') savedTheme = 'navy';

                  var savedMode = localStorage.getItem('theme_mode');
                  var isDark = savedMode === 'dark' || (!savedMode && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);

                  document.documentElement.setAttribute('data-theme', savedTheme);
                  if (isDark) {
                    document.documentElement.classList.add('dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                  }
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

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { GraduationCap, Compass, Bookmark } from "lucide-react";

export type ThemeName = "navy" | "crimson";

interface HeaderProps {
  savedCount: number;
  onOpenSavedModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({ savedCount, onOpenSavedModal }) => {
  const [currentTheme, setCurrentTheme] = useState<ThemeName>("navy");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = (localStorage.getItem("theme") || localStorage.getItem("theme_color")) as string | null;
    const initialTheme: ThemeName = (saved === "crimson" || saved === "sunrise" || saved === "dark") ? "crimson" : "navy";
    setCurrentTheme(initialTheme);
    applyTheme(initialTheme);
  }, []);

  const applyTheme = (theme: ThemeName) => {
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.classList.remove("dark");
  };

  const toggleTheme = () => {
    const nextTheme: ThemeName = currentTheme === "navy" ? "crimson" : "navy";
    setCurrentTheme(nextTheme);
    localStorage.setItem("theme", nextTheme);
    applyTheme(nextTheme);
  };

  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-[var(--theme-card)]/90 border-b border-[var(--theme-border)] px-4 sm:px-6 lg:px-12 py-3 flex items-center justify-between transition-colors shadow-2xs">
      {/* Brand Identity */}
      <Link href="/" className="flex items-center gap-3 group">
        <div className="w-10 h-10 rounded-xl bg-[var(--theme-primary)] flex items-center justify-center text-[var(--theme-primary-contrast)] shadow-sm group-hover:scale-105 transition-all">
          <GraduationCap className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-lg tracking-tight text-[var(--theme-primary)] transition-colors">
              Thai EduCenter
            </span>
            <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] border border-[var(--theme-accent-border)] transition-colors">
              Academic Directory
            </span>
          </div>
          <p className="text-[11px] text-[var(--theme-text-muted)] hidden sm:block">
            ระบบค้นหาหลักสูตรและอาจารย์ที่ปรึกษางานวิจัยระดับประเทศ
          </p>
        </div>
      </Link>

      {/* Navigation & Theme Toggle */}
      <nav className="flex items-center gap-2 sm:gap-3">
        <Link
          href="/career-discovery"
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[var(--theme-card-subtle)] hover:bg-[var(--theme-card)] text-xs font-semibold text-[var(--theme-text-body)] border border-[var(--theme-border)] transition-all hover:border-[var(--theme-primary)] shadow-2xs"
        >
          <Compass className="w-4 h-4 text-[var(--theme-primary)]" />
          <span className="hidden sm:inline">แบบประเมินค้นหาตนเอง</span>
          <span className="sm:hidden">แบบประเมิน</span>
        </Link>

        <button
          onClick={onOpenSavedModal}
          className="relative flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[var(--theme-card-subtle)] hover:bg-[var(--theme-card)] text-xs font-semibold text-[var(--theme-text-body)] border border-[var(--theme-border)] transition-all hover:border-[var(--theme-accent)] shadow-2xs cursor-pointer"
          title="รายการที่บันทึก"
        >
          <Bookmark className="w-4 h-4 text-[var(--theme-accent)]" />
          <span className="hidden sm:inline">บันทึกไว้</span>
          {savedCount > 0 && (
            <span className="w-5 h-5 rounded-full bg-[var(--theme-accent)] text-[var(--theme-accent-contrast)] text-[10px] font-bold flex items-center justify-center shadow-xs">
              {savedCount}
            </span>
          )}
        </button>

        {/* Single Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[var(--theme-card-subtle)] hover:bg-[var(--theme-card)] border border-[var(--theme-border)] text-xs font-bold transition-all shadow-2xs hover:border-[var(--theme-primary)] group cursor-pointer"
          title={
            mounted && currentTheme === "crimson"
              ? "สลับเป็นธีม 🔵 Oxford Navy & Beige"
              : "สลับเป็นธีม 🔴 Harvard Crimson & Ivory"
          }
          aria-label="Toggle Theme"
        >
          {mounted && currentTheme === "crimson" ? (
            <>
              <span className="w-2.5 h-2.5 rounded-full bg-[#4E0000] border border-[#4E0000]/40 inline-block shadow-xs" />
              <span className="text-[var(--theme-text-title)] hidden sm:inline">Crimson &amp; Ivory</span>
            </>
          ) : (
            <>
              <span className="w-2.5 h-2.5 rounded-full bg-[#001D51] border border-[#001D51]/40 inline-block shadow-xs" />
              <span className="text-[var(--theme-text-title)] hidden sm:inline">Navy &amp; Beige</span>
            </>
          )}
        </button>
      </nav>
    </header>
  );
};

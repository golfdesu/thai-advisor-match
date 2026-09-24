"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Bookmark, GraduationCap, Moon, Sun } from "lucide-react";

export type ModeName = "light" | "dark";

function readStoredDarkMode(): boolean {
  if (typeof window === "undefined") return true;
  const savedMode = window.localStorage.getItem("theme_mode");
  return savedMode ? savedMode === "dark" : true;
}

function applyDarkMode(isDark: boolean) {
  document.documentElement.classList.toggle("dark", isDark);
}

interface HeaderProps {
  savedCount: number;
  onOpenSavedModal: () => void;
  onSelectTab?: (tab: "courses" | "advisors" | "labs") => void;
}

export const Header: React.FC<HeaderProps> = ({ savedCount, onOpenSavedModal, onSelectTab }) => {
  const [, setMounted] = useState(false);
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const initialDark = readStoredDarkMode();
      setMounted(true);
      setIsDark(initialDark);
      applyDarkMode(initialDark);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const handleToggleMode = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    applyDarkMode(nextDark);
    window.localStorage.setItem("theme_mode", nextDark ? "dark" : "light");
  };

  return (
    <header className="site-header sticky top-0 z-40 border-b border-[var(--theme-border)]">
      <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-3" aria-label="Thai EduCenter หน้าหลัก">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)]">
            <GraduationCap className="h-5 w-5" aria-hidden="true" />
          </span>
          <span className="hidden text-sm font-bold tracking-tight text-[var(--theme-text-title)] sm:block">Thai EduCenter</span>
          <span className="text-sm font-bold text-[var(--theme-primary)] sm:hidden">TE</span>
        </Link>
        <nav className="hidden items-center gap-1 md:flex" aria-label="เมนูหลัก">
          <Link
            href="/#search-results"
            onClick={() => onSelectTab?.("courses")}
            className="nav-link"
          >
            หลักสูตร
          </Link>
          <Link
            href="/?tab=advisors#search-results"
            onClick={() => onSelectTab?.("advisors")}
            className="nav-link"
          >
            อาจารย์ที่ปรึกษา
          </Link>
          <Link
            href="/?tab=labs#search-results"
            onClick={() => onSelectTab?.("labs")}
            className="nav-link"
          >
            ห้องวิจัย
          </Link>
          <Link href="/career-discovery" className="nav-link">ค้นหาตนเอง</Link>
        </nav>
        <div className="flex items-center gap-1.5 sm:gap-2">
          <button
            type="button"
            onClick={onOpenSavedModal}
            aria-label={`รายการที่บันทึกไว้${savedCount ? ` (${savedCount} รายการ)` : ""}`}
            className="header-control"
          >
            <Bookmark className="h-4 w-4 text-[var(--theme-primary)]" aria-hidden="true" />
            <span className="hidden lg:inline">บันทึกไว้</span>
            {savedCount > 0 && <span className="count-badge">{savedCount}</span>}
          </button>
          <button
            type="button"
            onClick={handleToggleMode}
            aria-label={isDark ? "สลับเป็นโหมดสว่าง" : "สลับเป็นโหมดมืด"}
            className="header-icon-control"
          >
            {isDark ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>
      </div>
    </header>
  );
};

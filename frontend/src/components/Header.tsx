"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bookmark, Check, ChevronDown, GraduationCap, Moon, Palette, Sun } from "lucide-react";

export type ThemeName = "coral";
export type ModeName = "light" | "dark";

const THEMES = [{
  id: "coral" as const,
  name: "คอรัล ออเรนจ์",
  nameEn: "Coral Orange",
  primaryColor: "#FF7A59",
  darkPrimaryColor: "#FF967A",
}];

function readStoredDarkMode() {
  if (typeof window === "undefined") return true;
  const savedMode = window.localStorage.getItem("theme_mode");
  return savedMode ? savedMode === "dark" : true;
}

function applyMode(isDark: boolean) {
  document.documentElement.setAttribute("data-theme", "coral");
  document.documentElement.classList.toggle("dark", isDark);
}

interface HeaderProps {
  savedCount: number;
  onOpenSavedModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({ savedCount, onOpenSavedModal }) => {
  const [mounted, setMounted] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const paletteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const initialDark = readStoredDarkMode();
      setMounted(true);
      setIsDark(initialDark);
      applyMode(initialDark);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    applyMode(isDark);
    window.localStorage.setItem("theme_mode", isDark ? "dark" : "light");
  }, [isDark, mounted]);

  useEffect(() => {
    const closePalette = (event: MouseEvent) => {
      if (paletteRef.current && !paletteRef.current.contains(event.target as Node)) setIsPaletteOpen(false);
    };
    document.addEventListener("mousedown", closePalette);
    return () => document.removeEventListener("mousedown", closePalette);
  }, []);

  return (
    <header className="site-header sticky top-0 z-40 border-b border-[var(--theme-border)]">
      <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-3" aria-label="Thai EduCenter หน้าหลัก">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)]"><GraduationCap className="h-5 w-5" aria-hidden="true" /></span>
          <span className="hidden text-sm font-bold tracking-tight text-[var(--theme-text-title)] sm:block">Thai EduCenter</span>
          <span className="text-sm font-bold text-[var(--theme-primary)] sm:hidden">TE</span>
        </Link>
        <nav className="hidden items-center gap-1 md:flex" aria-label="เมนูหลัก">
          <Link href="/#search-results" className="nav-link">หลักสูตร</Link>
          <Link href="/?tab=advisors#search-results" className="nav-link">อาจารย์ที่ปรึกษา</Link>
          <Link href="/?tab=labs#search-results" className="nav-link">ห้องวิจัย</Link>
          <Link href="/career-discovery" className="nav-link">ค้นหาตนเอง</Link>
        </nav>
        <div className="flex items-center gap-1.5 sm:gap-2">
          <button type="button" onClick={onOpenSavedModal} aria-label={`รายการที่บันทึกไว้${savedCount ? ` (${savedCount} รายการ)` : ""}`} className="header-control"><Bookmark className="h-4 w-4 text-[var(--theme-primary)]" aria-hidden="true" /><span className="hidden lg:inline">บันทึกไว้</span>{savedCount > 0 && <span className="count-badge">{savedCount}</span>}</button>
          <div className="relative" ref={paletteRef}>
            <button type="button" onClick={() => setIsPaletteOpen((open) => !open)} aria-label="เลือกโทนสี" aria-expanded={isPaletteOpen} className="header-control"><Palette className="h-4 w-4 text-[var(--theme-primary)]" aria-hidden="true" /><span className="hidden xl:inline">Coral Orange</span><ChevronDown className={`h-3.5 w-3.5 transition-transform ${isPaletteOpen ? "rotate-180" : ""}`} aria-hidden="true" /></button>
            {isPaletteOpen && <div className="absolute right-0 top-12 z-50 w-56 border border-[var(--theme-border)] bg-[var(--theme-card)] p-2 shadow-2xl" role="menu"><div className="border-b border-[var(--theme-border)] px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-[var(--theme-text-muted)]">Color palette</div>{THEMES.map((theme) => <button key={theme.id} type="button" role="menuitem" onClick={() => setIsPaletteOpen(false)} className="flex w-full items-center justify-between px-3 py-3 text-left hover:bg-[var(--theme-card-subtle)]"><span className="flex items-center gap-3"><span className="h-4 w-4 rounded-full" style={{ backgroundColor: isDark ? theme.darkPrimaryColor : theme.primaryColor }} /><span><strong className="block text-sm text-[var(--theme-text-title)]">{theme.nameEn}</strong><small className="text-xs text-[var(--theme-text-muted)]">{theme.name}</small></span></span><Check className="h-4 w-4 text-[var(--theme-primary)]" aria-hidden="true" /></button>)}</div>}
          </div>
          <button type="button" onClick={() => setIsDark((value) => !value)} aria-label={isDark ? "สลับเป็นโหมดสว่าง" : "สลับเป็นโหมดมืด"} className="header-icon-control">{isDark ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}</button>
        </div>
      </div>
    </header>
  );
};

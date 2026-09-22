"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bookmark, Check, ChevronDown, GraduationCap, Moon, Palette, Sun } from "lucide-react";

export type ThemeName = "coral" | "peach" | "lavender" | "sage" | "sky" | "blush" | "matcha";
export type ModeName = "light" | "dark";

export const THEMES = [
  {
    id: "coral" as const,
    name: "คอรัล ออเรนจ์ (คลาสสิก)",
    nameEn: "Coral Orange",
    primaryColor: "#E05638",
    darkPrimaryColor: "#FF7A59",
  },
  {
    id: "peach" as const,
    name: "พีช พาสเทล",
    nameEn: "Pastel Peach",
    primaryColor: "#D96B43",
    darkPrimaryColor: "#FFB088",
  },
  {
    id: "lavender" as const,
    name: "ลาเวนเดอร์ พาสเทล",
    nameEn: "Pastel Lavender",
    primaryColor: "#7C5CBF",
    darkPrimaryColor: "#C4B5FD",
  },
  {
    id: "sage" as const,
    name: "เซจ มินต์ พาสเทล",
    nameEn: "Pastel Sage Mint",
    primaryColor: "#2E8B73",
    darkPrimaryColor: "#86EFAC",
  },
  {
    id: "sky" as const,
    name: "สกาย บลู พาสเทล",
    nameEn: "Pastel Sky",
    primaryColor: "#2B70C9",
    darkPrimaryColor: "#93C5FD",
  },
  {
    id: "blush" as const,
    name: "บลัช โรส พาสเทล",
    nameEn: "Pastel Blush",
    primaryColor: "#C44569",
    darkPrimaryColor: "#F472B6",
  },
  {
    id: "matcha" as const,
    name: "มัทฉะ พาสเทล",
    nameEn: "Pastel Matcha",
    primaryColor: "#5B8A28",
    darkPrimaryColor: "#BEF264",
  },
];

const VALID_THEME_IDS: ThemeName[] = ["coral", "peach", "lavender", "sage", "sky", "blush", "matcha"];

function readStoredTheme(): ThemeName {
  if (typeof window === "undefined") return "coral";
  const saved = window.localStorage.getItem("theme_name") as ThemeName;
  if (saved && VALID_THEME_IDS.includes(saved)) {
    return saved;
  }
  return "coral";
}

function readStoredDarkMode(): boolean {
  if (typeof window === "undefined") return true;
  const savedMode = window.localStorage.getItem("theme_mode");
  return savedMode ? savedMode === "dark" : true;
}

function applyThemeAndMode(theme: ThemeName, isDark: boolean) {
  document.documentElement.setAttribute("data-theme", theme);
  document.documentElement.classList.toggle("dark", isDark);
}

interface HeaderProps {
  savedCount: number;
  onOpenSavedModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({ savedCount, onOpenSavedModal }) => {
  const [, setMounted] = useState(false);
  const [currentTheme, setCurrentTheme] = useState<ThemeName>("coral");
  const [isDark, setIsDark] = useState(true);
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const paletteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const initialDark = readStoredDarkMode();
      const initialTheme = readStoredTheme();
      setMounted(true);
      setIsDark(initialDark);
      setCurrentTheme(initialTheme);
      applyThemeAndMode(initialTheme, initialDark);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const handleSelectTheme = (themeId: ThemeName) => {
    setCurrentTheme(themeId);
    applyThemeAndMode(themeId, isDark);
    window.localStorage.setItem("theme_name", themeId);
    setIsPaletteOpen(false);
  };

  const handleToggleMode = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    applyThemeAndMode(currentTheme, nextDark);
    window.localStorage.setItem("theme_mode", nextDark ? "dark" : "light");
  };

  useEffect(() => {
    const closePalette = (event: MouseEvent) => {
      if (paletteRef.current && !paletteRef.current.contains(event.target as Node)) setIsPaletteOpen(false);
    };
    document.addEventListener("mousedown", closePalette);
    return () => document.removeEventListener("mousedown", closePalette);
  }, []);

  const activeTheme = THEMES.find((t) => t.id === currentTheme) || THEMES[0];

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
            <button type="button" onClick={() => setIsPaletteOpen((open) => !open)} aria-label="เลือกโทนสี" aria-expanded={isPaletteOpen} className="header-control">
              <Palette className="h-4 w-4 text-[var(--theme-primary)]" aria-hidden="true" />
              <span className="hidden xl:inline">{activeTheme.nameEn}</span>
              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${isPaletteOpen ? "rotate-180" : ""}`} aria-hidden="true" />
            </button>
            {isPaletteOpen && (
              <div className="absolute right-0 top-12 z-50 w-64 rounded-xl border border-[var(--theme-border)] bg-[var(--theme-card)] p-2 shadow-2xl animate-in fade-in zoom-in-95 duration-100" role="menu">
                <div className="border-b border-[var(--theme-border)] px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-[var(--theme-text-muted)]">
                  Color palette
                </div>
                <div className="space-y-0.5 pt-1">
                  {THEMES.map((theme) => {
                    const isSelected = theme.id === currentTheme;
                    return (
                      <button
                        key={theme.id}
                        type="button"
                        role="menuitem"
                        onClick={() => handleSelectTheme(theme.id)}
                        className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left transition-colors cursor-pointer ${
                          isSelected ? "bg-[var(--theme-card-subtle)] font-bold" : "hover:bg-[var(--theme-card-subtle)]"
                        }`}
                      >
                        <span className="flex items-center gap-3 min-w-0">
                          <span
                            className="h-4 w-4 rounded-full shrink-0 shadow-2xs border border-white/20"
                            style={{ backgroundColor: isDark ? theme.darkPrimaryColor : theme.primaryColor }}
                          />
                          <span className="min-w-0 truncate">
                            <strong className="block text-xs text-[var(--theme-text-title)] leading-tight truncate">
                              {theme.nameEn}
                            </strong>
                            <small className="text-[11px] text-[var(--theme-text-muted)] font-normal block leading-tight truncate">
                              {theme.name}
                            </small>
                          </span>
                        </span>
                        {isSelected && <Check className="h-4 w-4 text-[var(--theme-primary)] shrink-0" aria-hidden="true" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
          <button type="button" onClick={handleToggleMode} aria-label={isDark ? "สลับเป็นโหมดสว่าง" : "สลับเป็นโหมดมืด"} className="header-icon-control">
            {isDark ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>
      </div>
    </header>
  );
};

"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { GraduationCap, Compass, Bookmark, Waves, Flame, Trees, Sparkles, Sun, Moon, ChevronDown, Check, Palette } from "lucide-react";

export type ThemeName = "navy" | "crimson" | "emerald" | "amethyst" | "amber";
export type ModeName = "light" | "dark";

interface ThemeOption {
  id: ThemeName;
  name: string;
  nameEn: string;
  primaryColor: string;
  darkPrimaryColor: string;
  icon: React.ComponentType<{ className?: string }>;
}

const THEMES: ThemeOption[] = [
  {
    id: "navy",
    name: "น้ำเงิน โอเชี่ยน",
    nameEn: "Ocean Navy",
    primaryColor: "#0A3C74",
    darkPrimaryColor: "#388BFD",
    icon: Waves,
  },
  {
    id: "crimson",
    name: "แดง เอมเบอร์",
    nameEn: "Ember Crimson",
    primaryColor: "#8E0024",
    darkPrimaryColor: "#FF4A55",
    icon: Flame,
  },
  {
    id: "emerald",
    name: "เขียว ฟอเรสต์",
    nameEn: "Forest Emerald",
    primaryColor: "#065F46",
    darkPrimaryColor: "#34D399",
    icon: Trees,
  },
  {
    id: "amethyst",
    name: "ม่วง อเมทิสต์",
    nameEn: "Royal Amethyst",
    primaryColor: "#521C9D",
    darkPrimaryColor: "#A78BFA",
    icon: Sparkles,
  },
  {
    id: "amber",
    name: "ส้ม ซันเซ็ต",
    nameEn: "Sunset Amber",
    primaryColor: "#A23A13",
    darkPrimaryColor: "#FB923C",
    icon: Sun,
  },
];

function readStoredTheme(): ThemeName {
  if (typeof window === "undefined") return "navy";
  const saved = window.localStorage.getItem("theme") || window.localStorage.getItem("theme_color");
  if (saved === "crimson" || saved === "sunrise") return "crimson";
  if (saved === "emerald" || saved === "green") return "emerald";
  if (saved === "amethyst" || saved === "purple") return "amethyst";
  if (saved === "amber" || saved === "orange") return "amber";
  return "navy";
}

function readStoredDarkMode(): boolean {
  if (typeof window === "undefined") return false;
  const saved = window.localStorage.getItem("theme") || window.localStorage.getItem("theme_color");
  const savedMode = window.localStorage.getItem("theme_mode");
  const systemPrefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  return savedMode ? savedMode === "dark" : (saved === "dark" || saved === "midnight" || systemPrefersDark);
}

function applyThemeAndMode(theme: ThemeName, dark: boolean) {
  document.documentElement.setAttribute("data-theme", theme);
  document.documentElement.classList.toggle("dark", dark);
}

interface HeaderProps {
  savedCount: number;
  onOpenSavedModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({ savedCount, onOpenSavedModal }) => {
  const [mounted, setMounted] = useState(false);
  const [currentTheme, setCurrentTheme] = useState<ThemeName>("navy"); // Default for server render
  const [isDark, setIsDark] = useState<boolean>(false); // Default for server render
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setMounted(true);
      const initialTheme = readStoredTheme();
      const initialDark = readStoredDarkMode();
      setCurrentTheme(initialTheme);
      setIsDark(initialDark);
      applyThemeAndMode(initialTheme, initialDark);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    applyThemeAndMode(currentTheme, isDark);
  }, [currentTheme, isDark, mounted]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectTheme = (theme: ThemeName) => {
    setCurrentTheme(theme);
    localStorage.setItem("theme", theme);
    applyThemeAndMode(theme, isDark);
  };

  const toggleDarkMode = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    localStorage.setItem("theme_mode", nextDark ? "dark" : "light");
    applyThemeAndMode(currentTheme, nextDark);
  };

  const activeThemeOption = THEMES.find((t) => t.id === currentTheme) || THEMES[0];
  const ActiveIcon = activeThemeOption.icon;

  return (
    <header className="site-header sticky top-0 z-40 border-b border-[var(--theme-border)] px-4 py-3 sm:px-6 lg:px-12">
      <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-4">
      {/* Brand Identity */}
      <Link href="/" className="group flex min-w-0 items-center gap-3.5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] transition-transform duration-200 group-hover:scale-[1.03]">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="hidden truncate text-lg font-extrabold tracking-tight text-[var(--theme-primary)] transition-colors sm:inline sm:text-xl">
              Thai EduCenter
            </span>
            <span className="text-lg font-extrabold tracking-tight text-[var(--theme-primary)] sm:hidden">TE</span>
            <span className="hidden rounded-full border border-[var(--theme-accent-border)] bg-[var(--theme-accent-subtle)] px-2 py-0.5 text-[10px] font-bold tracking-[0.12em] text-[var(--theme-accent)] transition-colors sm:inline-flex">
              Academic Hub
            </span>
          </div>
          <p className="mt-0.5 hidden truncate text-xs font-medium text-[var(--theme-text-muted)] sm:block">
            ศูนย์รวมหลักสูตรและทำเนียบคณาจารย์ที่ปรึกษางานวิจัยระดับประเทศ
          </p>
        </div>
      </Link>

      {/* Navigation & Theme Controls */}
      <nav className="flex shrink-0 items-center gap-1.5 sm:gap-2.5">
        <Link
          href="/career-discovery"
          className="group flex items-center gap-2 rounded-lg border border-transparent px-2.5 py-2 text-xs font-bold text-[var(--theme-text-body)] transition-colors hover:border-[var(--theme-border)] hover:bg-[var(--theme-card-subtle)] hover:text-[var(--theme-primary)] sm:px-3 sm:text-sm"
        >
          <Compass className="w-4 h-4 text-[var(--theme-primary)] group-hover:rotate-45 transition-transform" />
          <span className="hidden sm:inline">ค้นหาตนเอง (RIASEC)</span>
          <span className="sm:hidden">ค้นหาตนเอง</span>
        </Link>

        <button
          onClick={onOpenSavedModal}
          className="relative flex items-center gap-2 rounded-lg border border-transparent px-2.5 py-2 text-xs font-bold text-[var(--theme-text-body)] transition-colors hover:border-[var(--theme-border)] hover:bg-[var(--theme-card-subtle)] hover:text-[var(--theme-accent)] sm:px-3 sm:text-sm"
          title="รายการที่บันทึกไว้"
        >
          <Bookmark className="w-4 h-4 text-[var(--theme-accent)]" />
          <span className="hidden sm:inline">บันทึกไว้</span>
          {savedCount > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--theme-accent)] text-xs font-black text-[var(--theme-accent-contrast)]">
              {savedCount}
            </span>
          )}
        </button>

        {/* 5-Color Theme Dropdown Selector */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="group flex shrink-0 items-center gap-2 rounded-lg border border-[var(--theme-border)] bg-[var(--theme-card-subtle)] px-2.5 py-2 text-xs font-bold text-[var(--theme-text-body)] transition-colors hover:border-[var(--theme-primary)] hover:bg-[var(--theme-card)] sm:px-3 sm:text-sm"
            aria-label="Select Color Theme"
            aria-expanded={isDropdownOpen}
          >
            <div
              className="w-4 h-4 rounded-full flex items-center justify-center shadow-2xs shrink-0 transition-transform group-hover:scale-110"
              style={{ backgroundColor: isDark ? activeThemeOption.darkPrimaryColor : activeThemeOption.primaryColor }}
            >
              <ActiveIcon className="w-2.5 h-2.5 text-white" />
            </div>
            <span className="hidden md:inline font-bold">{activeThemeOption.nameEn}</span>
            <ChevronDown
              className={`w-4 h-4 text-[var(--theme-text-muted)] transition-transform duration-200 ${
                isDropdownOpen ? "rotate-180 text-[var(--theme-primary)]" : ""
              }`}
            />
          </button>

          {/* Dropdown Menu Modal */}
          {isDropdownOpen && (
            <div className="absolute right-0 z-50 mt-2 w-64 rounded-xl border border-[var(--theme-border)] bg-[var(--theme-card)] p-2.5 shadow-xl animate-in fade-in zoom-in-95 duration-150">
              <div className="px-3 py-2 border-b border-[var(--theme-border-subtle)] mb-1.5 flex items-center justify-between text-xs font-black text-[var(--theme-text-muted)]">
                <div className="flex items-center gap-2">
                  <Palette className="w-4 h-4 text-[var(--theme-primary)]" />
                  <span>เลือกโทนสี (Color Palette)</span>
                </div>
              </div>
              <div className="space-y-1">
                {THEMES.map((theme) => {
                  const IconComponent = theme.icon;
                  const isSelected = currentTheme === theme.id;
                  const themeColor = isDark ? theme.darkPrimaryColor : theme.primaryColor;
                  return (
                    <button
                      key={theme.id}
                      onClick={() => selectTheme(theme.id)}
                      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left transition-all cursor-pointer ${
                        isSelected
                          ? "bg-[var(--theme-primary-subtle)] border border-[var(--theme-primary-border)] text-[var(--theme-primary)] font-black"
                          : "hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-body)] border border-transparent font-semibold"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-5 h-5 rounded-full flex items-center justify-center shadow-xs shrink-0"
                          style={{ backgroundColor: themeColor }}
                        >
                          <IconComponent className="w-3 h-3 text-white" />
                        </div>
                        <div>
                          <div className="text-xs sm:text-sm tracking-tight font-black">{theme.nameEn}</div>
                          <div className="text-xs text-[var(--theme-text-muted)] font-medium">{theme.name}</div>
                        </div>
                      </div>
                      {isSelected && (
                        <Check className="w-4 h-4 text-[var(--theme-primary)] stroke-[2.5]" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Light / Dark Mode Toggle Switch */}
        <button
          onClick={toggleDarkMode}
          className={`flex h-10 w-10 cursor-pointer items-center justify-center rounded-lg border transition-colors ${
            isDark
              ? "bg-[var(--theme-primary-subtle)] border-[var(--theme-primary-border)] text-[var(--theme-primary)] hover:bg-[var(--theme-card-subtle)]"
              : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-body)] hover:border-[var(--theme-primary)] hover:text-[var(--theme-primary)]"
          }`}
          title={isDark ? "สลับเป็นโหมดสว่าง (Light Mode)" : "สลับเป็นโหมดมืด (Dark Mode)"}
          aria-label="Toggle Light / Dark Mode"
        >
          {isDark ? (
            <Sun className="w-4.5 h-4.5 text-[var(--theme-primary)] transition-transform hover:rotate-45" />
          ) : (
            <Moon className="w-4.5 h-4.5 text-[var(--theme-text-muted)] transition-transform hover:-rotate-12" />
          )}
        </button>
      </nav>
      </div>
    </header>
  );
};

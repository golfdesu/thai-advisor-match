"use client";

import React from "react";
import Link from "next/link";
import { GraduationCap, Compass, Bookmark } from "lucide-react";

interface HeaderProps {
  savedCount: number;
  onOpenSavedModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({ savedCount, onOpenSavedModal }) => {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-[#F8F1E7]/95 border-b border-stone-200/80 px-4 sm:px-6 lg:px-12 py-3.5 flex items-center justify-between transition-colors">
      {/* Brand Identity */}
      <Link href="/" className="flex items-center gap-3.5 group">
        <div className="w-10 h-10 rounded-xl bg-[#5B0F18] flex items-center justify-center text-white shadow-sm group-hover:scale-105 transition-transform">
          <GraduationCap className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-lg tracking-tight text-[#5B0F18]">
              Thai EduCenter
            </span>
            <span className="text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-full bg-rose-50 text-[#5B0F18] border border-rose-200">
              Academic Directory
            </span>
          </div>
          <p className="text-[11px] text-stone-500 hidden sm:block">
            ระบบค้นหาหลักสูตรและอาจารย์ที่ปรึกษางานวิจัยระดับประเทศ
          </p>
        </div>
      </Link>

      {/* Navigation Actions */}
      <nav className="flex items-center gap-2.5">
        <Link
          href="/career-discovery"
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white hover:bg-stone-50 text-xs font-semibold text-stone-700 border border-stone-200 transition-all hover:border-[#5B0F18] shadow-2xs"
        >
          <Compass className="w-4 h-4 text-[#5B0F18]" />
          <span className="hidden sm:inline">แบบประเมินค้นหาตนเอง</span>
          <span className="sm:hidden">แบบประเมิน</span>
        </Link>

        <button
          onClick={onOpenSavedModal}
          className="relative flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white hover:bg-stone-50 text-xs font-semibold text-stone-700 border border-stone-200 transition-all hover:border-[#5B0F18] shadow-2xs cursor-pointer"
          title="รายการที่บันทึก"
        >
          <Bookmark className="w-4 h-4 text-[#5B0F18]" />
          <span className="hidden sm:inline">บันทึกไว้</span>
          {savedCount > 0 && (
            <span className="w-5 h-5 rounded-full bg-[#5B0F18] text-white text-[10px] font-bold flex items-center justify-center">
              {savedCount}
            </span>
          )}
        </button>
      </nav>
    </header>
  );
};

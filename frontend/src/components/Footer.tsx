"use client";

import React from "react";
import Link from "next/link";
import { GraduationCap } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-[var(--theme-border)] bg-[var(--theme-card-subtle)] mt-20 text-[var(--theme-text-muted)] text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[var(--theme-primary)] flex items-center justify-center text-[var(--theme-primary-contrast)] shadow-xs">
                <GraduationCap className="w-4 h-4" />
              </div>
              <span className="font-extrabold text-base text-[var(--theme-primary)]">Thai EduCenter</span>
            </div>
            <p className="text-[var(--theme-text-muted)] leading-relaxed max-w-md">
              ศูนย์รวมข้อมูลดัชนีหลักสูตรการศึกษาและทำเนียบคณาจารย์ที่ปรึกษาวิทยานิพนธ์จากมหาวิทยาลัยชั้นนำในประเทศไทย พัฒนาขึ้นเพื่อช่วยให้นักศึกษาค้นพบเส้นทางวิชาการและงานวิจัยที่ตรงเป้าหมายที่สุด
            </p>
          </div>

          <div>
            <h4 className="font-bold text-[var(--theme-text-title)] mb-3 uppercase tracking-wider text-[11px]">บริการระบบ</h4>
            <ul className="space-y-2 text-[var(--theme-text-body)]">
              <li><Link href="/" className="hover:text-[var(--theme-primary)] transition-colors">ค้นหาหลักสูตร (Courses Directory)</Link></li>
              <li><Link href="/?tab=advisors" className="hover:text-[var(--theme-primary)] transition-colors">ค้นหาอาจารย์ที่ปรึกษา (Advisor Directory)</Link></li>
              <li><Link href="/career-discovery" className="hover:text-[var(--theme-primary)] transition-colors">แบบประเมินค้นหาตนเอง (RIASEC Assessment)</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-[var(--theme-text-title)] mb-3 uppercase tracking-wider text-[11px]">การเชื่อมโยงข้อมูล</h4>
            <p className="text-[var(--theme-text-muted)] leading-relaxed">
              ข้อมูลหลักสูตรและคณาจารย์รวบรวมจากแหล่งข้อมูลสาธารณะของแต่ละสถาบันการศึกษา เป็นไปตามมาตรฐานข้อมูลเปิดและสิทธิส่วนบุคคล (PDPA)
            </p>
          </div>
        </div>

        <div className="border-t border-[var(--theme-border)] mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[var(--theme-text-muted)]">
          <p>© {new Date().getFullYear()} Thai EduCenter & Academic Research Matcher. All rights reserved.</p>
          <p className="flex items-center gap-1">
            Built for Thai Higher Education Discovery
          </p>
        </div>
      </div>
    </footer>
  );
};

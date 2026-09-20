"use client";

import React from "react";
import Link from "next/link";
import { GraduationCap } from "lucide-react";

export const Footer: React.FC = () => (
  <footer className="site-footer mt-16 border-t border-[#eaecef] bg-[#fafafa] text-[#181a20]">
    <div className="mx-auto max-w-[1280px] px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
      <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-2">
          <div className="flex items-center gap-2 text-[#181a20]"><span className="flex h-8 w-8 items-center justify-center rounded-md bg-[#ff7a59] text-[#24110c]"><GraduationCap className="h-4 w-4" aria-hidden="true" /></span><strong>Thai EduCenter</strong></div>
          <p className="footer-muted mt-4 max-w-md text-sm leading-6">ฐานข้อมูลหลักสูตร อาจารย์ที่ปรึกษา และห้องวิจัยจากมหาวิทยาลัยในประเทศไทย เพื่อช่วยให้การตัดสินใจทางการศึกษาชัดเจนขึ้น</p>
        </div>
        <div><h2 className="footer-heading">บริการ</h2><ul className="footer-links"><li><Link href="/#search-results">ค้นหาหลักสูตร</Link></li><li><Link href="/?tab=advisors#search-results">ค้นหาอาจารย์</Link></li><li><Link href="/career-discovery">แบบประเมิน RIASEC</Link></li></ul></div>
        <div><h2 className="footer-heading">ข้อมูล</h2><p className="footer-muted text-sm leading-6">ข้อมูลมาจากแหล่งข้อมูลสาธารณะของสถาบันการศึกษา และจัดทำโดยคำนึงถึงมาตรฐานข้อมูลเปิดและ PDPA</p></div>
      </div>
      <div className="footer-muted mt-12 border-t border-[#eaecef] pt-5 text-xs">© {new Date().getFullYear()} Thai EduCenter & Academic Research Matcher.</div>
    </div>
  </footer>
);

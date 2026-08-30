"use client";

import React from "react";
import { Course } from "@/types";
import { Scale, X, ExternalLink } from "lucide-react";

interface ComparisonModalProps {
  isOpen: boolean;
  courses: Course[];
  onClose: () => void;
  onClearAll: () => void;
}

export const ComparisonModal: React.FC<ComparisonModalProps> = ({
  isOpen,
  courses,
  onClose,
  onClearAll,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="bg-[var(--theme-card)] border-2 border-[var(--theme-border)] rounded-3xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden shadow-black/30">
        {/* Header */}
        <div className="px-6 sm:px-8 py-5 border-b border-[var(--theme-border)] flex items-center justify-between bg-[var(--theme-card-subtle)]/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[var(--theme-primary-subtle)] border border-[var(--theme-primary-border)] flex items-center justify-center text-[var(--theme-primary)] shadow-xs">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black text-[var(--theme-text-title)]">
                ตารางเปรียบเทียบหลักสูตร (Curriculum Comparison Matrix)
              </h2>
              <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold">
                เปรียบเทียบโครงสร้าง ค่าธรรมเนียม และจุดเด่นของหลักสูตร
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] border border-[var(--theme-border)] cursor-pointer transition shadow-2xs"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Matrix Content Table */}
        <div className="flex-1 overflow-auto p-6 sm:p-8">
          <div className="min-w-[750px]">
            <table className="w-full text-xs sm:text-sm text-left border-collapse">
              <thead>
                <tr className="border-b border-[var(--theme-border)]">
                  <th className="p-3.5 text-[var(--theme-text-title)] font-black w-1/5 bg-[var(--theme-card-subtle)] rounded-l-2xl text-xs sm:text-sm">
                    หัวข้อเปรียบเทียบ
                  </th>
                  {courses.map((c) => (
                    <th key={c.id} className="p-3.5 text-[var(--theme-text-title)] font-black w-1/5">
                      <div className="space-y-1">
                        <span className="text-xs font-black text-[var(--theme-primary)] block">
                          {c.university_th}
                        </span>
                        <span className="line-clamp-2 text-xs sm:text-sm font-bold">{c.title_th}</span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--theme-border)] text-[var(--theme-text-body)]">
                <tr>
                  <td className="p-3.5 font-bold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60 text-xs sm:text-sm">ระดับปริญญา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3.5 font-black text-[var(--theme-primary)] text-xs sm:text-sm">
                      {c.degree_level} {c.degree_name ? `(${c.degree_name})` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3.5 font-bold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60 text-xs sm:text-sm">คณะ / ภาควิชา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3.5 font-semibold text-xs sm:text-sm">
                      {c.faculty_th} {c.department_th ? `• ${c.department_th}` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3.5 font-bold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60 text-xs sm:text-sm">ค่าธรรมเนียมการศึกษา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3.5 font-black text-[var(--theme-accent)] text-xs sm:text-sm">
                      {c.tuition_per_semester || "ตามประกาศสถาบัน"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3.5 font-bold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60 text-xs sm:text-sm">ระยะเวลาการศึกษา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3.5 font-semibold text-xs sm:text-sm">
                      {c.duration_years || "4 ปี"} {c.total_credits ? `(${c.total_credits})` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3.5 font-bold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60 text-xs sm:text-sm">จุดเด่นหลักสูตร</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3.5 text-xs sm:text-sm text-[var(--theme-text-body)] leading-relaxed">
                      {c.curriculum_highlights && c.curriculum_highlights.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1">
                          {c.curriculum_highlights.slice(0, 2).map((h, i) => (
                            <li key={i} className="font-medium">{h}</li>
                          ))}
                        </ul>
                      ) : (
                        "-"
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3.5 font-bold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60 text-xs sm:text-sm">เส้นทางอาชีพ</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3.5 text-xs sm:text-sm text-[var(--theme-text-body)] font-semibold">
                      {c.career_paths && c.career_paths.length > 0 ? c.career_paths.join(", ") : "-"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3.5 font-bold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60 text-xs sm:text-sm">ข้อมูลทางการ</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3.5">
                      {c.website_url ? (
                        <a
                          href={c.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[var(--theme-primary)] font-black hover:underline inline-flex items-center gap-1 text-xs sm:text-sm"
                        >
                          <span>เปิดเว็บไซต์</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      ) : (
                        "-"
                      )}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 sm:px-8 py-4.5 border-t border-[var(--theme-border)] bg-[var(--theme-card-subtle)]/90 flex items-center justify-between">
          <button
            onClick={onClearAll}
            className="text-xs sm:text-sm text-[var(--theme-accent)] font-black hover:underline cursor-pointer"
          >
            ล้างการเปรียบเทียบทั้งหมด
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-black transition-all cursor-pointer shadow-md"
          >
            ปิดหน้าต่าง
          </button>
        </div>
      </div>
    </div>
  );
};

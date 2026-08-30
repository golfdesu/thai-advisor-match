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
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[var(--theme-border)] flex items-center justify-between bg-[var(--theme-card-subtle)]">
          <div className="flex items-center gap-2.5">
            <Scale className="w-5 h-5 text-[var(--theme-primary)]" />
            <h2 className="text-base font-bold text-[var(--theme-text-title)]">
              ตารางเปรียบเทียบหลักสูตร (Curriculum Comparison Matrix)
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] border border-[var(--theme-border)] cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Matrix Content Table */}
        <div className="flex-1 overflow-auto p-6">
          <div className="min-w-[700px]">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-[var(--theme-border)]">
                  <th className="p-3 text-[var(--theme-text-title)] font-bold w-1/5 bg-[var(--theme-card-subtle)] rounded-l-xl">
                    หัวข้อเปรียบเทียบ
                  </th>
                  {courses.map((c) => (
                    <th key={c.id} className="p-3 text-[var(--theme-text-title)] font-bold w-1/5">
                      <div className="space-y-1">
                        <span className="text-[10px] font-bold text-[var(--theme-primary)] block">
                          {c.university_th}
                        </span>
                        <span className="line-clamp-2">{c.title_th}</span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--theme-border)] text-[var(--theme-text-body)]">
                <tr>
                  <td className="p-3 font-semibold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60">ระดับปริญญา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3 font-bold text-[var(--theme-primary)]">
                      {c.degree_level} {c.degree_name ? `(${c.degree_name})` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60">คณะ / ภาควิชา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3">
                      {c.faculty_th} {c.department_th ? `• ${c.department_th}` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60">ค่าธรรมเนียมการศึกษา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3 font-bold text-[var(--theme-text-title)]">
                      {c.tuition_per_semester || "ตามประกาศสถาบัน"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60">ระยะเวลาการศึกษา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3">
                      {c.duration_years || "4 ปี"} {c.total_credits ? `(${c.total_credits})` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60">จุดเด่นหลักสูตร</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3 text-[11px] text-[var(--theme-text-body)] leading-relaxed">
                      {c.curriculum_highlights && c.curriculum_highlights.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1">
                          {c.curriculum_highlights.slice(0, 2).map((h, i) => (
                            <li key={i}>{h}</li>
                          ))}
                        </ul>
                      ) : (
                        "-"
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60">เส้นทางอาชีพ</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3 text-[11px] text-[var(--theme-text-body)] font-medium">
                      {c.career_paths && c.career_paths.length > 0 ? c.career_paths.join(", ") : "-"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-[var(--theme-text-title)] bg-[var(--theme-card-subtle)]/60">ข้อมูลทางการ</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3">
                      {c.website_url ? (
                        <a
                          href={c.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[var(--theme-primary)] font-bold hover:underline inline-flex items-center gap-1"
                        >
                          <span>เปิดเว็บไซต์</span>
                          <ExternalLink className="w-3 h-3" />
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
        <div className="px-6 py-4 border-t border-[var(--theme-border)] bg-[var(--theme-card-subtle)] flex items-center justify-between">
          <button
            onClick={onClearAll}
            className="text-xs text-[var(--theme-accent)] font-bold hover:underline cursor-pointer"
          >
            ล้างการเปรียบเทียบทั้งหมด
          </button>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold transition-all cursor-pointer"
          >
            ปิดหน้าต่าง
          </button>
        </div>
      </div>
    </div>
  );
};

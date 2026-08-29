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
    <div className="fixed inset-0 z-50 bg-stone-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-stone-200 rounded-3xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-stone-200 flex items-center justify-between bg-stone-50/80">
          <div className="flex items-center gap-2.5">
            <Scale className="w-5 h-5 text-[#5B0F18]" />
            <h2 className="text-base font-bold text-stone-900">
              ตารางเปรียบเทียบหลักสูตร (Curriculum Comparison Matrix)
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl bg-white hover:bg-stone-100 text-stone-500 hover:text-stone-900 border border-stone-200 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Matrix Content Table */}
        <div className="flex-1 overflow-auto p-6">
          <div className="min-w-[700px]">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-stone-200">
                  <th className="p-3 text-stone-700 font-bold w-1/5 bg-stone-50 rounded-l-xl">
                    หัวข้อเปรียบเทียบ
                  </th>
                  {courses.map((c) => (
                    <th key={c.id} className="p-3 text-stone-900 font-bold w-1/5">
                      <div className="space-y-1">
                        <span className="text-[10px] font-bold text-[#5B0F18] block">
                          {c.university_th}
                        </span>
                        <span className="line-clamp-2">{c.title_th}</span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-200 text-stone-700">
                <tr>
                  <td className="p-3 font-semibold text-stone-800 bg-stone-50/50">ระดับปริญญา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3 font-bold text-[#5B0F18]">
                      {c.degree_level} {c.degree_name ? `(${c.degree_name})` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-stone-800 bg-stone-50/50">คณะ / ภาควิชา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3">
                      {c.faculty_th} {c.department_th ? `• ${c.department_th}` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-stone-800 bg-stone-50/50">ค่าธรรมเนียมการศึกษา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3 font-bold text-stone-900">
                      {c.tuition_per_semester || "ตามประกาศสถาบัน"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-stone-800 bg-stone-50/50">ระยะเวลาการศึกษา</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3">
                      {c.duration_years || "4 ปี"} {c.total_credits ? `(${c.total_credits})` : ""}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-stone-800 bg-stone-50/50">จุดเด่นหลักสูตร</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3 text-[11px] text-stone-700 leading-relaxed">
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
                  <td className="p-3 font-semibold text-stone-800 bg-stone-50/50">เส้นทางอาชีพ</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3 text-[11px] text-stone-700 font-medium">
                      {c.career_paths && c.career_paths.length > 0 ? c.career_paths.join(", ") : "-"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-3 font-semibold text-stone-800 bg-stone-50/50">ข้อมูลทางการ</td>
                  {courses.map((c) => (
                    <td key={c.id} className="p-3">
                      {c.website_url ? (
                        <a
                          href={c.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#5B0F18] font-bold hover:underline inline-flex items-center gap-1"
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
        <div className="px-6 py-4 border-t border-stone-200 bg-stone-50/80 flex items-center justify-between">
          <button
            onClick={onClearAll}
            className="text-xs text-rose-700 font-bold hover:underline cursor-pointer"
          >
            ล้างการเปรียบเทียบทั้งหมด
          </button>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-stone-800 hover:bg-stone-900 text-white text-xs font-bold transition-all cursor-pointer"
          >
            ปิดหน้าต่าง
          </button>
        </div>
      </div>
    </div>
  );
};

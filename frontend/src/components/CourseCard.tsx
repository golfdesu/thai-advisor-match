"use client";

import React from "react";
import { Course } from "@/types";
import {
  Building2,
  ExternalLink,
  Layers,
  Scale,
  Heart,
  BookOpen,
  Briefcase
} from "lucide-react";

interface CourseCardProps {
  course: Course;
  isSaved: boolean;
  isCompared: boolean;
  onToggleBookmark: (id: string) => void;
  onToggleCompare: (course: Course) => void;
}

function getSelectivityBadge(course: Course) {
  const title = (course.title_th + " " + (course.title_en || "")).toLowerCase();
  const uni = (course.university_th + " " + course.university).toLowerCase();

  if (
    title.includes("แพทย์") ||
    title.includes("ทันตแพทย์") ||
    title.includes("medicine") ||
    title.includes("dentistry") ||
    (uni.includes("จุฬา") && (title.includes("วิศวกรรม") || title.includes("พาณิชยศาสตร์") || title.includes("ai"))) ||
    (uni.includes("ธรรมศาสตร์") && (title.includes("นิติศาสตร์") || title.includes("siit") || title.includes("พาณิชยศาสตร์")))
  ) {
    return { 
      label: "การแข่งขันสูง", 
      color: "bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)] border-[var(--theme-primary-border)]" 
    };
  }
  if (
    title.includes("นานาชาติ") ||
    title.includes("international") ||
    title.includes("bascii") ||
    title.includes("balac") ||
    title.includes("bba") ||
    title.includes("ise")
  ) {
    return { 
      label: "หลักสูตรนานาชาติ", 
      color: "bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] border-[var(--theme-accent-border)]" 
    };
  }
  if (
    title.includes("ดิจิทัล") ||
    title.includes("หุ่นยนต์") ||
    title.includes("ai") ||
    title.includes("data") ||
    title.includes("ภาพยนตร์") ||
    title.includes("ศิลปกรรม")
  ) {
    return { 
      label: "เน้นทักษะ & Portfolio", 
      color: "bg-[var(--theme-card-subtle)] text-[var(--theme-text-title)] border-[var(--theme-border)]" 
    };
  }
  return { 
    label: "รับตรง / Admission", 
    color: "bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] border-[var(--theme-border)]" 
  };
}

export const CourseCard: React.FC<CourseCardProps> = ({
  course,
  isSaved,
  isCompared,
  onToggleBookmark,
  onToggleCompare,
}) => {
  const badge = getSelectivityBadge(course);

  return (
    <div className="group relative p-5 sm:p-6 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] hover:border-[var(--theme-primary)] transition-all flex flex-col justify-between hover:shadow-md">
      <div className="space-y-4">
        {/* Top Header Meta */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="px-2.5 py-0.5 rounded-md bg-[var(--theme-card-subtle)] text-[var(--theme-text-title)] text-[11px] font-bold border border-[var(--theme-border)]">
              {course.degree_level || "ปริญญาตรี"}
            </span>
            <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border ${badge.color}`}>
              {badge.label}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => onToggleCompare(course)}
              className={`p-1.5 rounded-lg border text-xs transition-all cursor-pointer ${
                isCompared
                  ? "bg-[var(--theme-primary)] border-[var(--theme-primary)] text-[var(--theme-primary-contrast)]"
                  : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)]"
              }`}
              title="เปรียบเทียบหลักสูตร"
            >
              <Scale className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onToggleBookmark(course.id)}
              className={`p-1.5 rounded-lg border text-xs transition-all cursor-pointer ${
                isSaved
                  ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)]"
                  : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)]"
              }`}
              title="บันทึกหลักสูตร"
            >
              <Heart className={`w-3.5 h-3.5 ${isSaved ? "fill-[var(--theme-accent)]" : ""}`} />
            </button>
          </div>
        </div>

        {/* Title & University */}
        <div>
          <h3 className="text-base font-bold text-[var(--theme-text-title)] group-hover:text-[var(--theme-primary)] transition-colors leading-snug">
            {course.title_th}
          </h3>
          {course.title_en && (
            <p className="text-xs text-[var(--theme-text-muted)] line-clamp-1 mt-0.5">{course.title_en}</p>
          )}
        </div>

        {/* Institution Info */}
        <div className="flex items-center gap-1.5 text-xs text-[var(--theme-text-body)]">
          <Building2 className="w-3.5 h-3.5 text-[var(--theme-text-muted)] flex-shrink-0" />
          <span className="truncate">
            {course.university_th} • {course.faculty_th}
          </span>
        </div>

        {/* Tuition & Duration Meta Card */}
        <div className="grid grid-cols-2 gap-2 p-2.5 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[11px]">
          <div>
            <span className="text-[var(--theme-text-muted)] block text-[10px]">ค่าเทอม / ภาคเรียน:</span>
            <span className="font-bold text-[var(--theme-text-title)]">
              {course.tuition_per_semester || "ตามประกาศสถาบัน"}
            </span>
          </div>
          <div>
            <span className="text-[var(--theme-text-muted)] block text-[10px]">ระยะเวลา / หน่วยกิต:</span>
            <span className="font-semibold text-[var(--theme-text-body)]">
              {course.duration_years || "4 ปี"} {course.total_credits ? `(${course.total_credits})` : ""}
            </span>
          </div>
        </div>

        {/* Curriculum Highlight */}
        {course.curriculum_highlights && course.curriculum_highlights.length > 0 && (
          <p className="text-xs text-[var(--theme-text-body)] line-clamp-2 leading-relaxed">
            {course.curriculum_highlights[0]}
          </p>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="pt-4 mt-4 border-t border-[var(--theme-border)] flex items-center justify-between">
        {course.career_paths && course.career_paths.length > 0 ? (
          <span className="text-[11px] text-[var(--theme-text-muted)] truncate max-w-[200px] flex items-center gap-1">
            <Briefcase className="w-3 h-3 text-[var(--theme-text-muted)] flex-shrink-0" />
            <span className="truncate">{course.career_paths[0]}</span>
          </span>
        ) : (
          <span className="text-[11px] text-[var(--theme-text-muted)]">หลักสูตรมาตรฐาน</span>
        )}

        {course.website_url ? (
          <a
            href={course.website_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-bold text-[var(--theme-primary)] hover:underline flex items-center gap-1"
          >
            <span>ข้อมูลหลักสูตร</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        ) : (
          <span className="text-xs text-[var(--theme-text-muted)]">ติดต่อคณะ</span>
        )}
      </div>
    </div>
  );
};

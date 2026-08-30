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
  Briefcase,
  Sparkles,
  ArrowRight,
  Clock,
  Coins
} from "lucide-react";

interface CourseCardProps {
  course: Course;
  isSaved: boolean;
  isCompared: boolean;
  onToggleBookmark: (id: string) => void;
  onToggleCompare: (course: Course) => void;
  onSelectCourse?: (course: Course) => void;
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
  onSelectCourse,
}) => {
  const badge = getSelectivityBadge(course);

  return (
    <div
      onClick={() => onSelectCourse && onSelectCourse(course)}
      className="group relative p-5 sm:p-6 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] hover:border-[var(--theme-primary)] transition-all duration-200 flex flex-col justify-between hover:shadow-md cursor-pointer"
    >
      <div className="space-y-4">
        {/* Top Header Meta */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-3 py-1 rounded-xl bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)] text-xs font-black border border-[var(--theme-primary-border)] shadow-2xs">
              {course.degree_level || "ปริญญาตรี"}
            </span>
            <span className={`px-2.5 py-1 rounded-xl text-xs font-bold border shadow-2xs ${badge.color}`}>
              {badge.label}
            </span>
          </div>

          <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => onToggleCompare(course)}
              className={`p-2 rounded-xl border text-xs transition-all cursor-pointer ${
                isCompared
                  ? "bg-[var(--theme-primary)] border-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-xs"
                  : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] hover:border-[var(--theme-primary)]"
              }`}
              title="เปรียบเทียบหลักสูตร"
            >
              <Scale className="w-4 h-4" />
            </button>
            <button
              onClick={() => onToggleBookmark(course.id)}
              className={`p-2 rounded-xl border text-xs transition-all cursor-pointer ${
                isSaved
                  ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)] shadow-xs"
                  : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-accent)] hover:border-[var(--theme-accent)]"
              }`}
              title="บันทึกหลักสูตร"
            >
              <Heart className={`w-4 h-4 ${isSaved ? "fill-[var(--theme-accent)]" : ""}`} />
            </button>
          </div>
        </div>

        {/* Title & University */}
        <div>
          <h3 className="text-lg sm:text-xl font-black text-[var(--theme-text-title)] group-hover:text-[var(--theme-primary)] transition-colors leading-snug">
            {course.title_th}
          </h3>
          {course.title_en && course.title_en !== "Not specified" && (
            <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-medium line-clamp-1 mt-1">{course.title_en}</p>
          )}
        </div>

        {/* Institution Info */}
        <div className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-[var(--theme-text-body)]">
          <div className="w-6 h-6 rounded-lg bg-[var(--theme-primary-subtle)] flex items-center justify-center text-[var(--theme-primary)] shrink-0">
            <Building2 className="w-3.5 h-3.5" />
          </div>
          <span className="truncate">
            {course.university_th} • <span className="text-[var(--theme-text-muted)] font-medium">{course.faculty_th}</span>
          </span>
        </div>

        {/* Tuition & Duration Meta Card */}
        <div className="grid grid-cols-2 gap-2 p-3.5 rounded-xl bg-[var(--theme-card-subtle)]/80 border border-[var(--theme-border)] text-xs">
          <div>
            <span className="text-[var(--theme-text-muted)] block text-xs font-semibold flex items-center gap-1">
              <Coins className="w-3.5 h-3.5 text-[var(--theme-accent)]" /> ค่าเทอม/ภาคเรียน:
            </span>
            <span className="font-extrabold text-[var(--theme-text-title)] block truncate mt-0.5 text-xs sm:text-sm">
              {course.tuition_per_semester || "ตามประกาศสถาบัน"}
            </span>
          </div>
          <div>
            <span className="text-[var(--theme-text-muted)] block text-xs font-semibold flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-[var(--theme-primary)]" /> ระยะเวลา/หน่วยกิต:
            </span>
            <span className="font-bold text-[var(--theme-text-body)] block truncate mt-0.5 text-xs sm:text-sm">
              {course.duration_years || "4 ปี"} {course.total_credits ? `(${course.total_credits})` : ""}
            </span>
          </div>
        </div>

        {/* Curriculum Highlight */}
        {course.curriculum_highlights && course.curriculum_highlights.length > 0 && (
          <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] line-clamp-2 leading-relaxed font-normal">
            {course.curriculum_highlights[0]}
          </p>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="pt-4 mt-4 border-t border-[var(--theme-border)] flex items-center justify-between" onClick={(e) => e.stopPropagation()}>
        {course.career_paths && course.career_paths.length > 0 ? (
          <span className="text-xs font-medium text-[var(--theme-text-muted)] truncate max-w-[200px] flex items-center gap-1.5">
            <Briefcase className="w-4 h-4 text-[var(--theme-accent)] flex-shrink-0" />
            <span className="truncate">{course.career_paths[0]}</span>
          </span>
        ) : (
          <span className="text-xs text-[var(--theme-text-muted)]">หลักสูตรมาตรฐาน</span>
        )}

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onSelectCourse && onSelectCourse(course)}
            className="text-xs sm:text-sm font-black text-[var(--theme-primary)] hover:underline flex items-center gap-1 cursor-pointer group/btn"
          >
            <span>โครงสร้าง</span>
            <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-0.5 transition-transform" />
          </button>
          {course.website_url && (
            <a
              href={course.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-bold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] flex items-center gap-1 p-1.5 rounded-lg hover:bg-[var(--theme-card-subtle)] transition"
              title="ไปยังเว็บไซต์คณะ/หลักสูตร"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

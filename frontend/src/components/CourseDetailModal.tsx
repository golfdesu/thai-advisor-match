"use client";

import React from "react";
import {
  X,
  Building2,
  GraduationCap,
  Clock,
  Award,
  DollarSign,
  Briefcase,
  CheckCircle2,
  ExternalLink,
  Search,
  Bookmark,
  Share2,
  Tag,
  Sparkles,
  BookOpen,
  Globe
} from "lucide-react";
import { Course } from "@/types";

interface CourseDetailModalProps {
  course: Course | null;
  isOpen: boolean;
  onClose: () => void;
  isSaved?: boolean;
  onToggleBookmark?: (id: string) => void;
}

export const CourseDetailModal: React.FC<CourseDetailModalProps> = ({
  course,
  isOpen,
  onClose,
  isSaved = false,
  onToggleBookmark
}) => {
  if (!isOpen || !course) return null;

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: course.title_th,
        text: `ดูรายละเอียดโครงสร้างหลักสูตร ${course.title_th} (${course.university_th}) บน Thai EduCenter`,
        url: window.location.href,
      }).catch(() => {});
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert("คัดลอกลิงก์เรียบร้อยแล้ว!");
    }
  };

  const googleSearchUrl = `https://www.google.com/search?q=${encodeURIComponent(
    `${course.title_th} ${course.university_th} หลักสูตร มคอ.2`
  )}`;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="bg-[var(--theme-card)] border-2 border-[var(--theme-border)] rounded-3xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden relative shadow-black/30">
        {/* Modal Top Header with ambient lighting */}
        <div className="p-6 sm:p-8 border-b border-[var(--theme-border)] flex items-start justify-between gap-4 bg-[var(--theme-card-subtle)]/70 relative">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-bold px-3 py-1 rounded-xl">
                {course.degree_level || "ระดับปริญญา"}
              </span>
              {course.degree_name && (
                <span className="bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-title)] text-xs sm:text-sm font-extrabold px-3.5 py-1 rounded-xl shadow-2xs">
                  {course.degree_name}
                </span>
              )}
            </div>
            <h3 className="text-xl sm:text-2xl font-black text-[var(--theme-text-title)] leading-snug">
              {course.title_th}
            </h3>
            {course.title_en && course.title_en !== "Not specified" && (
              <p className="text-sm text-[var(--theme-text-muted)] font-semibold mt-1">
                {course.title_en}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onToggleBookmark && (
              <button
                onClick={() => onToggleBookmark(course.id)}
                className={`p-2.5 rounded-xl border transition-all cursor-pointer shadow-xs ${
                  isSaved
                    ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)]"
                    : "bg-[var(--theme-card)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-accent)] hover:border-[var(--theme-accent)]"
                }`}
                title={isSaved ? "ลบออกจากรายการบันทึก" : "บันทึกหลักสูตรนี้"}
              >
                <Bookmark size={18} className={isSaved ? "fill-current" : ""} />
              </button>
            )}
            <button
              onClick={handleShare}
              className="p-2.5 rounded-xl bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-primary)] hover:border-[var(--theme-primary)] transition-all shadow-xs cursor-pointer"
              title="แชร์หลักสูตรนี้"
            >
              <Share2 size={18} />
            </button>
            <button
              onClick={onClose}
              className="p-2.5 rounded-xl bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] hover:border-[var(--theme-border)] transition-all shadow-xs cursor-pointer"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Scrollable Content Body */}
        <div className="p-6 sm:p-8 overflow-y-auto space-y-6">
          {/* Institution Info Card */}
          <div className="p-5 rounded-2xl bg-[var(--theme-card-subtle)]/70 border border-[var(--theme-border)] flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-[var(--theme-primary-subtle)] border border-[var(--theme-primary-border)] flex items-center justify-center text-[var(--theme-primary)] shrink-0 shadow-xs">
              <Building2 size={26} />
            </div>
            <div>
              <h4 className="text-base sm:text-lg font-black text-[var(--theme-text-title)]">
                {course.university_th}
              </h4>
              <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold mt-0.5">
                {course.faculty_th} {course.department_th ? `• ${course.department_th}` : ""}
              </p>
            </div>
          </div>

          {/* Key Facts Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-2xl bg-[var(--theme-bg)] border border-[var(--theme-border-subtle)] shadow-2xs">
              <span className="text-xs font-bold text-[var(--theme-text-muted)] flex items-center gap-1.5">
                <DollarSign size={14} className="text-[var(--theme-accent)]" /> ค่าเทอม/ภาคเรียน
              </span>
              <span className="text-xs sm:text-sm font-black text-[var(--theme-accent)] mt-1.5 block truncate">
                {course.tuition_per_semester || "ตามประกาศสถาบัน"}
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--theme-bg)] border border-[var(--theme-border-subtle)] shadow-2xs">
              <span className="text-xs font-bold text-[var(--theme-text-muted)] flex items-center gap-1.5">
                <Clock size={14} className="text-[var(--theme-primary)]" /> ระยะเวลาศึกษา
              </span>
              <span className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] mt-1.5 block truncate">
                {course.duration_years || "4 ปี"}
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--theme-bg)] border border-[var(--theme-border-subtle)] shadow-2xs">
              <span className="text-xs font-bold text-[var(--theme-text-muted)] flex items-center gap-1.5">
                <Award size={14} className="text-[var(--theme-primary)]" /> จำนวนหน่วยกิต
              </span>
              <span className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] mt-1.5 block truncate">
                {course.total_credits || "ตามโครงสร้าง"}
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--theme-bg)] border border-[var(--theme-border-subtle)] shadow-2xs">
              <span className="text-xs font-bold text-[var(--theme-text-muted)] flex items-center gap-1.5">
                <GraduationCap size={14} className="text-[var(--theme-primary)]" /> แผนการเรียน
              </span>
              <span className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] mt-1.5 block truncate">
                {course.program_type || "ภาคปกติ / พิเศษ"}
              </span>
            </div>
          </div>

          {/* Description Section */}
          {course.description && (
            <div className="space-y-2.5">
              <h4 className="text-xs sm:text-sm font-black text-[var(--theme-primary)] uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles size={16} />
                <span>คำอธิบายหลักสูตร & วัตถุประสงค์ (Description)</span>
              </h4>
              <p className="text-xs sm:text-sm text-[var(--theme-text-body)] leading-relaxed font-normal bg-[var(--theme-bg)] p-5 rounded-2xl border border-[var(--theme-border-subtle)]">
                {course.description}
              </p>
            </div>
          )}

          {/* Curriculum Highlights */}
          {course.curriculum_highlights && course.curriculum_highlights.length > 0 && (
            <div className="space-y-2.5">
              <h4 className="text-xs sm:text-sm font-black text-[var(--theme-primary)] uppercase tracking-wider flex items-center gap-1.5">
                <BookOpen size={16} />
                <span>จุดเด่น & โครงสร้างรายวิชาสำคัญ (Curriculum Highlights / TQF-2)</span>
              </h4>
              <div className="space-y-3 bg-[var(--theme-bg)] p-5 rounded-2xl border border-[var(--theme-border-subtle)]">
                {course.curriculum_highlights.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3 text-xs sm:text-sm text-[var(--theme-text-body)]">
                    <CheckCircle2 size={18} className="text-[var(--theme-primary)] shrink-0 mt-0.5" />
                    <span className="font-semibold leading-relaxed">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Career Paths */}
          {course.career_paths && course.career_paths.length > 0 && (
            <div className="space-y-2.5">
              <h4 className="text-xs sm:text-sm font-black text-[var(--theme-accent)] uppercase tracking-wider flex items-center gap-1.5">
                <Briefcase size={16} />
                <span>เส้นทางอาชีพและโอกาสการทำงาน (Career Opportunities)</span>
              </h4>
              <div className="flex flex-wrap gap-2.5 bg-[var(--theme-bg)] p-5 rounded-2xl border border-[var(--theme-border-subtle)]">
                {course.career_paths.map((career, idx) => (
                  <span
                    key={idx}
                    className="bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-title)] text-xs sm:text-sm font-bold px-3.5 py-1.5 rounded-xl shadow-2xs flex items-center gap-2"
                  >
                    <span className="w-2 h-2 rounded-full bg-[var(--theme-accent)]" />
                    {career}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Academic Tags */}
          {course.tags && course.tags.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-[var(--theme-border-subtle)]">
              <Tag size={14} className="text-[var(--theme-text-muted)]" />
              {course.tags.map((t, idx) => (
                <span
                  key={idx}
                  className="text-xs font-bold text-[var(--theme-text-muted)] bg-[var(--theme-card-subtle)] px-3 py-1 rounded-xl border border-[var(--theme-border-subtle)]"
                >
                  #{t}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Modal Sticky Footer Actions */}
        <div className="p-5 sm:p-6 border-t border-[var(--theme-border)] bg-[var(--theme-card-subtle)]/90 flex flex-col sm:flex-row items-center justify-between gap-3">
          <a
            href={googleSearchUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto px-5 py-3 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-xs sm:text-sm font-black text-[var(--theme-text-title)] flex items-center justify-center gap-2 transition shadow-2xs hover:border-[var(--theme-primary)]"
          >
            <Search size={15} className="text-[var(--theme-primary)]" />
            <span>ค้นหา มคอ.2 บน Google</span>
          </a>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            {course.website_url ? (
              <a
                href={course.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 sm:flex-initial px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition cursor-pointer"
              >
                <Globe size={15} />
                <span>ไปยังเว็บไซต์หลักสูตร / คณะ</span>
                <ExternalLink size={15} />
              </a>
            ) : (
              <button
                onClick={() => window.open(googleSearchUrl, "_blank")}
                className="flex-1 sm:flex-initial px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition cursor-pointer"
              >
                <span>ค้นหาเว็บไซต์ทางการ</span>
                <ExternalLink size={15} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

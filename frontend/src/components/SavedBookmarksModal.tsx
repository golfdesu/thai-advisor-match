"use client";

import React from "react";
import Link from "next/link";
import { Bookmark, X, Trash2, ExternalLink, User, BookOpen } from "lucide-react";
import { Course, SearchMatchResult } from "@/types";

interface SavedBookmarksModalProps {
  isOpen: boolean;
  savedCourses: string[];
  savedAdvisors: string[];
  allCourses?: Course[];
  allAdvisors?: SearchMatchResult[];
  onClose: () => void;
  onRemoveCourse: (id: string) => void;
  onRemoveAdvisor: (id: string) => void;
}

export const SavedBookmarksModal: React.FC<SavedBookmarksModalProps> = ({
  isOpen,
  savedCourses,
  savedAdvisors,
  allCourses = [],
  allAdvisors = [],
  onClose,
  onRemoveCourse,
  onRemoveAdvisor,
}) => {
  if (!isOpen) return null;

  const courseMap = new Map(allCourses.map((c) => [c.id, c]));
  const advisorMap = new Map(allAdvisors.map((a) => [a.faculty.id, a.faculty]));

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--theme-border)] flex items-center justify-between bg-[var(--theme-card-subtle)]">
          <div className="flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-[var(--theme-accent)]" />
            <h2 className="text-base font-bold text-[var(--theme-text-title)]">รายการที่บันทึกไว้ (Bookmarks)</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] border border-[var(--theme-border)] cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-6 space-y-5">
          {/* Courses Bookmarks */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-[var(--theme-text-title)] uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
              <span>หลักสูตรที่บันทึก ({savedCourses.length})</span>
            </h4>
            {savedCourses.length === 0 ? (
              <p className="text-xs text-[var(--theme-text-muted)] italic bg-[var(--theme-card-subtle)] p-3 rounded-xl">
                ยังไม่มีหลักสูตรที่บันทึกไว้
              </p>
            ) : (
              <div className="space-y-2">
                {savedCourses.map((id) => {
                  const course = courseMap.get(id);
                  return (
                    <div
                      key={id}
                      className="p-3.5 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] flex items-center justify-between gap-3"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-bold text-xs text-[var(--theme-text-title)] truncate">
                          {course ? course.title_th : id}
                        </div>
                        {course && (
                          <p className="text-[11px] text-[var(--theme-text-muted)] truncate">
                            {course.university_th} • {course.faculty_th}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {course?.website_url && (
                          <a
                            href={course.website_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 rounded-lg bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-primary)] hover:underline flex items-center gap-1 text-[11px] font-bold"
                          >
                            <span>เว็บหลักสูตร</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                        <button
                          onClick={() => onRemoveCourse(id)}
                          className="text-xs text-[var(--theme-accent)] font-bold hover:underline flex items-center gap-1 cursor-pointer px-2 py-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>ลบออก</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Advisors Bookmarks */}
          <div className="space-y-2 pt-4 border-t border-[var(--theme-border)]">
            <h4 className="text-xs font-bold text-[var(--theme-text-title)] uppercase tracking-wider flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-[var(--theme-accent)]" />
              <span>อาจารย์ที่ปรึกษาที่บันทึก ({savedAdvisors.length})</span>
            </h4>
            {savedAdvisors.length === 0 ? (
              <p className="text-xs text-[var(--theme-text-muted)] italic bg-[var(--theme-card-subtle)] p-3 rounded-xl">
                ยังไม่มีอาจารย์ที่บันทึกไว้
              </p>
            ) : (
              <div className="space-y-2">
                {savedAdvisors.map((id) => {
                  const fac = advisorMap.get(id);
                  return (
                    <div
                      key={id}
                      className="p-3.5 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] flex items-center justify-between gap-3"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-bold text-xs text-[var(--theme-text-title)] truncate">
                          {fac ? fac.full_name_th : id}
                        </div>
                        {fac && (
                          <p className="text-[11px] text-[var(--theme-text-muted)] truncate">
                            {fac.university_th} • {fac.faculty_th}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Link
                          href={`/advisor/${id}`}
                          onClick={onClose}
                          className="p-1.5 rounded-lg bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-primary)] hover:underline flex items-center gap-1 text-[11px] font-bold"
                        >
                          <span>ดูโปรไฟล์</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                        <button
                          onClick={() => onRemoveAdvisor(id)}
                          className="text-xs text-[var(--theme-accent)] font-bold hover:underline flex items-center gap-1 cursor-pointer px-2 py-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>ลบออก</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="px-6 py-4 border-t border-[var(--theme-border)] bg-[var(--theme-card-subtle)] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold cursor-pointer"
          >
            ปิด
          </button>
        </div>
      </div>
    </div>
  );
};

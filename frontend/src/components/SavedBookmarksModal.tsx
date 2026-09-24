"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Bookmark, X, Trash2, ExternalLink, User, BookOpen } from "lucide-react";
import type { Course, FacultyMember, SearchMatchResult } from "@/types";
import { API_BASE_URL } from "@/lib/config";

interface SavedBookmarksModalProps {
  isOpen: boolean;
  savedCourses: string[];
  savedAdvisors: string[];
  allCourses?: Course[];
  allAdvisors?: SearchMatchResult[];
  onClose: () => void;
  onRemoveCourse: (id: string) => void;
  onRemoveAdvisor: (id: string) => void;
  onSelectCourse?: (course: Course) => void;
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
  onSelectCourse,
}) => {
  const [extraCourses, setExtraCourses] = useState<Record<string, Course>>({});
  const [extraAdvisors, setExtraAdvisors] = useState<Record<string, FacultyMember>>({});

  const courseMap = new Map(allCourses.map((c) => [c.id, c]));
  const advisorMap = new Map(allAdvisors.map((a) => [a.faculty.id, a.faculty]));

  useEffect(() => {
    if (!isOpen) return;

    // Fetch missing course details for bookmarks not in the active search slice
    const missingCourseIds = savedCourses.filter((id) => !courseMap.has(id) && !extraCourses[id]);
    missingCourseIds.forEach((id) => {
      fetch(`${API_BASE_URL}/courses/${id}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) setExtraCourses((prev) => ({ ...prev, [id]: data }));
        })
        .catch(() => {});
    });

    // Fetch missing advisor details for bookmarks not in the active search slice
    const missingAdvisorIds = savedAdvisors.filter((id) => !advisorMap.has(id) && !extraAdvisors[id]);
    missingAdvisorIds.forEach((id) => {
      fetch(`${API_BASE_URL}/faculty/${id}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) setExtraAdvisors((prev) => ({ ...prev, [id]: data }));
        })
        .catch(() => {});
    });
  }, [isOpen, savedCourses, savedAdvisors]);

  if (!isOpen) return null;

  return (
    <div className="ui-modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="ui-modal w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="saved-bookmarks-title">
        <div className="ui-modal-header px-6 sm:px-8 py-5 border-b border-[var(--theme-border)] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[var(--theme-accent-subtle)] border border-[var(--theme-accent-border)] flex items-center justify-center text-[var(--theme-accent)] shadow-xs">
              <Bookmark className="w-5 h-5 fill-current" />
            </div>
            <div>
              <h2 id="saved-bookmarks-title" className="text-base sm:text-lg font-black text-[var(--theme-text-title)]">รายการที่บันทึกไว้ (Bookmarks)</h2>
              <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold">
                หลักสูตรและอาจารย์ที่ปรึกษาที่คุณสนใจ
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            type="button"
            aria-label="ปิดรายการที่บันทึกไว้"
            className="ui-icon-button p-2 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-6 sm:p-8 space-y-6">
          {/* Courses Bookmarks */}
          <div className="space-y-3">
            <h4 className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-[var(--theme-primary)]" />
              <span>หลักสูตรที่บันทึก ({savedCourses.length})</span>
            </h4>
            {savedCourses.length === 0 ? (
              <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] italic bg-[var(--theme-card-subtle)] p-4 rounded-2xl border border-[var(--theme-border-subtle)]">
                ยังไม่มีหลักสูตรที่บันทึกไว้
              </p>
            ) : (
              <div className="space-y-2.5">
                {savedCourses.map((id) => {
                  const course = courseMap.get(id) || extraCourses[id];
                  return (
                    <div
                      key={id}
                      className="p-4 rounded-2xl bg-[var(--theme-card-subtle)]/80 border border-[var(--theme-border)] flex items-center justify-between gap-3 shadow-2xs"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-black text-xs sm:text-sm text-[var(--theme-text-title)] truncate">
                          {course ? course.title_th : id}
                        </div>
                        {course && (
                          <p className="text-xs text-[var(--theme-text-muted)] font-semibold truncate mt-0.5">
                            {course.university_th} • {course.faculty_th}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {onSelectCourse && course ? (
                          <button
                            type="button"
                            onClick={() => {
                              onSelectCourse(course);
                              onClose();
                            }}
                            className="px-3 py-1.5 rounded-xl bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-primary)] hover:underline flex items-center gap-1.5 text-xs font-bold shadow-2xs cursor-pointer"
                          >
                            <span>ดูโครงสร้าง</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </button>
                        ) : course?.website_url ? (
                          <a
                            href={course.website_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1.5 rounded-xl bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-primary)] hover:underline flex items-center gap-1.5 text-xs font-bold shadow-2xs"
                          >
                            <span>เว็บหลักสูตร</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        ) : null}
                        <button
                          onClick={() => onRemoveCourse(id)}
                          className="text-xs text-[var(--theme-accent)] font-bold hover:underline flex items-center gap-1 cursor-pointer px-2.5 py-1.5"
                        >
                          <Trash2 className="w-4 h-4" />
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
          <div className="space-y-3 pt-5 border-t border-[var(--theme-border)]">
            <h4 className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] uppercase tracking-wider flex items-center gap-2">
              <User className="w-4 h-4 text-[var(--theme-accent)]" />
              <span>อาจารย์ที่ปรึกษาที่บันทึก ({savedAdvisors.length})</span>
            </h4>
            {savedAdvisors.length === 0 ? (
              <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] italic bg-[var(--theme-card-subtle)] p-4 rounded-2xl border border-[var(--theme-border-subtle)]">
                ยังไม่มีอาจารย์ที่บันทึกไว้
              </p>
            ) : (
              <div className="space-y-2.5">
                {savedAdvisors.map((id) => {
                  const fac = advisorMap.get(id) || extraAdvisors[id];
                  return (
                    <div
                      key={id}
                      className="p-4 rounded-2xl bg-[var(--theme-card-subtle)]/80 border border-[var(--theme-border)] flex items-center justify-between gap-3 shadow-2xs"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-black text-xs sm:text-sm text-[var(--theme-text-title)] truncate">
                          {fac ? fac.full_name_th : id}
                        </div>
                        {fac && (
                          <p className="text-xs text-[var(--theme-text-muted)] font-semibold truncate mt-0.5">
                            {fac.university_th} • {fac.faculty_th}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Link
                          href={`/advisor/${id}`}
                          onClick={onClose}
                          className="px-3 py-1.5 rounded-xl bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-primary)] hover:underline flex items-center gap-1.5 text-xs font-bold shadow-2xs"
                        >
                          <span>ดูโปรไฟล์</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                        <button
                          onClick={() => onRemoveAdvisor(id)}
                          className="text-xs text-[var(--theme-accent)] font-bold hover:underline flex items-center gap-1 cursor-pointer px-2.5 py-1.5"
                        >
                          <Trash2 className="w-4 h-4" />
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

        <div className="ui-modal-footer px-6 sm:px-8 py-4.5 border-t border-[var(--theme-border)] flex justify-end">
          <button
            onClick={onClose}
            className="ui-primary-button px-6 py-2.5 text-xs sm:text-sm cursor-pointer"
          >
            ปิด
          </button>
        </div>
      </div>
    </div>
  );
};

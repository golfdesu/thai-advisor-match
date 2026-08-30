"use client";

import React from "react";
import { Bookmark, X, Trash2 } from "lucide-react";

interface SavedBookmarksModalProps {
  isOpen: boolean;
  savedCourses: string[];
  savedAdvisors: string[];
  onClose: () => void;
  onRemoveCourse: (id: string) => void;
  onRemoveAdvisor: (id: string) => void;
}

export const SavedBookmarksModal: React.FC<SavedBookmarksModalProps> = ({
  isOpen,
  savedCourses,
  savedAdvisors,
  onClose,
  onRemoveCourse,
  onRemoveAdvisor,
}) => {
  if (!isOpen) return null;

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
            <h4 className="text-xs font-bold text-[var(--theme-text-title)] uppercase tracking-wider">
              หลักสูตรที่บันทึก ({savedCourses.length})
            </h4>
            {savedCourses.length === 0 ? (
              <p className="text-xs text-[var(--theme-text-muted)] italic bg-[var(--theme-card-subtle)] p-3 rounded-xl">
                ยังไม่มีหลักสูตรที่บันทึกไว้
              </p>
            ) : (
              <div className="space-y-2">
                {savedCourses.map((id) => (
                  <div
                    key={id}
                    className="p-3 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] flex items-center justify-between"
                  >
                    <span className="text-xs font-semibold text-[var(--theme-text-title)]">รหัสหลักสูตร: {id}</span>
                    <button
                      onClick={() => onRemoveCourse(id)}
                      className="text-xs text-[var(--theme-accent)] font-bold hover:underline flex items-center gap-1 cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>ลบออก</span>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Advisors Bookmarks */}
          <div className="space-y-2 pt-4 border-t border-[var(--theme-border)]">
            <h4 className="text-xs font-bold text-[var(--theme-text-title)] uppercase tracking-wider">
              อาจารย์ที่ปรึกษาที่บันทึก ({savedAdvisors.length})
            </h4>
            {savedAdvisors.length === 0 ? (
              <p className="text-xs text-[var(--theme-text-muted)] italic bg-[var(--theme-card-subtle)] p-3 rounded-xl">
                ยังไม่มีอาจารย์ที่บันทึกไว้
              </p>
            ) : (
              <div className="space-y-2">
                {savedAdvisors.map((id) => (
                  <div
                    key={id}
                    className="p-3 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] flex items-center justify-between"
                  >
                    <span className="text-xs font-semibold text-[var(--theme-text-title)]">รหัสอาจารย์: {id}</span>
                    <button
                      onClick={() => onRemoveAdvisor(id)}
                      className="text-xs text-[var(--theme-accent)] font-bold hover:underline flex items-center gap-1 cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>ลบออก</span>
                    </button>
                  </div>
                ))}
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

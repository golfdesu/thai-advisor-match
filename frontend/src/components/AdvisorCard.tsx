"use client";

import React, { useState } from "react";
import Link from "next/link";
import { SearchMatchResult, FacultyMember } from "@/types";
import { getAdvisorAvatarUrl } from "@/lib/config";
import {
  Building2,
  Mail,
  Heart,
  BookOpen,
  ArrowUpRight,
  Sparkles,
  FileText,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Award,
  GraduationCap
} from "lucide-react";

interface AdvisorCardProps {
  matchItem: SearchMatchResult;
  isSaved: boolean;
  onToggleBookmark: (id: string) => void;
  onOpenColdEmail: (advisor: FacultyMember) => void;
}

export const AdvisorCard: React.FC<AdvisorCardProps> = ({
  matchItem,
  isSaved,
  onToggleBookmark,
  onOpenColdEmail,
}) => {
  const f = matchItem.faculty;
  const matchScore = matchItem.match_score;
  const [showSynergyDetails, setShowSynergyDetails] = useState(false);

  const hasSynergyBadges = matchItem.synergy_badges && matchItem.synergy_badges.length > 0;
  const hasMatchingPubs = matchItem.matching_publications && matchItem.matching_publications.length > 0;
  const hasSuggestedAngles = matchItem.suggested_thesis_angles && matchItem.suggested_thesis_angles.length > 0;
  const hasExtendedInsights = hasMatchingPubs || hasSuggestedAngles;

  return (
    <div className="group relative p-5 sm:p-6 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] hover:border-[var(--theme-primary)] transition-all duration-200 flex flex-col justify-between hover:shadow-md">
      <div className="space-y-4">
        {/* Top Header Avatar & Title */}
        <div className="flex items-start justify-between gap-3">
          <Link
            href={`/advisor/${f.id}`}
            className="flex items-center gap-3.5 flex-1 min-w-0 hover:opacity-95 transition group/avatar"
          >
            <div className="relative flex-shrink-0">
              <img
                src={f.image_url || getAdvisorAvatarUrl(f.full_name_th || f.full_name || f.first_name)}
                alt={f.full_name_th}
                loading="lazy"
                decoding="async"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = getAdvisorAvatarUrl(f.full_name_th || f.full_name || f.first_name);
                }}
                className="w-16 h-16 rounded-2xl object-cover border-2 border-[var(--theme-border)] bg-[var(--theme-card-subtle)] group-hover/avatar:border-[var(--theme-primary)] group-hover/avatar:scale-105 transition-all shadow-xs"
              />
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-lg bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center text-xs shadow-xs">
                <GraduationCap className="w-3.5 h-3.5" />
              </div>
            </div>
            <div className="min-w-0">
              <span className="text-xs font-bold text-[var(--theme-primary)] block truncate">
                {f.academic_title_th || "อาจารย์"}
              </span>
              <h3 className="text-base sm:text-lg font-black text-[var(--theme-text-title)] group-hover:text-[var(--theme-primary)] transition-colors leading-snug truncate">
                {f.full_name_th || `${f.first_name} ${f.last_name}`}
              </h3>
              <p className="text-xs text-[var(--theme-text-muted)] font-semibold truncate mt-0.5">
                {f.university_th}
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-2 flex-shrink-0">
            {matchScore !== undefined && (
              <span
                className={`px-3 py-1 rounded-xl text-xs font-black border shadow-2xs ${
                  matchScore >= 85
                    ? "bg-[var(--theme-primary-subtle)] border-[var(--theme-primary-border)] text-[var(--theme-primary)]"
                    : matchScore >= 70
                    ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)]"
                    : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)]"
                }`}
                title="ระดับความตรงสายงานวิจัย (คำนวณจาก AI Vector + Publications + Research Focus)"
              >
                ตรงสาย {Math.round(matchScore)}%
              </span>
            )}

            <button
              onClick={() => onToggleBookmark(f.id)}
              className={`p-2 rounded-xl border text-xs transition-all cursor-pointer ${
                isSaved
                  ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)] shadow-xs"
                  : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-accent)] hover:border-[var(--theme-accent)]"
              }`}
              title="บันทึกรายชื่ออาจารย์"
            >
              <Heart className={`w-4 h-4 ${isSaved ? "fill-[var(--theme-accent)]" : ""}`} />
            </button>
          </div>
        </div>

        {/* Affiliation Info */}
        <div className="text-xs sm:text-sm text-[var(--theme-text-body)] font-medium flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[var(--theme-primary-subtle)] flex items-center justify-center text-[var(--theme-primary)] shrink-0">
            <Building2 className="w-3.5 h-3.5" />
          </div>
          <span className="truncate">
            {f.faculty_th} {f.department_th ? `• ${f.department_th}` : ""}
          </span>
        </div>

        {/* Synergy Badges */}
        {hasSynergyBadges && (
          <div className="flex flex-wrap gap-2">
            {matchItem.synergy_badges!.map((badge, idx) => (
              <span
                key={idx}
                className="px-3 py-1 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-xs font-bold text-[var(--theme-text-title)] leading-tight shadow-2xs"
              >
                {badge}
              </span>
            ))}
          </div>
        )}

        {/* Research Expertise Tags */}
        <div className="space-y-1.5">
          <span className="text-xs uppercase font-black tracking-wider text-[var(--theme-text-muted)]">
            ความเชี่ยวชาญทางวิชาการ:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {f.research_interests && f.research_interests.length > 0 ? (
              f.research_interests.slice(0, 3).map((interest, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-xl bg-[var(--theme-card-subtle)]/80 border border-[var(--theme-border)] text-xs font-semibold text-[var(--theme-text-body)] leading-tight hover:border-[var(--theme-primary)] transition-colors"
                >
                  {interest}
                </span>
              ))
            ) : (
              <span className="text-xs text-[var(--theme-text-muted)] font-medium">งานวิจัยและวิทยานิพนธ์</span>
            )}
          </div>
        </div>

        {/* Contextual Alignment Box */}
        {matchItem.ai_explanation && (
          <div className="p-4 rounded-2xl bg-[var(--theme-card-subtle)]/80 border border-[var(--theme-border)] text-xs sm:text-sm text-[var(--theme-text-body)] leading-relaxed">
            <div className="flex items-center justify-between mb-2">
              <span className="font-black text-[var(--theme-text-title)] flex items-center gap-1.5 text-xs sm:text-sm">
                <Sparkles className="w-4 h-4 text-[var(--theme-primary)] animate-pulse" />
                ความสอดคล้องกับงานวิจัยของคุณ:
              </span>
              {hasExtendedInsights && (
                <button
                  type="button"
                  onClick={() => setShowSynergyDetails(!showSynergyDetails)}
                  className="text-xs font-extrabold text-[var(--theme-primary)] hover:underline flex items-center gap-0.5 cursor-pointer"
                >
                  <span>{showSynergyDetails ? "ซ่อนรายละเอียด" : "ดูจุดเชื่อมโยง"}</span>
                  {showSynergyDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              )}
            </div>
            <p className="text-xs sm:text-sm leading-relaxed text-[var(--theme-text-body)] font-normal">{matchItem.ai_explanation}</p>

            {/* Collapsible Deep Synergy Insights */}
            {showSynergyDetails && hasExtendedInsights && (
              <div className="mt-3 pt-3 border-t border-[var(--theme-border)] space-y-3 text-xs">
                {hasMatchingPubs && (
                  <div>
                    <span className="font-bold text-[var(--theme-text-title)] flex items-center gap-1 mb-1 text-xs uppercase">
                      <FileText className="w-3.5 h-3.5 text-[var(--theme-primary)]" /> ผลงานตีพิมพ์ที่สอดคล้อง:
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-[var(--theme-text-muted)] pl-1 text-xs">
                      {matchItem.matching_publications!.map((pub, idx) => (
                        <li key={idx} className="line-clamp-1 italic">
                          &ldquo;{pub}&rdquo;
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {hasSuggestedAngles && (
                  <div>
                    <span className="font-bold text-[var(--theme-text-title)] flex items-center gap-1 mb-1 text-xs uppercase">
                      <Lightbulb className="w-3.5 h-3.5 text-[var(--theme-accent)]" /> ข้อเสนอแนะแนวทางวิทยานิพนธ์:
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-[var(--theme-text-muted)] pl-1 text-xs">
                      {matchItem.suggested_thesis_angles!.map((angle, idx) => (
                        <li key={idx}>{angle}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="pt-4 mt-4 border-t border-[var(--theme-border)] flex items-center justify-between gap-2">
        <Link
          href={`/advisor/${f.id}`}
          className="text-xs sm:text-sm font-bold text-[var(--theme-text-muted)] hover:text-[var(--theme-primary)] transition-colors flex items-center gap-1 group/link"
        >
          <span>ดูประวัติ & ผลงาน</span>
          <ArrowUpRight className="w-4 h-4 group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5 transition-transform" />
        </Link>

        <button
          onClick={() => onOpenColdEmail(f)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold transition cursor-pointer"
        >
          <Mail className="w-4 h-4" />
          <span>ร่างอีเมล AI</span>
        </button>
      </div>
    </div>
  );
};

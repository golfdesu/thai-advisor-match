"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import type { SearchMatchResult } from "@/types";
import { getAdvisorAvatarUrl } from "@/lib/config";
import {
  Building2,
  Heart,
  ArrowUpRight,
  Sparkles,
  FileText,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  GraduationCap,
  Award
} from "lucide-react";

interface AdvisorCardProps {
  matchItem: SearchMatchResult;
  isSaved: boolean;
  onToggleBookmark: (id: string) => void;
}

export const AdvisorCard: React.FC<AdvisorCardProps> = ({
  matchItem,
  isSaved,
  onToggleBookmark,
}) => {
  const f = matchItem.faculty;
  const matchScore = matchItem.match_score;
  const [showSynergyDetails, setShowSynergyDetails] = useState(false);
  const [imgSrc, setImgSrc] = useState(
    f.image_url || getAdvisorAvatarUrl(f.full_name_th || f.full_name || f.first_name)
  );

  const hasSynergyBadges = matchItem.synergy_badges && matchItem.synergy_badges.length > 0;
  const hasMatchingPubs = matchItem.matching_publications && matchItem.matching_publications.length > 0;
  const hasSuggestedAngles = matchItem.suggested_thesis_angles && matchItem.suggested_thesis_angles.length > 0;
  const hasExtendedInsights = hasMatchingPubs || hasSuggestedAngles;

  return (
    <div className="ui-card group relative p-5 sm:p-6 flex flex-col justify-between">
      <div className="space-y-3.5">
        {/* Top Header Meta: Match Score & Bookmark */}
        <div className="flex items-center justify-between gap-3">
          {matchScore !== undefined ? (
            <div className="flex items-center gap-2 min-w-0">
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-black border shadow-2xs truncate ${
                  matchScore >= 85
                    ? "bg-[var(--theme-primary-subtle)] border-[var(--theme-primary-border)] text-[var(--theme-primary)]"
                    : matchScore >= 70
                    ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)]"
                    : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)]"
                }`}
                title="ระดับความตรงสายงานวิจัย (คำนวณจาก AI Vector + Publications + Research Focus)"
              >
                {matchItem.match_tier_label ? `${matchItem.match_tier_label} • ` : "ตรงสาย "}
                {Math.round(matchScore)}%
              </span>
            </div>
          ) : (
            <div />
          )}

          <button
            onClick={() => onToggleBookmark(f.id)}
            aria-label={isSaved ? "ยกเลิกบันทึกรายชื่ออาจารย์" : "บันทึกรายชื่ออาจารย์"}
            className={`p-2 rounded-xl border text-xs transition-all cursor-pointer shrink-0 ${
              isSaved
                ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)] shadow-xs"
                : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-accent)] hover:border-[var(--theme-accent)]"
            }`}
            title="บันทึกรายชื่ออาจารย์"
          >
            <Heart className={`w-4 h-4 ${isSaved ? "fill-[var(--theme-accent)]" : ""}`} />
          </button>
        </div>

        {/* Profile Hero Section */}
        <Link
          href={`/advisor/${f.id}`}
          className="flex items-start gap-3.5 hover:opacity-95 transition group/avatar"
        >
          <div className="relative flex-shrink-0 w-14 h-14 sm:w-16 sm:h-16">
            <Image
              src={imgSrc}
              alt={f.full_name_th || f.full_name || "รูปภาพอาจารย์"}
              width={64}
              height={64}
              loading="lazy"
              decoding="async"
              unoptimized
              onError={() => {
                setImgSrc(getAdvisorAvatarUrl(f.full_name_th || f.full_name || f.first_name));
              }}
              className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl object-cover border-2 border-[var(--theme-border)] bg-[var(--theme-card-subtle)] group-hover/avatar:border-[var(--theme-primary)] group-hover/avatar:scale-105 transition-all shadow-xs"
            />
            <div className="absolute -bottom-1 -right-1 w-5 h-5 sm:w-6 sm:h-6 rounded-lg bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center text-[10px] sm:text-xs shadow-xs">
              <GraduationCap className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs font-bold text-[var(--theme-primary)]">
                {f.academic_title_th || "อาจารย์"}
              </span>
              {((f.h_index !== undefined && f.h_index >= 20) || ((f.total_citations || 0) >= 1000)) && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-black bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 shrink-0">
                  <Award className="w-2.5 h-2.5 text-amber-500" />
                  นักวิจัยแนวหน้า
                </span>
              )}
              {(f.has_research_lab || (f.research_labs && f.research_labs.length > 0)) && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-black bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 shrink-0">
                  <Building2 className="w-2.5 h-2.5 text-emerald-600 dark:text-emerald-400" />
                  ศูนย์วิจัย
                </span>
              )}
            </div>

            <h3 className="text-base sm:text-lg font-black text-[var(--theme-text-title)] group-hover:text-[var(--theme-primary)] transition-colors leading-snug line-clamp-1 mt-0.5">
              {f.full_name_th || `${f.first_name} ${f.last_name}`}
            </h3>

            {/* Combined Affiliation */}
            <p className="text-xs text-[var(--theme-text-muted)] font-medium line-clamp-1 mt-0.5">
              {f.university_th}
              {f.faculty_th ? ` • ${f.faculty_th}` : ""}
              {f.department_th && f.department_th !== "ระบุไม่ได้" ? ` • ${f.department_th}` : ""}
            </p>

            {/* Research Stats */}
            <div className="flex flex-wrap items-center gap-2 mt-1.5 text-[11px] font-semibold text-[var(--theme-text-muted)]">
              {f.total_publications_count !== undefined && f.total_publications_count > 0 && (
                <span className="font-bold text-[var(--theme-primary)]">
                  {f.total_publications_count} ผลงาน
                </span>
              )}
              {f.h_index !== undefined && f.h_index > 0 && (
                <span className="px-1.5 py-0.5 rounded-md bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[10px] font-bold text-[var(--theme-text-title)]" title="ดัชนี h-index">
                  h-index {f.h_index}
                </span>
              )}
              {f.total_citations !== undefined && f.total_citations > 0 && (
                <span className="text-[10px] text-[var(--theme-text-muted)]" title="จำนวนการอ้างอิงทั้งหมด">
                  {f.total_citations.toLocaleString()} citations
                </span>
              )}
            </div>
          </div>
        </Link>

        {/* Research Lab Affiliation */}
        {f.research_labs && f.research_labs.length > 0 ? (
          <div className="flex items-center gap-1.5 flex-wrap">
            {f.research_labs.slice(0, 1).map((lab) => (
              <Link
                key={lab.id}
                href={`/labs/${lab.id}`}
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 hover:border-emerald-500/40 transition hover:underline"
                title={`เข้าชมห้องปฏิบัติการ: ${lab.name_th}`}
              >
                <Building2 className="w-3 h-3 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span className="truncate max-w-[240px]">
                  {lab.is_lead ? `Lab Director: ${lab.name_th}` : lab.name_th}
                </span>
                <ArrowUpRight className="w-3 h-3 shrink-0 opacity-70" />
              </Link>
            ))}
            {f.research_labs.length > 1 && (
              <span className="text-[10px] font-bold text-[var(--theme-text-muted)]">
                +{f.research_labs.length - 1} ศูนย์
              </span>
            )}
          </div>
        ) : f.has_research_lab ? (
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
              <Building2 className="w-3 h-3 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span>ประจำห้องปฏิบัติการวิจัยเฉพาะทาง</span>
            </span>
          </div>
        ) : null}

        {/* Synergy Badges */}
        {hasSynergyBadges && (
          <div className="flex flex-wrap gap-1.5">
            {matchItem.synergy_badges!.slice(0, 2).map((badge, idx) => (
              <span
                key={idx}
                className="px-2.5 py-0.5 rounded-lg bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[11px] font-semibold text-[var(--theme-text-title)] leading-tight shadow-2xs"
              >
                {badge}
              </span>
            ))}
          </div>
        )}

        {/* Research Expertise Tags */}
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--theme-text-muted)]">
            ความเชี่ยวชาญทางวิชาการ:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {f.research_interests && f.research_interests.length > 0 ? (
              f.research_interests.slice(0, 3).map((interest, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-lg bg-[var(--theme-card-subtle)]/80 border border-[var(--theme-border)] text-[11px] font-medium text-[var(--theme-text-body)] leading-tight line-clamp-1 hover:border-[var(--theme-primary)] transition-colors"
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
          <div className="p-3.5 rounded-xl bg-[var(--theme-card-subtle)]/80 border border-[var(--theme-border)] text-xs text-[var(--theme-text-body)] leading-relaxed">
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-bold text-[var(--theme-text-title)] flex items-center gap-1.5 text-xs">
                <Sparkles className="w-3.5 h-3.5 text-[var(--theme-primary)] animate-pulse shrink-0" />
                ความสอดคล้องกับงานวิจัยของคุณ:
              </span>
              {hasExtendedInsights && (
                <button
                  type="button"
                  onClick={() => setShowSynergyDetails(!showSynergyDetails)}
                  aria-expanded={showSynergyDetails}
                  aria-label={showSynergyDetails ? "ซ่อนรายละเอียดความสอดคล้อง" : "แสดงรายละเอียดความสอดคล้อง"}
                  className="text-[11px] font-extrabold text-[var(--theme-primary)] hover:underline flex items-center gap-0.5 cursor-pointer shrink-0"
                >
                  <span>{showSynergyDetails ? "ซ่อน" : "ดูจุดเชื่อมโยง"}</span>
                  {showSynergyDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
              )}
            </div>
            <p className="text-xs leading-relaxed text-[var(--theme-text-body)] font-normal line-clamp-3">
              {matchItem.ai_explanation}
            </p>

            {/* Collapsible Deep Synergy Insights */}
            {showSynergyDetails && hasExtendedInsights && (
              <div className="mt-2.5 pt-2.5 border-t border-[var(--theme-border)] space-y-2 text-xs">
                {hasMatchingPubs && (
                  <div>
                    <span className="font-bold text-[var(--theme-text-title)] flex items-center gap-1 mb-1 text-[11px] uppercase">
                      <FileText className="w-3 h-3 text-[var(--theme-primary)]" /> ผลงานตีพิมพ์ที่สอดคล้อง:
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-[var(--theme-text-muted)] pl-1 text-[11px]">
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
                    <span className="font-bold text-[var(--theme-text-title)] flex items-center gap-1 mb-1 text-[11px] uppercase">
                      <Lightbulb className="w-3 h-3 text-[var(--theme-accent)]" /> ข้อเสนอแนะแนวทางวิทยานิพนธ์:
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-[var(--theme-text-muted)] pl-1 text-[11px]">
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
      <div className="pt-3 mt-3 border-t border-[var(--theme-border)] flex items-center justify-between gap-2">
        <Link
          href={`/advisor/${f.id}`}
          className="text-xs font-bold text-[var(--theme-text-muted)] hover:text-[var(--theme-primary)] transition-colors flex items-center gap-1 group/link"
        >
          <span>ดูประวัติ & ผลงาน</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5 transition-transform" />
        </Link>

        {f.research_labs && f.research_labs.length > 0 && (
          <Link
            href={`/labs/${f.research_labs[0].id}`}
            onClick={(e) => e.stopPropagation()}
            className="text-xs font-bold text-emerald-700 dark:text-emerald-400 hover:underline flex items-center gap-1"
          >
            <span>ห้องปฏิบัติการวิจัย</span>
            <ArrowUpRight className="w-3 h-3" />
          </Link>
        )}
      </div>
    </div>
  );
};

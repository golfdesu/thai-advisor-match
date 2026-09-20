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
      <div className="space-y-4">
        {/* Top Header Avatar & Title */}
        <div className="flex items-start justify-between gap-3">
          <Link
            href={`/advisor/${f.id}`}
            className="flex items-center gap-3.5 flex-1 min-w-0 hover:opacity-95 transition group/avatar"
          >
            <div className="relative flex-shrink-0 w-16 h-16">
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
                className="w-16 h-16 rounded-2xl object-cover border-2 border-[var(--theme-border)] bg-[var(--theme-card-subtle)] group-hover/avatar:border-[var(--theme-primary)] group-hover/avatar:scale-105 transition-all shadow-xs"
              />
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-lg bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center text-xs shadow-xs">
                <GraduationCap className="w-3.5 h-3.5" />
              </div>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-xs font-bold text-[var(--theme-primary)] block truncate">
                  {f.academic_title_th || "อาจารย์"}
                </span>
                {((f.h_index !== undefined && f.h_index >= 20) || ((f.total_citations || 0) >= 1000)) && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-black bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 shrink-0 shadow-2xs">
                    <Award className="w-3 h-3 text-amber-500" />
                    นักวิจัยแนวหน้า
                  </span>
                )}
                {(f.has_research_lab || (f.research_labs && f.research_labs.length > 0)) && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-black bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 shrink-0 shadow-2xs">
                    <Building2 className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                    ศูนย์วิจัย
                  </span>
                )}
              </div>
              <h3 className="text-base sm:text-lg font-black text-[var(--theme-text-title)] group-hover:text-[var(--theme-primary)] transition-colors leading-snug truncate">
                {f.full_name_th || `${f.first_name} ${f.last_name}`}
              </h3>
              <p className="text-xs text-[var(--theme-text-muted)] font-semibold truncate mt-0.5">
                {f.university_th}
              </p>
              <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] font-semibold text-[var(--theme-text-muted)]">
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
                {matchItem.match_tier_label ? `${matchItem.match_tier_label} • ` : "ตรงสาย "}
                {Math.round(matchScore)}%
              </span>
            )}

            <button
              onClick={() => onToggleBookmark(f.id)}
              aria-label={isSaved ? "ยกเลิกบันทึกรายชื่ออาจารย์" : "บันทึกรายชื่ออาจารย์"}
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

        {/* Research Lab Affiliation */}
        {f.research_labs && f.research_labs.length > 0 ? (
          <div className="flex items-center gap-1.5 flex-wrap">
            {f.research_labs.slice(0, 1).map((lab) => (
              <Link
                key={lab.id}
                href={`/labs/${lab.id}`}
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[11px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 hover:border-emerald-500/40 transition hover:underline"
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
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[11px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
              <Building2 className="w-3 h-3 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span>ประจำห้องปฏิบัติการวิจัยเฉพาะทาง</span>
            </span>
          </div>
        ) : null}

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
                  aria-expanded={showSynergyDetails}
                  aria-label={showSynergyDetails ? "ซ่อนรายละเอียดความสอดคล้อง" : "แสดงรายละเอียดความสอดคล้อง"}
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

        {f.research_labs && f.research_labs.length > 0 && (
          <Link
            href={`/labs/${f.research_labs[0].id}`}
            onClick={(e) => e.stopPropagation()}
            className="text-xs font-bold text-emerald-700 dark:text-emerald-400 hover:underline flex items-center gap-1"
          >
            <span>ห้องปฏิบัติการวิจัย</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        )}
      </div>
    </div>
  );
};

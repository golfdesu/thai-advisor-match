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
  ChevronUp
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
    <div className="group relative p-5 sm:p-6 rounded-2xl bg-white border border-stone-200/90 hover:border-[#5B0F18]/40 transition-all flex flex-col justify-between hover:shadow-md">
      <div className="space-y-4">
        {/* Top Header Avatar & Title */}
        <div className="flex items-start justify-between gap-3">
          <Link
            href={`/advisor/${f.id}`}
            className="flex items-center gap-3.5 flex-1 min-w-0 hover:opacity-90 transition group/avatar"
          >
            <img
              src={f.image_url || getAdvisorAvatarUrl(f.first_name)}
              alt={f.full_name_th}
              loading="lazy"
              decoding="async"
              onError={(e) => {
                (e.target as HTMLImageElement).src = getAdvisorAvatarUrl(f.first_name);
              }}
              className="w-13 h-13 rounded-2xl object-cover border border-stone-200 bg-stone-100 flex-shrink-0 group-hover/avatar:scale-102 transition-transform"
            />
            <div className="min-w-0">
              <span className="text-[11px] font-semibold text-[#5B0F18] block truncate">
                {f.academic_title_th || "อาจารย์"}
              </span>
              <h3 className="text-base font-bold text-stone-900 group-hover:text-[#5B0F18] transition-colors leading-snug truncate">
                {f.full_name_th || `${f.first_name} ${f.last_name}`}
              </h3>
              <p className="text-[11px] text-stone-500 truncate mt-0.5">
                {f.university_th}
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            {matchScore !== undefined && (
              <span
                className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${
                  matchScore >= 85
                    ? "bg-rose-50 border-rose-200 text-[#5B0F18]"
                    : matchScore >= 70
                    ? "bg-amber-50 border-amber-200 text-amber-900"
                    : "bg-stone-50 border-stone-200 text-stone-700"
                }`}
                title="ระดับความตรงสายงานวิจัย (คำนวณจาก AI Vector + Publications + Research Focus)"
              >
                ตรงสาย {Math.round(matchScore)}%
              </span>
            )}

            <button
              onClick={() => onToggleBookmark(f.id)}
              className={`p-1.5 rounded-lg border text-xs transition-all cursor-pointer ${
                isSaved
                  ? "bg-rose-50 border-rose-200 text-[#5B0F18]"
                  : "bg-stone-50 border-stone-200 text-stone-500 hover:text-stone-900"
              }`}
              title="บันทึกรายชื่ออาจารย์"
            >
              <Heart className={`w-3.5 h-3.5 ${isSaved ? "fill-[#5B0F18]" : ""}`} />
            </button>
          </div>
        </div>

        {/* Affiliation Info */}
        <div className="text-xs text-stone-600 flex items-center gap-1.5">
          <Building2 className="w-3.5 h-3.5 text-stone-400 flex-shrink-0" />
          <span className="truncate">
            {f.faculty_th} {f.department_th ? `• ${f.department_th}` : ""}
          </span>
        </div>

        {/* Synergy Badges */}
        {hasSynergyBadges && (
          <div className="flex flex-wrap gap-1.5">
            {matchItem.synergy_badges!.map((badge, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded-md bg-stone-50 border border-stone-200/80 text-[10px] font-semibold text-stone-700 leading-tight"
              >
                {badge}
              </span>
            ))}
          </div>
        )}

        {/* Research Expertise Tags */}
        <div className="space-y-1.5">
          <span className="text-[10px] uppercase font-bold tracking-wider text-stone-500">
            ความเชี่ยวชาญทางวิชาการ:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {f.research_interests && f.research_interests.length > 0 ? (
              f.research_interests.slice(0, 3).map((interest, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md bg-stone-100/80 border border-stone-200 text-[11px] text-stone-700 font-medium leading-tight"
                >
                  {interest}
                </span>
              ))
            ) : (
              <span className="text-xs text-stone-400">งานวิจัยและวิทยานิพนธ์</span>
            )}
          </div>
        </div>

        {/* Contextual Alignment Box */}
        {matchItem.ai_explanation && (
          <div className="p-3 rounded-xl bg-stone-50/90 border border-stone-200/90 text-xs text-stone-700 leading-relaxed">
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-stone-900 flex items-center gap-1.5 text-[11px]">
                <Sparkles className="w-3.5 h-3.5 text-[#5B0F18]" />
                ความสอดคล้องกับงานวิจัยของคุณ:
              </span>
              {hasExtendedInsights && (
                <button
                  type="button"
                  onClick={() => setShowSynergyDetails(!showSynergyDetails)}
                  className="text-[10px] font-bold text-[#5B0F18] hover:underline flex items-center gap-0.5 cursor-pointer"
                >
                  <span>{showSynergyDetails ? "ซ่อนรายละเอียด" : "ดูจุดเชื่อมโยง"}</span>
                  {showSynergyDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
              )}
            </div>
            <p className="text-[11px] leading-relaxed text-stone-700">{matchItem.ai_explanation}</p>

            {/* Collapsible Deep Synergy Insights */}
            {showSynergyDetails && hasExtendedInsights && (
              <div className="mt-2.5 pt-2.5 border-t border-stone-200/80 space-y-2 text-[11px]">
                {hasMatchingPubs && (
                  <div>
                    <span className="font-semibold text-stone-800 flex items-center gap-1 mb-1">
                      <FileText className="w-3 h-3 text-[#5B0F18]" /> ผลงานตีพิมพ์ที่สอดคล้อง:
                    </span>
                    <ul className="list-disc list-inside space-y-0.5 text-stone-600 pl-1">
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
                    <span className="font-semibold text-stone-800 flex items-center gap-1 mb-1">
                      <Lightbulb className="w-3 h-3 text-amber-600" /> ข้อเสนอแนะแนวทางวิทยานิพนธ์:
                    </span>
                    <ul className="list-disc list-inside space-y-0.5 text-stone-600 pl-1">
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
      <div className="pt-4 mt-4 border-t border-stone-100 flex items-center justify-between gap-2">
        <Link
          href={`/advisor/${f.id}`}
          className="text-xs font-bold text-stone-600 hover:text-[#5B0F18] transition-colors flex items-center gap-1"
        >
          <span>ดูประวัติและผลงานวิจัย</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>

        <button
          onClick={() => onOpenColdEmail(f)}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          <Mail className="w-3.5 h-3.5" />
          <span>ร่างอีเมลติดต่อ</span>
        </button>
      </div>
    </div>
  );
};

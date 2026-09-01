"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Building2,
  Sparkles,
  Users,
  Wrench,
  ChevronRight,
  Send,
  Award
} from "lucide-react";
import type { ResearchLab } from "@/types";
import { LabInquiryModal } from "./LabInquiryModal";

interface LabCardProps {
  lab: ResearchLab;
  onOpenInquiry?: (lab: ResearchLab) => void;
}

export const LabCard: React.FC<LabCardProps> = ({ lab, onOpenInquiry }) => {
  const [showInquiryModal, setShowInquiryModal] = useState(false);
  const [labImgError, setLabImgError] = useState(false);
  const [piImgError, setPiImgError] = useState(false);

  const handleInquiryClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onOpenInquiry) {
      onOpenInquiry(lab);
    } else {
      setShowInquiryModal(true);
    }
  };

  return (
    <>
      <div className="group relative bg-[var(--theme-card)] rounded-2xl border border-[var(--theme-border)] hover:border-[var(--theme-primary)] hover:shadow-lg transition-all duration-200 flex flex-col justify-between overflow-hidden">
        {/* Top Banner Image with Gradient Overlay */}
        <div className="relative h-44 w-full overflow-hidden bg-[var(--theme-card-subtle)] border-b border-[var(--theme-border)]">
          {lab.image_url && !labImgError ? (
            <Image
              src={lab.image_url}
              alt={lab.name_th || lab.name_en || "รูปภาพห้องปฏิบัติการวิจัย"}
              fill
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
              loading="lazy"
              decoding="async"
              unoptimized
              className="object-cover group-hover:scale-105 transition-transform duration-500"
              onError={() => {
                setLabImgError(true);
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)]">
              <Building2 className="w-12 h-12 opacity-60" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent pointer-events-none" />

          {/* Match Score Badge */}
          {lab.match_score !== undefined && (
            <div className="absolute top-3 right-3 px-3 py-1 rounded-full bg-emerald-500/90 text-white font-black text-xs flex items-center gap-1 shadow-md backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5" />
              <span>{lab.match_score.toFixed(0)}% Match</span>
            </div>
          )}

          {/* University Tag Overlay */}
          <div className="absolute bottom-3 left-4 right-4">
            <div className="flex items-center gap-1.5 text-xs font-bold text-white/90 drop-shadow-sm">
              <Building2 className="w-3.5 h-3.5 text-[var(--theme-accent)]" />
              <span className="truncate">{lab.university_th}</span>
            </div>
            <h3 className="text-base sm:text-lg font-black text-white line-clamp-1 mt-0.5 drop-shadow-md">
              {lab.name_th}
            </h3>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            {/* English Title & Faculty */}
            <div>
              <div className="text-xs font-semibold text-[var(--theme-primary)] tracking-wide line-clamp-1">
                {lab.name_en}
              </div>
              <div className="text-xs text-[var(--theme-text-muted)] mt-0.5">
                {lab.faculty_th} {lab.department_th ? `• ${lab.department_th}` : ""}
              </div>
            </div>

            {/* AI Explanation Banner if Available */}
            {lab.ai_explanation && (
              <div className="p-2.5 rounded-xl bg-[var(--theme-accent-subtle)] border border-[var(--theme-accent-border)] text-xs text-[var(--theme-text-body)]">
                <div className="flex items-center gap-1 font-bold text-[var(--theme-accent)] mb-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>ความสอดคล้องกับแนวคิดวิจัย:</span>
                </div>
                <p className="line-clamp-2 leading-relaxed text-[var(--theme-text-muted)]">
                  {lab.ai_explanation}
                </p>
              </div>
            )}

            {/* Description */}
            {lab.description && !lab.ai_explanation && (
              <p className="text-xs text-[var(--theme-text-muted)] line-clamp-2 leading-relaxed">
                {lab.description}
              </p>
            )}

            {/* Synergy Badges */}
            {lab.synergy_badges && lab.synergy_badges.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {lab.synergy_badges.map((badge, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)] border border-[var(--theme-primary-border)]"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            )}

            {/* Research Domains Chips */}
            {lab.research_domains && lab.research_domains.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <div className="text-xs font-bold text-[var(--theme-text-muted)] flex items-center gap-1">
                  <Award className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
                  <span>สาขาความเชี่ยวชาญหลัก:</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {lab.research_domains.slice(0, 3).map((domain, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md text-xs font-medium bg-[var(--theme-card-subtle)] text-[var(--theme-text-body)] border border-[var(--theme-border)]"
                    >
                      {domain}
                    </span>
                  ))}
                  {lab.research_domains.length > 3 && (
                    <span className="px-1.5 py-0.5 rounded-md text-xs text-[var(--theme-text-muted)]">
                      +{lab.research_domains.length - 3}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Flagship Equipment Highlights */}
            {lab.flagship_equipment && lab.flagship_equipment.length > 0 && (
              <div className="pt-2 border-t border-[var(--theme-border-subtle)]">
                <div className="text-xs text-[var(--theme-text-muted)] flex items-center gap-1 font-semibold">
                  <Wrench className="w-3 h-3 text-[var(--theme-accent)]" />
                  <span className="truncate">
                    เครื่องมือวิจัย: {lab.flagship_equipment[0]}
                  </span>
                </div>
              </div>
            )}

            {/* Lead Advisor PI */}
            {lab.lead_advisor && (
              <div className="pt-2 flex items-center gap-2.5">
                <div className="relative w-7 h-7 rounded-full bg-[var(--theme-primary-subtle)] border border-[var(--theme-primary-border)] flex items-center justify-center text-xs font-bold text-[var(--theme-primary)] shrink-0 overflow-hidden">
                  {lab.lead_advisor.image_url && !piImgError ? (
                    <Image
                      src={lab.lead_advisor.image_url}
                      alt={lab.lead_advisor.full_name_th || "รูปหัวหน้าห้องปฏิบัติการ"}
                      width={28}
                      height={28}
                      loading="lazy"
                      decoding="async"
                      unoptimized
                      className="w-full h-full object-cover"
                      onError={() => { setPiImgError(true); }}
                    />
                  ) : (
                    <Users className="w-3.5 h-3.5" />
                  )}
                </div>
                <div className="text-xs truncate">
                  <span className="font-bold text-[var(--theme-text-body)]">หัวหน้าห้องปฏิบัติการ (PI):</span>{" "}
                  <Link
                    href={`/advisor/${lab.lead_advisor.id}`}
                    className="text-[var(--theme-primary)] hover:underline font-semibold"
                  >
                    {lab.lead_advisor.full_name_th}
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="pt-4 border-t border-[var(--theme-border)] flex items-center justify-between gap-2">
            <Link
              href={`/labs/${lab.id}`}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-xl bg-[var(--theme-card-subtle)] hover:bg-[var(--theme-card)] text-xs font-bold text-[var(--theme-text-body)] border border-[var(--theme-border)] hover:border-[var(--theme-primary)] transition-all cursor-pointer group"
            >
              <span>ดูข้อมูลห้องวิจัย</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>

            <button
              onClick={handleInquiryClick}
              className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-xl bg-[var(--theme-primary)] hover:opacity-90 text-[var(--theme-primary-contrast)] text-xs font-bold shadow-xs transition-all cursor-pointer"
              title="สร้างข้อความติดต่อสมัครเข้าร่วมแล็บด้วย AI"
            >
              <Send className="w-3.5 h-3.5" />
              <span>ติดต่อแล็บ (AI)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Embedded Modal if used independently */}
      {showInquiryModal && (
        <LabInquiryModal lab={lab} onClose={() => setShowInquiryModal(false)} />
      )}
    </>
  );
};

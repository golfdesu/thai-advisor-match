"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  Building2,
  Users,
  Wrench,
  Briefcase,
  ExternalLink,
  Award,
  Sparkles,
  Loader2,
  AlertCircle,
  Bookmark,
  Share2,
  CheckCircle2,
  Globe,
  Send,
  Check,
  ChevronRight
} from "lucide-react";
import type { ResearchLab } from "@/types";
import { API_BASE_URL } from "@/lib/config";
import { labDetailCache } from "@/lib/dsa";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { LabInquiryModal } from "@/components/LabInquiryModal";

const hasSavedId = (storageKey: string, id: string): boolean => {
  if (typeof window === "undefined") return false;

  try {
    const saved = window.localStorage.getItem(storageKey);
    const parsed: unknown = saved ? JSON.parse(saved) : [];
    return Array.isArray(parsed) && parsed.includes(id);
  } catch {
    return false;
  }
};

export default function LabDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [lab, setLab] = useState<ResearchLab | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState(() => hasSavedId("thai_educenter_saved_labs", id));
  const [showInquiryModal, setShowInquiryModal] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [heroImgError, setHeroImgError] = useState(false);
  const [piImgError, setPiImgError] = useState(false);
  const [memberImgErrors, setMemberImgErrors] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!id) return;

    // Check client O(1) LRU Cache first
    const cachedLab = labDetailCache.get(id);
    if (cachedLab) {
      queueMicrotask(() => {
        setLab(cachedLab);
        setLoading(false);
      });
      return;
    }

    const fetchLab = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/labs/${id}`);
        if (!res.ok) {
          if (res.status === 404) throw new Error("ไม่พบข้อมูลห้องปฏิบัติการนี้");
          throw new Error("เกิดข้อผิดพลาดในการดึงข้อมูลห้องปฏิบัติการ");
        }
        const data = await res.json();
        labDetailCache.put(id, data);
        setLab(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "เกิดข้อผิดพลาดในการโหลดข้อมูล");
      } finally {
        setLoading(false);
      }
    };

    fetchLab();
  }, [id]);

  const toggleSave = () => {
    if (!lab) return;
    try {
      const savedLabs = localStorage.getItem("thai_educenter_saved_labs");
      let list: string[] = savedLabs ? JSON.parse(savedLabs) : [];
      if (list.includes(lab.id)) {
        list = list.filter((item) => item !== lab.id);
        setIsSaved(false);
      } else {
        list.push(lab.id);
        setIsSaved(true);
      }
      localStorage.setItem("thai_educenter_saved_labs", JSON.stringify(list));
    } catch {
      // ignore
    }
  };

  const handleShare = () => {
    if (navigator.share && lab) {
      navigator.share({
        title: `${lab.name_th} | Thai EduCenter`,
        text: `ทำความรู้จักห้องปฏิบัติการวิจัย ${lab.name_th} (${lab.university_th})`,
        url: window.location.href,
      }).catch(() => {});
    } else {
      navigator.clipboard.writeText(window.location.href);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--theme-bg)] text-[var(--theme-text-body)] flex flex-col font-sans selection:bg-[var(--theme-primary)] selection:text-[var(--theme-primary-contrast)] antialiased">
      <Header savedCount={0} onOpenSavedModal={() => {}} />

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-xs sm:text-sm font-black text-[var(--theme-primary)] hover:underline cursor-pointer group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span>ย้อนกลับ</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleShare}
              className="p-2.5 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] transition shadow-2xs cursor-pointer"
              title="แชร์ลิงก์ห้องวิจัยนี้"
            >
              {copiedLink ? <Check className="w-4 h-4 text-emerald-500" /> : <Share2 className="w-4 h-4" />}
            </button>
            <button
              onClick={toggleSave}
              className={`p-2.5 rounded-xl border transition shadow-2xs cursor-pointer ${
                isSaved
                  ? "bg-[var(--theme-accent)] text-[var(--theme-accent-contrast)] border-[var(--theme-accent)]"
                  : "bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)]"
              }`}
              title={isSaved ? "ลบออกจากรายการบันทึก" : "บันทึกห้องวิจัยนี้"}
            >
              <Bookmark className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="py-24 text-center space-y-4">
            <Loader2 className="w-10 h-10 animate-spin text-[var(--theme-primary)] mx-auto" />
            <p className="text-sm font-black text-[var(--theme-text-muted)]">
              กำลังโหลดข้อมูลห้องปฏิบัติการและศูนย์วิจัย...
            </p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="py-16 text-center bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl p-8 space-y-4 shadow-sm">
            <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
            <h2 className="text-lg font-black text-[var(--theme-text-title)]">{error}</h2>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] text-sm font-bold shadow-sm"
            >
              กลับสู่หน้าหลัก
            </Link>
          </div>
        )}

        {/* Lab Profile Detail */}
        {lab && !loading && (
          <div className="space-y-8">
            {/* Hero Header Card */}
            <div className="bg-[var(--theme-card)] rounded-3xl border border-[var(--theme-border)] overflow-hidden shadow-sm">
              <div className="relative h-64 sm:h-80 w-full overflow-hidden bg-black/40">
                {lab.image_url && !heroImgError ? (
                  <Image
                    src={lab.image_url}
                    alt={lab.name_th || lab.name_en || "รูปภาพห้องปฏิบัติการวิจัย"}
                    fill
                    sizes="(max-width: 1024px) 100vw, 1024px"
                    priority
                    unoptimized
                    className="object-cover"
                    onError={() => { setHeroImgError(true); }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)]">
                    <Building2 className="w-20 h-20 opacity-40" />
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent pointer-events-none" />

                <div className="absolute bottom-6 left-6 right-6 space-y-2">
                  <div className="flex flex-wrap items-center gap-2 text-xs font-bold text-white/90">
                    <span className="px-3 py-1 rounded-full bg-[var(--theme-primary)] text-white shadow-sm">
                      {lab.university_th}
                    </span>
                    <span className="px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-white">
                      {lab.faculty_th}
                    </span>
                  </div>
                  <h1 className="text-2xl sm:text-4xl font-black text-white leading-tight drop-shadow-md">
                    {lab.name_th}
                  </h1>
                  <p className="text-sm sm:text-base text-white/80 font-semibold drop-shadow-sm">
                    {lab.name_en}
                  </p>
                </div>
              </div>

              {/* Quick Action Bar */}
              <div className="p-6 bg-[var(--theme-card)] flex flex-wrap items-center justify-between gap-4 border-t border-[var(--theme-border)]">
                <div className="flex flex-wrap items-center gap-2">
                  {lab.synergy_badges?.map((badge, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 rounded-full bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] border border-[var(--theme-accent-border)] text-xs font-black flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{badge}</span>
                    </span>
                  ))}
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto">
                  {lab.website_url && (
                    <a
                      href={lab.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[var(--theme-card-subtle)] hover:bg-[var(--theme-card)] border border-[var(--theme-border)] text-xs sm:text-sm font-bold text-[var(--theme-text-body)] transition cursor-pointer"
                    >
                      <Globe className="w-4 h-4 text-[var(--theme-primary)]" />
                      <span>เว็บไซต์ทางการ</span>
                      <ExternalLink className="w-3.5 h-3.5 opacity-60" />
                    </a>
                  )}
                  <button
                    onClick={() => setShowInquiryModal(true)}
                    className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:opacity-90 text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-black shadow-md transition cursor-pointer"
                  >
                    <Send className="w-4 h-4" />
                    <span>ติดต่อสมัครเข้าร่วมแล็บ (AI)</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Main Column */}
              <div className="lg:col-span-2 space-y-8">
                {/* About Lab */}
                <div className="bg-[var(--theme-card)] p-6 sm:p-8 rounded-3xl border border-[var(--theme-border)] space-y-4 shadow-xs">
                  <h2 className="text-lg font-black text-[var(--theme-text-title)] flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-[var(--theme-primary)]" />
                    <span>เกี่ยวกับห้องปฏิบัติการและวิสัยทัศน์งานวิจัย</span>
                  </h2>
                  <p className="text-sm sm:text-base text-[var(--theme-text-body)] leading-relaxed font-normal">
                    {lab.description}
                  </p>
                </div>

                {/* Research Domains */}
                {lab.research_domains && lab.research_domains.length > 0 && (
                  <div className="bg-[var(--theme-card)] p-6 sm:p-8 rounded-3xl border border-[var(--theme-border)] space-y-4 shadow-xs">
                    <h2 className="text-lg font-black text-[var(--theme-text-title)] flex items-center gap-2">
                      <Award className="w-5 h-5 text-[var(--theme-accent)]" />
                      <span>สาขาวิชาวิจัยและความเชี่ยวชาญหลัก (Research Domains)</span>
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {lab.research_domains.map((dom, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] flex items-start gap-2.5"
                        >
                          <div className="w-2 h-2 rounded-full bg-[var(--theme-primary)] mt-1.5 shrink-0" />
                          <span className="text-xs sm:text-sm font-bold text-[var(--theme-text-title)]">
                            {dom}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Flagship Equipment & National Infrastructure */}
                {lab.flagship_equipment && lab.flagship_equipment.length > 0 && (
                  <div className="bg-[var(--theme-card)] p-6 sm:p-8 rounded-3xl border border-[var(--theme-border)] space-y-4 shadow-xs">
                    <h2 className="text-lg font-black text-[var(--theme-text-title)] flex items-center gap-2">
                      <Wrench className="w-5 h-5 text-[var(--theme-primary)]" />
                      <span>เครื่องมือวิจัยและโครงสร้างพื้นฐานระดับชาติ (Flagship Equipment)</span>
                    </h2>
                    <div className="space-y-2.5">
                      {lab.flagship_equipment.map((eq, idx) => (
                        <div
                          key={idx}
                          className="p-3.5 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] flex items-center gap-3"
                        >
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                          <span className="text-xs sm:text-sm font-semibold text-[var(--theme-text-body)]">
                            {eq}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Industry & Academic Partners */}
                {lab.industry_partners && lab.industry_partners.length > 0 && (
                  <div className="bg-[var(--theme-card)] p-6 sm:p-8 rounded-3xl border border-[var(--theme-border)] space-y-4 shadow-xs">
                    <h2 className="text-lg font-black text-[var(--theme-text-title)] flex items-center gap-2">
                      <Briefcase className="w-5 h-5 text-[var(--theme-accent)]" />
                      <span>พันธมิตรภาคอุตสาหกรรมและสากล (Industry & Global Partners)</span>
                    </h2>
                    <div className="flex flex-wrap gap-2">
                      {lab.industry_partners.map((partner, idx) => (
                        <span
                          key={idx}
                          className="px-3.5 py-1.5 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-xs sm:text-sm font-bold text-[var(--theme-text-body)]"
                        >
                          🤝 {partner}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Sidebar */}
              <div className="space-y-6">
                {/* Open Positions & Grants Box */}
                {lab.open_positions && lab.open_positions.length > 0 && (
                  <div className="bg-emerald-500/10 border-2 border-emerald-500/30 p-6 rounded-3xl space-y-3">
                    <div className="flex items-center gap-2 font-black text-sm text-emerald-700 dark:text-emerald-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span>เปิดรับสมัครนักศึกษาและทุนวิจัย (Active Calls)</span>
                    </div>
                    <ul className="space-y-2">
                      {lab.open_positions.map((pos, idx) => (
                        <li
                          key={idx}
                          className="text-xs sm:text-sm font-bold text-[var(--theme-text-title)] bg-[var(--theme-card)] p-3 rounded-xl border border-emerald-500/20 shadow-2xs"
                        >
                          {pos}
                        </li>
                      ))}
                    </ul>
                    <button
                      onClick={() => setShowInquiryModal(true)}
                      className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs sm:text-sm transition shadow-sm cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>สมัครรับทุน / ติดต่ออาจารย์</span>
                    </button>
                  </div>
                )}

                {/* Lead Advisor (Principal Investigator) Card */}
                {lab.lead_advisor && (
                  <div className="bg-[var(--theme-card)] p-6 rounded-3xl border border-[var(--theme-border)] space-y-4 shadow-xs">
                    <div className="text-xs font-black text-[var(--theme-text-muted)] uppercase tracking-wider">
                      หัวหน้าห้องปฏิบัติการ (Principal Investigator)
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="relative w-14 h-14 rounded-2xl bg-[var(--theme-primary-subtle)] border border-[var(--theme-primary-border)] flex items-center justify-center text-lg font-black text-[var(--theme-primary)] shrink-0 overflow-hidden">
                        {lab.lead_advisor.image_url && !piImgError ? (
                          <Image
                            src={lab.lead_advisor.image_url}
                            alt={lab.lead_advisor.full_name_th || "รูปหัวหน้าห้องปฏิบัติการ"}
                            width={56}
                            height={56}
                            loading="lazy"
                            decoding="async"
                            unoptimized
                            className="w-full h-full object-cover"
                            onError={() => { setPiImgError(true); }}
                          />
                        ) : (
                          <Users className="w-6 h-6" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <Link
                          href={`/advisor/${lab.lead_advisor.id}`}
                          className="text-sm sm:text-base font-black text-[var(--theme-text-title)] hover:text-[var(--theme-primary)] transition line-clamp-1"
                        >
                          {lab.lead_advisor.full_name_th}
                        </Link>
                        <p className="text-xs text-[var(--theme-text-muted)] truncate">
                          {lab.lead_advisor.role || lab.lead_advisor.academic_title_th || "อาจารย์ประจำสาขา"}
                        </p>
                      </div>
                    </div>

                    <Link
                      href={`/advisor/${lab.lead_advisor.id}`}
                      className="w-full py-2.5 rounded-xl bg-[var(--theme-card-subtle)] hover:bg-[var(--theme-card)] border border-[var(--theme-border)] hover:border-[var(--theme-primary)] text-xs font-bold text-[var(--theme-text-body)] flex items-center justify-center gap-1.5 transition cursor-pointer"
                    >
                      <span>ดูโปรไฟล์ผลงานวิจัยของอาจารย์</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                )}

                {/* Member Researchers */}
                {lab.member_faculties && lab.member_faculties.length > 0 && (
                  <div className="bg-[var(--theme-card)] p-6 rounded-3xl border border-[var(--theme-border)] space-y-4 shadow-xs">
                    <div className="text-xs font-black text-[var(--theme-text-muted)] uppercase tracking-wider">
                      คณาจารย์และนักวิจัยประจำแล็บ ({lab.member_faculties.length} ท่าน)
                    </div>

                    <div className="space-y-3">
                      {lab.member_faculties.map((fac) => (
                        <Link
                          key={fac.id}
                          href={`/advisor/${fac.id}`}
                          className="flex items-center gap-3 p-2.5 rounded-2xl hover:bg-[var(--theme-card-subtle)] border border-transparent hover:border-[var(--theme-border)] transition group"
                        >
                          <div className="relative w-10 h-10 rounded-xl bg-[var(--theme-primary-subtle)] flex items-center justify-center text-xs font-bold text-[var(--theme-primary)] shrink-0 overflow-hidden">
                            {fac.image_url && !memberImgErrors[fac.id] ? (
                              <Image
                                src={fac.image_url}
                                alt={fac.full_name_th || "รูปอาจารย์ประจำแล็บ"}
                                width={40}
                                height={40}
                                loading="lazy"
                                decoding="async"
                                unoptimized
                                className="w-full h-full object-cover"
                                onError={() => {
                                  setMemberImgErrors((prev) => ({
                                    ...prev,
                                    [fac.id]: true,
                                  }));
                                }}
                              />
                            ) : (
                              <Users className="w-4 h-4" />
                            )}
                          </div>
                          <div className="min-w-0">
                            <div className="text-xs sm:text-sm font-bold text-[var(--theme-text-body)] group-hover:text-[var(--theme-primary)] truncate">
                              {fac.full_name_th}
                            </div>
                            <div className="text-xs text-[var(--theme-text-muted)] truncate">
                              {fac.faculty_th}
                            </div>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* AI Inquiry Modal */}
      {lab && showInquiryModal && (
        <LabInquiryModal
          lab={lab}
          onClose={() => setShowInquiryModal(false)}
        />
      )}

      <Footer />
    </div>
  );
}

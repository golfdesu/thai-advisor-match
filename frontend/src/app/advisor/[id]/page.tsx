"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import {
  ArrowLeft,
  Mail,
  ExternalLink,
  GraduationCap,
  BookOpen,
  FileText,
  Building2,
  Award,
  Sparkles,
  AlertCircle,
  Heart,
  Share2,
  CheckCircle2,
  Globe
} from "lucide-react";
import type { FacultyMember } from "@/types";
import { API_BASE_URL, getAdvisorAvatarUrl } from "@/lib/config";
import { facultyDetailCache } from "@/lib/dsa";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { ColdEmailModal } from "@/components/ColdEmailModal";

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

export default function AdvisorProfilePage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [advisor, setAdvisor] = useState<FacultyMember | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState(() => hasSavedId("thai_educenter_saved_advisors", id));
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    if (!id) return;

    // Check O(1) in-memory LRU Cache first
    const cachedAdvisor = facultyDetailCache.get(id);
    if (cachedAdvisor) {
      queueMicrotask(() => {
        setAdvisor(cachedAdvisor);
        setLoading(false);
      });
      return;
    }

    const fetchAdvisor = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/faculty/${id}`);
        if (!res.ok) {
          if (res.status === 404) throw new Error("ไม่พบข้อมูลอาจารย์ท่านนี้");
          throw new Error("เกิดข้อผิดพลาดในการดึงข้อมูล");
        }
        const data = await res.json();
        // Save to O(1) LRU Cache
        facultyDetailCache.put(id, data);
        setAdvisor(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "เกิดข้อผิดพลาดในการโหลดข้อมูลอาจารย์");
      } finally {
        setLoading(false);
      }
    };

    fetchAdvisor();
  }, [id]);

  const toggleSave = () => {
    if (!advisor) return;
    try {
      const savedA = localStorage.getItem("thai_educenter_saved_advisors");
      let list: string[] = savedA ? JSON.parse(savedA) : [];
      if (list.includes(advisor.id)) {
        list = list.filter((item) => item !== advisor.id);
        setIsSaved(false);
      } else {
        list.push(advisor.id);
        setIsSaved(true);
      }
      localStorage.setItem("thai_educenter_saved_advisors", JSON.stringify(list));
    } catch {}
  };

  const handleShare = () => {
    if (navigator.share && advisor) {
      navigator.share({
        title: advisor.full_name_th || advisor.full_name,
        text: `ประวัติและผลงานวิจัยของ ${advisor.full_name_th} (${advisor.university_th}) บน Thai EduCenter`,
        url: window.location.href,
      }).catch(() => {});
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert("คัดลอกลิงก์เรียบร้อยแล้ว!");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--theme-bg)] flex flex-col items-center justify-center space-y-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--theme-primary-subtle)] border-t-[var(--theme-primary)] animate-spin" />
          <GraduationCap className="w-6 h-6 text-[var(--theme-primary)] absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        </div>
        <p className="text-sm font-bold text-[var(--theme-text-muted)] animate-pulse">กำลังโหลดข้อมูลอาจารย์ที่ปรึกษา...</p>
      </div>
    );
  }

  if (error || !advisor) {
    return (
      <div className="min-h-screen bg-[var(--theme-bg)] p-8 flex flex-col items-center justify-center text-center">
        <div className="bg-[var(--theme-card)] p-8 rounded-3xl border border-[var(--theme-border)] shadow-xl max-w-md w-full space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto">
            <AlertCircle size={28} />
          </div>
          <h2 className="text-xl font-extrabold text-[var(--theme-text-title)]">ไม่พบข้อมูล</h2>
          <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] leading-relaxed">{error || "อาจารย์ที่ปรึกษาไม่มีอยู่ในระบบ"}</p>
          <button
            onClick={() => router.push("/")}
            className="bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] font-extrabold px-6 py-3 rounded-xl transition w-full shadow-md cursor-pointer text-xs sm:text-sm"
          >
            กลับสู่หน้าหลัก
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--theme-bg)] text-[var(--theme-text-body)] flex flex-col selection:bg-[var(--theme-primary)] selection:text-[var(--theme-primary-contrast)] font-sans antialiased">
      <Header savedCount={0} onOpenSavedModal={() => {}} />

      {/* Top Clean Header Banner */}
      <div className="relative bg-[var(--theme-card-subtle)] border-b border-[var(--theme-border)] pt-8 pb-28 sm:pb-36 px-4 sm:px-6 lg:px-12">
        <div className="max-w-6xl mx-auto flex items-center justify-between relative z-10">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-[var(--theme-text-title)] bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] px-4 py-2.5 rounded-xl transition text-xs sm:text-sm font-bold shadow-xs cursor-pointer hover:border-[var(--theme-primary)]"
          >
            <ArrowLeft size={16} /> กลับ
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleSave}
              className={`p-2.5 rounded-xl border text-xs sm:text-sm font-bold transition shadow-xs cursor-pointer flex items-center gap-1.5 ${
                isSaved
                  ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)]"
                  : "bg-[var(--theme-card)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-accent)]"
              }`}
              title="บันทึกรายชื่ออาจารย์"
            >
              <Heart size={16} className={isSaved ? "fill-current" : ""} />
              <span className="hidden sm:inline">{isSaved ? "บันทึกแล้ว" : "บันทึก"}</span>
            </button>

            <button
              onClick={handleShare}
              className="p-2.5 rounded-xl bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-primary)] transition shadow-xs cursor-pointer"
              title="แชร์โปรไฟล์"
            >
              <Share2 size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Profile Content Card */}
      <div className="max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-12 -mt-20 sm:-mt-28 relative z-20 pb-20">
        <div className="bg-[var(--theme-card)] rounded-3xl shadow-xl border border-[var(--theme-border)] overflow-hidden">
          {/* Header Profile Section */}
          <div className="p-6 sm:p-10 flex flex-col md:flex-row gap-6 md:gap-8 items-start border-b border-[var(--theme-border)] bg-[var(--theme-card-subtle)]/30">
            <div className="relative shrink-0 w-32 h-32 sm:w-40 sm:h-40">
              <Image
                src={
                  !imgError && advisor.image_url
                    ? advisor.image_url
                    : getAdvisorAvatarUrl(advisor.full_name_th || advisor.full_name)
                }
                alt={advisor.full_name_th || advisor.full_name || "รูปภาพอาจารย์"}
                width={160}
                height={160}
                loading="lazy"
                decoding="async"
                unoptimized
                onError={() => {
                  setImgError(true);
                }}
                className="w-32 h-32 sm:w-40 sm:h-40 rounded-3xl object-cover border-4 border-[var(--theme-card)] shadow-xl bg-[var(--theme-card-subtle)]"
              />
              <div className="absolute -bottom-2 -right-2 w-9 h-9 rounded-xl bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center text-sm shadow-md border-2 border-[var(--theme-card)]">
                <GraduationCap size={18} />
              </div>
            </div>

            <div className="flex-1 w-full">
              <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
                <div>
                  <span className="text-xs sm:text-sm font-black text-[var(--theme-primary)] block mb-1">
                    {advisor.academic_title_th || "อาจารย์ประจำและนักวิจัย"}
                  </span>
                  <h1 className="text-2xl sm:text-4xl font-black text-[var(--theme-text-title)] mb-2 leading-tight">
                    {advisor.full_name_th}
                  </h1>
                  {advisor.full_name && (
                    <p className="text-[var(--theme-text-muted)] font-semibold mb-4 text-sm sm:text-base">
                      {advisor.full_name}
                    </p>
                  )}

                  <div className="flex flex-wrap items-center gap-2.5 mb-4">
                    <span className="bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] border border-[var(--theme-accent-border)] text-xs sm:text-sm font-black px-3.5 py-1.5 rounded-xl flex items-center gap-2 shadow-2xs">
                      <Award size={16} /> {advisor.role || "อาจารย์ประจำ"}
                    </span>
                    <span className="bg-[var(--theme-card-subtle)] text-[var(--theme-text-body)] border border-[var(--theme-border)] text-xs sm:text-sm font-bold px-3.5 py-1.5 rounded-xl flex items-center gap-2 shadow-2xs">
                      <Building2 size={16} className="text-[var(--theme-primary)]" />
                      {advisor.department_th || advisor.faculty_th}
                    </span>
                  </div>

                  <p className="text-[var(--theme-text-muted)] font-semibold text-xs sm:text-sm">
                    {advisor.faculty_th} • <strong className="text-[var(--theme-text-title)]">{advisor.university_th}</strong>
                  </p>
                </div>

                {/* Direct Action Buttons */}
                <div className="flex flex-col sm:flex-row lg:flex-col gap-3 w-full lg:w-auto shrink-0">
                  <button
                    onClick={() => setShowEmailModal(true)}
                    className="bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] font-bold px-5 py-3 rounded-xl transition flex items-center justify-center gap-2 text-xs sm:text-sm cursor-pointer shadow-xs"
                  >
                    <Mail size={16} /> ร่างอีเมลติดต่อด้วย AI
                  </button>

                  {advisor.profile_url && (
                    <a
                      href={advisor.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-title)] font-bold px-6 py-3.5 rounded-xl transition flex items-center justify-center gap-2 text-xs sm:text-sm border border-[var(--theme-border)] shadow-xs hover:border-[var(--theme-primary)]"
                    >
                      <Globe size={16} className="text-[var(--theme-primary)]" />
                      <span>เว็บทางการของสถาบัน</span>
                      <ExternalLink size={14} />
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Body Content Grid */}
          <div className="p-6 sm:p-10 grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left 2 Columns */}
            <div className="lg:col-span-2 space-y-8">
              {/* Research Interests */}
              {advisor.research_interests && advisor.research_interests.length > 0 && (
                <section className="space-y-4">
                  <h2 className="text-base sm:text-xl font-black text-[var(--theme-text-title)] flex items-center gap-2">
                    <BookOpen className="text-[var(--theme-primary)]" size={22} />
                    <span>สาขาวิจัยและความเชี่ยวชาญ (Research Interests)</span>
                  </h2>
                  <div className="flex flex-wrap gap-2.5">
                    {advisor.research_interests.map((interest, i) => (
                      <span
                        key={i}
                        className="bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] font-bold px-4 py-2 rounded-xl text-xs sm:text-sm shadow-2xs hover:border-[var(--theme-primary)] transition"
                      >
                        {interest}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Education */}
              {advisor.education && advisor.education.length > 0 && (
                <section className="space-y-4">
                  <h2 className="text-base sm:text-xl font-black text-[var(--theme-text-title)] flex items-center gap-2">
                    <GraduationCap className="text-[var(--theme-primary)]" size={22} />
                    <span>ประวัติการศึกษา (Education)</span>
                  </h2>
                  <div className="space-y-3">
                    {advisor.education.map((edu, i) => (
                      <div
                        key={i}
                        className="flex gap-4 bg-[var(--theme-card-subtle)]/70 p-4.5 rounded-2xl border border-[var(--theme-border)]"
                      >
                        <div className="w-9 h-9 rounded-xl bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)] flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                          <CheckCircle2 size={18} />
                        </div>
                        <p className="text-xs sm:text-sm text-[var(--theme-text-body)] font-semibold leading-relaxed">
                          {edu}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Publications */}
              {advisor.featured_publications && advisor.featured_publications.length > 0 && (
                <section className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-base sm:text-xl font-black text-[var(--theme-text-title)] flex items-center gap-2">
                      <FileText className="text-[var(--theme-primary)]" size={22} />
                      <span>ผลงานวิชาการและงานวิจัยเด่น (Publications)</span>
                    </h2>
                    {advisor.scholar_url && (
                      <a
                        href={advisor.scholar_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs sm:text-sm font-bold text-[var(--theme-primary)] hover:underline flex items-center gap-1.5 bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] px-3.5 py-1.5 rounded-xl transition shadow-2xs"
                      >
                        <span>Google Scholar</span>
                        <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                  <div className="space-y-3.5">
                    {advisor.featured_publications.map((pub, i) => (
                      <div
                        key={i}
                        className="bg-[var(--theme-card)] p-5 rounded-2xl border border-[var(--theme-border)] shadow-xs hover:border-[var(--theme-primary)] transition hover:shadow-md"
                      >
                        <h4 className="font-black text-sm sm:text-base text-[var(--theme-text-title)] leading-snug mb-2.5">
                          {pub.title}
                        </h4>
                        <div className="flex flex-wrap items-center gap-2.5 text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold">
                          {pub.year && (
                            <span className="bg-[var(--theme-card-subtle)] px-2.5 py-0.5 rounded-md text-[var(--theme-text-body)] font-bold border border-[var(--theme-border)] text-xs">
                              {pub.year}
                            </span>
                          )}
                          {pub.venue && <span className="text-xs sm:text-sm">{pub.venue}</span>}
                          {pub.citation_count !== undefined && pub.citation_count > 0 && (
                            <span className="text-[var(--theme-accent)] bg-[var(--theme-accent-subtle)] border border-[var(--theme-accent-border)] px-2.5 py-0.5 rounded-md font-extrabold text-xs">
                              อ้างอิง {pub.citation_count} ครั้ง
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>

            {/* Right Column Meta & Contact Card */}
            <div className="space-y-6">
              <div className="p-6 sm:p-7 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] space-y-4">
                <h3 className="text-xs sm:text-sm font-black uppercase tracking-wider text-[var(--theme-primary)] flex items-center gap-2">
                  <Sparkles size={16} />
                  <span>ข้อมูลสำหรับการติดต่อ & งานวิจัย</span>
                </h3>

                <div className="space-y-3.5 text-xs sm:text-sm">
                  <div>
                    <span className="text-[var(--theme-text-muted)] font-semibold block text-xs">สถาบันสังกัด:</span>
                    <strong className="text-[var(--theme-text-title)] text-xs sm:text-sm">{advisor.university_th}</strong>
                  </div>

                  <div>
                    <span className="text-[var(--theme-text-muted)] font-semibold block text-xs">คณะ / สำนักวิชา:</span>
                    <strong className="text-[var(--theme-text-title)] text-xs sm:text-sm">{advisor.faculty_th}</strong>
                  </div>

                  {advisor.email && (
                    <div>
                      <span className="text-[var(--theme-text-muted)] font-semibold block text-xs">อีเมลทางการ:</span>
                      <a
                        href={`mailto:${advisor.email}`}
                        className="text-[var(--theme-primary)] font-bold hover:underline break-all text-xs sm:text-sm"
                      >
                        {advisor.email}
                      </a>
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t border-[var(--theme-border)]">
                  <button
                    onClick={() => setShowEmailModal(true)}
                    className="w-full bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] font-black py-3 rounded-xl transition text-xs sm:text-sm flex items-center justify-center gap-2 shadow-sm cursor-pointer"
                  >
                    <Mail size={16} /> ร่างอีเมลติดต่ออาจารย์
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Cold Email Modal */}
      {showEmailModal && (
        <ColdEmailModal
          advisor={advisor}
          onClose={() => setShowEmailModal(false)}
        />
      )}

      <Footer />
    </div>
  );
}

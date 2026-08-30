"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  Award,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
  Star,
  CheckCircle2,
  Bookmark,
  ExternalLink,
  BookOpen,
  Users,
  Flame,
  Building2,
  GraduationCap,
  Mail,
  Heart,
  FileText
} from "lucide-react";
import { UniversityHighlight, Course, FacultyMember } from "@/types";
import { API_BASE_URL, getAdvisorAvatarUrl } from "@/lib/config";

interface FeaturedProgramsShowcaseProps {
  activeTab: "courses" | "advisors";
  onSelectUniversity: (uniName: string) => void;
  onSelectCourseSearch: (query: string) => void;
  onSelectCourseDetail?: (course: Course) => void;
  savedCourses: string[];
  savedAdvisors?: string[];
  onToggleBookmarkCourse: (id: string) => void;
  onToggleBookmarkAdvisor?: (id: string) => void;
  onOpenColdEmail?: (advisor: FacultyMember) => void;
}

export const FeaturedProgramsShowcase: React.FC<FeaturedProgramsShowcaseProps> = ({
  activeTab,
  onSelectUniversity,
  onSelectCourseSearch,
  onSelectCourseDetail,
  savedCourses,
  savedAdvisors = [],
  onToggleBookmarkCourse,
  onToggleBookmarkAdvisor,
  onOpenColdEmail
}) => {
  const [highlights, setHighlights] = useState<UniversityHighlight[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUniIdx, setSelectedUniIdx] = useState(0);
  const [activeCourseSlide, setActiveCourseSlide] = useState(0);
  const [activeAdvisorSlide, setActiveAdvisorSlide] = useState(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchSignaturePrograms = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/universities/signature-programs`);
        if (res.ok) {
          const data = await res.json();
          setHighlights(data);
        }
      } catch (e) {
        console.error("Failed to load signature programs", e);
      } finally {
        setLoading(false);
      }
    };
    fetchSignaturePrograms();
  }, []);

  // Auto-scroll promo banner timer
  useEffect(() => {
    if (highlights.length === 0) return;
    const currentUni = highlights[selectedUniIdx];
    const maxCourseLen = currentUni?.signature_programs?.length || 1;
    const maxAdvLen = currentUni?.distinguished_advisors?.length || 1;

    const interval = setInterval(() => {
      if (activeTab === "courses") {
        setActiveCourseSlide((prev) => (prev + 1) % Math.min(6, maxCourseLen));
      } else {
        setActiveAdvisorSlide((prev) => (prev + 1) % Math.min(6, maxAdvLen));
      }
    }, 6000);
    return () => clearInterval(interval);
  }, [highlights, selectedUniIdx, activeTab]);

  const currentUni = highlights[selectedUniIdx];
  const currentPrograms = currentUni?.signature_programs || [];
  const currentFeaturedCourse = currentPrograms[activeCourseSlide] || currentPrograms[0];

  const currentAdvisors = currentUni?.distinguished_advisors || [];
  const currentFeaturedAdvisor = currentAdvisors[activeAdvisorSlide] || currentAdvisors[0];

  const scrollTabs = (direction: "left" | "right") => {
    if (scrollContainerRef.current) {
      const scrollAmount = direction === "left" ? -240 : 240;
      scrollContainerRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" });
    }
  };

  if (loading || highlights.length === 0) {
    return null;
  }

  const isAdvisorTab = activeTab === "advisors";

  return (
    <section className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 my-2">
      {/* Promotion Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 mb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[var(--theme-accent-subtle)] border border-[var(--theme-accent-border)] text-[var(--theme-accent)] text-xs font-black mb-2.5 shadow-2xs">
            <Flame size={15} className="fill-current animate-pulse" />
            <span>
              {isAdvisorTab
                ? "DISTINGUISHED ADVISORS • อาจารย์ที่ปรึกษาและนักวิจัยเด่น"
                : "SIGNATURE SPOTLIGHT • หลักสูตรเรือธงยอดนิยม"}
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-[var(--theme-text-title)] tracking-tight flex items-center gap-2">
            <span>
              {isAdvisorTab
                ? "อาจารย์และนักวิจัยชั้นนำประจำสถาบัน"
                : "จุดแข็งและหลักสูตรเด่นประจำสถาบัน"}
            </span>
            <Sparkles size={24} className="text-[var(--theme-primary)]" />
          </h2>
          <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold mt-1">
            {isAdvisorTab
              ? "ทำเนียบอาจารย์ที่ปรึกษางานวิจัยและนักวิชาการชั้นแนวหน้า ผู้เชี่ยวชาญเฉพาะทางระดับประเทศของมหาวิทยาลัยชั้นนำ"
              : "ส่องหลักสูตรเรือธงยอดนิยม (Signature Programs) และเอกลักษณ์ความเชี่ยวชาญเฉพาะทางของมหาวิทยาลัยชั้นนำ"}
          </p>
        </div>

        {/* University Fast Filter Scroll Controls */}
        <div className="hidden sm:flex items-center gap-2 self-end">
          <button
            onClick={() => scrollTabs("left")}
            className="w-9 h-9 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] flex items-center justify-center text-[var(--theme-text-title)] transition shadow-2xs cursor-pointer"
            aria-label="Scroll left"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            onClick={() => scrollTabs("right")}
            className="w-9 h-9 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] flex items-center justify-center text-[var(--theme-text-title)] transition shadow-2xs cursor-pointer"
            aria-label="Scroll right"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* University Horizontal Badges Selector */}
      <div className="relative mb-6">
        <div
          ref={scrollContainerRef}
          className="flex items-center gap-2.5 overflow-x-auto pb-2 scrollbar-none scroll-smooth"
        >
          {highlights.map((item, idx) => {
            const isSelected = selectedUniIdx === idx;
            return (
              <button
                key={item.metadata.slug}
                onClick={() => {
                  setSelectedUniIdx(idx);
                  setActiveCourseSlide(0);
                  setActiveAdvisorSlide(0);
                }}
                className={`flex items-center gap-2.5 px-4 py-2.5 rounded-2xl text-xs sm:text-sm font-extrabold whitespace-nowrap transition-all cursor-pointer shrink-0 border ${
                  isSelected
                    ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] border-[var(--theme-primary)] shadow-md scale-[1.02]"
                    : "bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-body)] border-[var(--theme-border)] shadow-2xs"
                }`}
              >
                <div
                  className="w-6 h-6 rounded-lg flex items-center justify-center text-white text-xs font-black shrink-0 shadow-2xs"
                  style={{ backgroundColor: item.metadata.logo_color }}
                >
                  {item.metadata.short_name.split("/")[0].trim().substring(0, 2)}
                </div>
                <span>{item.metadata.short_name.split("/")[0].trim()}</span>
                {isSelected && (
                  <span className="w-2 h-2 rounded-full bg-[var(--theme-accent)] shadow-xs animate-ping" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* HERO PROMOTIONAL BANNER CARD */}
      {currentUni && (
        <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl overflow-hidden shadow-sm transition-all relative group">
          {/* Subtle Ambient Glow */}
          <div
            className="absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl opacity-15 pointer-events-none transition-colors"
            style={{ backgroundColor: currentUni.metadata.logo_color }}
          />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
            {/* Left Promotional Showcase (Hero Feature) */}
            <div className="lg:col-span-7 p-6 sm:p-8 lg:p-10 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-[var(--theme-border-subtle)] relative z-10">
              <div>
                {/* University Identity Header */}
                <div className="flex items-center justify-between gap-4 mb-4">
                  <div className="flex items-center gap-3.5">
                    <div
                      className="w-14 h-14 rounded-2xl flex items-center justify-center text-white text-lg font-black shadow-md shrink-0"
                      style={{ backgroundColor: currentUni.metadata.logo_color }}
                    >
                      {currentUni.metadata.short_name.split("/")[0].trim().substring(0, 3)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-xl sm:text-2xl font-black text-[var(--theme-text-title)]">
                          {currentUni.metadata.name_th}
                        </h3>
                      </div>
                      <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold">
                        {currentUni.metadata.name_en} • {currentUni.metadata.region}
                      </p>
                    </div>
                  </div>

                  <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-black text-[var(--theme-accent)] bg-[var(--theme-accent-subtle)] border border-[var(--theme-accent-border)] px-3.5 py-1.5 rounded-full">
                    <Star size={14} className="fill-current" /> TOP RANKED
                  </span>
                </div>

                {/* Motto / Slogan Banner */}
                <div className="p-4 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border-subtle)] mb-6 text-xs sm:text-sm text-[var(--theme-text-body)] font-medium italic leading-relaxed">
                  &ldquo;{currentUni.metadata.motto}&rdquo;
                </div>

                {/* SPOTLIGHT CONTENT: COURSES VS ADVISORS */}
                {!isAdvisorTab ? (
                  /* 🎓 Featured Course Spotlight */
                  currentFeaturedCourse && (
                    <div className="bg-[var(--theme-bg)] border border-[var(--theme-border)] rounded-2xl p-5 sm:p-6 mb-6 shadow-inner relative overflow-hidden">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] text-xs font-black px-3 py-1 rounded-lg shadow-2xs">
                            {currentFeaturedCourse.degree_level || "ปริญญา"}
                          </span>
                          <span className="bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] border border-[var(--theme-accent-border)] text-xs font-extrabold px-3 py-1 rounded-lg">
                            ⭐ หลักสูตรแนะนำพิเศษ
                          </span>
                        </div>

                        <button
                          onClick={() => onToggleBookmarkCourse(currentFeaturedCourse.id)}
                          className={`p-2 rounded-xl border transition cursor-pointer ${
                            savedCourses.includes(currentFeaturedCourse.id)
                              ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)]"
                              : "bg-[var(--theme-card)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-accent)]"
                          }`}
                          title="บันทึกหลักสูตรนี้"
                        >
                          <Bookmark size={16} className={savedCourses.includes(currentFeaturedCourse.id) ? "fill-current" : ""} />
                        </button>
                      </div>

                      <h4 className="text-lg sm:text-xl font-black text-[var(--theme-text-title)] leading-snug mb-2">
                        {currentFeaturedCourse.title_th}
                      </h4>

                      {currentFeaturedCourse.title_en && currentFeaturedCourse.title_en !== "Not specified" && (
                        <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold mb-3">
                          {currentFeaturedCourse.title_en}
                        </p>
                      )}

                      <p className="text-xs sm:text-sm text-[var(--theme-text-body)] font-semibold flex items-center gap-2 mb-4">
                        <Building2 size={16} className="text-[var(--theme-primary)] shrink-0" />
                        <span>{currentFeaturedCourse.faculty_th}</span>
                      </p>

                      {/* Highlights Bullets */}
                      {currentFeaturedCourse.curriculum_highlights && currentFeaturedCourse.curriculum_highlights.length > 0 && (
                        <div className="space-y-2 pt-3 border-t border-[var(--theme-border-subtle)]">
                          {currentFeaturedCourse.curriculum_highlights.slice(0, 2).map((h, hIdx) => (
                            <div key={hIdx} className="flex items-start gap-2.5 text-xs sm:text-sm text-[var(--theme-text-body)]">
                              <CheckCircle2 size={16} className="text-[var(--theme-primary)] shrink-0 mt-0.5" />
                              <span className="font-medium line-clamp-1">{h}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="mt-4 pt-3.5 border-t border-[var(--theme-border-subtle)] flex items-center justify-between">
                        <div className="text-xs sm:text-sm font-black text-[var(--theme-accent)]">
                          ค่าเทอม: {currentFeaturedCourse.tuition_per_semester || "ตามประกาศสถาบัน"}
                        </div>

                        <div className="flex items-center gap-2.5">
                          {onSelectCourseDetail && (
                            <button
                              onClick={() => onSelectCourseDetail(currentFeaturedCourse)}
                              className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] hover:text-[var(--theme-primary)] hover:underline flex items-center gap-1 cursor-pointer"
                            >
                              <span>ดูโครงสร้างหลักสูตร</span>
                            </button>
                          )}
                          {currentFeaturedCourse.website_url && (
                            <a
                              href={currentFeaturedCourse.website_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs sm:text-sm font-bold text-[var(--theme-primary)] hover:underline flex items-center gap-1"
                              title="ไปยังเว็บไซต์คณะ/หลักสูตร"
                            >
                              <span>เว็บคณะ</span>
                              <ExternalLink size={14} />
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                ) : (
                  /* 👨‍🏫 Distinguished Advisor Spotlight */
                  currentFeaturedAdvisor ? (
                    <div className="bg-[var(--theme-bg)] border border-[var(--theme-border)] rounded-2xl p-5 sm:p-6 mb-6 shadow-inner relative overflow-hidden">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] text-xs font-black px-3 py-1 rounded-lg shadow-2xs">
                            {currentFeaturedAdvisor.academic_title_th || "อาจารย์ที่ปรึกษา"}
                          </span>
                          <span className="bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] border border-[var(--theme-accent-border)] text-xs font-extrabold px-3 py-1 rounded-lg">
                            ⭐ นักวิจัยเด่นประจำสถาบัน
                          </span>
                        </div>

                        {onToggleBookmarkAdvisor && (
                          <button
                            onClick={() => onToggleBookmarkAdvisor(currentFeaturedAdvisor.id)}
                            className={`p-2 rounded-xl border transition cursor-pointer ${
                              savedAdvisors.includes(currentFeaturedAdvisor.id)
                                ? "bg-[var(--theme-accent-subtle)] border-[var(--theme-accent-border)] text-[var(--theme-accent)]"
                                : "bg-[var(--theme-card)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-accent)]"
                            }`}
                            title="บันทึกอาจารย์ท่านนี้"
                          >
                            <Heart size={16} className={savedAdvisors.includes(currentFeaturedAdvisor.id) ? "fill-current text-rose-500" : ""} />
                          </button>
                        )}
                      </div>

                      <div className="flex items-start gap-4 mb-4">
                        <div className="relative shrink-0">
                          <img
                            src={currentFeaturedAdvisor.image_url || getAdvisorAvatarUrl(currentFeaturedAdvisor.full_name_th || currentFeaturedAdvisor.full_name || currentFeaturedAdvisor.first_name)}
                            alt={currentFeaturedAdvisor.full_name_th}
                            loading="lazy"
                            decoding="async"
                            onError={(e) => {
                              (e.target as HTMLImageElement).src = getAdvisorAvatarUrl(currentFeaturedAdvisor.full_name_th || currentFeaturedAdvisor.full_name || currentFeaturedAdvisor.first_name);
                            }}
                            className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl object-cover border-2 border-[var(--theme-border)] shadow-xs bg-[var(--theme-card-subtle)]"
                          />
                          <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-lg bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center text-xs shadow-xs">
                            <GraduationCap className="w-3.5 h-3.5" />
                          </div>
                        </div>

                        <div className="min-w-0 flex-1">
                          <h4 className="text-lg sm:text-xl font-black text-[var(--theme-text-title)] leading-snug truncate">
                            {currentFeaturedAdvisor.full_name_th || currentFeaturedAdvisor.full_name}
                          </h4>
                          {currentFeaturedAdvisor.full_name && currentFeaturedAdvisor.full_name !== currentFeaturedAdvisor.full_name_th && (
                            <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold truncate mt-0.5">
                              {currentFeaturedAdvisor.full_name}
                            </p>
                          )}
                          <p className="text-xs sm:text-sm text-[var(--theme-text-body)] font-semibold flex items-center gap-2 mt-2">
                            <Building2 size={16} className="text-[var(--theme-primary)] shrink-0" />
                            <span className="truncate">{currentFeaturedAdvisor.department_th || currentFeaturedAdvisor.faculty_th}</span>
                          </p>
                        </div>
                      </div>

                      {/* Research Interests Tags */}
                      {currentFeaturedAdvisor.research_interests && currentFeaturedAdvisor.research_interests.length > 0 && (
                        <div className="space-y-2 pt-3 border-t border-[var(--theme-border-subtle)]">
                          <span className="text-xs font-black text-[var(--theme-text-muted)] block">
                            สาขาวิจัยและความเชี่ยวชาญ:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {currentFeaturedAdvisor.research_interests.slice(0, 3).map((r, rIdx) => (
                              <span
                                key={rIdx}
                                className="bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-title)] text-xs font-bold px-2.5 py-1 rounded-lg"
                              >
                                {r}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-4 pt-3.5 border-t border-[var(--theme-border-subtle)] flex items-center justify-between">
                        <Link
                          href={`/advisor/${currentFeaturedAdvisor.id}`}
                          className="text-xs sm:text-sm font-black text-[var(--theme-primary)] hover:underline flex items-center gap-1 cursor-pointer"
                        >
                          <span>ดูโปรไฟล์ & งานวิจัยเต็ม</span>
                          <ArrowRight size={14} />
                        </Link>

                        {onOpenColdEmail && (
                          <button
                            onClick={() => onOpenColdEmail(currentFeaturedAdvisor)}
                            className="px-3.5 py-1.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold transition flex items-center gap-1.5 shadow-2xs cursor-pointer"
                          >
                            <Mail size={13} />
                            <span>ร่างอีเมล AI</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="p-8 rounded-2xl bg-[var(--theme-bg)] border border-[var(--theme-border)] text-center text-xs text-[var(--theme-text-muted)] mb-6">
                      กำลังรวบรวมทำเนียบอาจารย์ที่ปรึกษาของสถาบันนี้...
                    </div>
                  )
                )}
              </div>

              {/* Bottom Quick Action CTAs */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div className="flex items-center gap-3 text-xs sm:text-sm text-[var(--theme-text-muted)] font-bold">
                  <div className="flex items-center gap-1.5 bg-[var(--theme-card-subtle)] px-3.5 py-1.5 rounded-xl border border-[var(--theme-border)]">
                    <BookOpen size={15} className="text-[var(--theme-primary)]" />
                    <span>{currentUni.total_courses} หลักสูตรในระบบ</span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-[var(--theme-card-subtle)] px-3.5 py-1.5 rounded-xl border border-[var(--theme-border)]">
                    <Users size={15} className="text-[var(--theme-accent)]" />
                    <span>{currentUni.total_advisors} อาจารย์ที่ปรึกษา</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onSelectUniversity(currentUni.metadata.name_th)}
                    className="bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-black px-4.5 py-2.5 rounded-xl transition flex items-center gap-2 shadow-sm cursor-pointer"
                  >
                    <span>
                      {isAdvisorTab
                        ? `ดูทุกอาจารย์ของ ${currentUni.metadata.short_name.split("/")[0].trim()}`
                        : `ดูทุกหลักสูตรของ ${currentUni.metadata.short_name.split("/")[0].trim()}`}
                    </span>
                    <ArrowRight size={15} />
                  </button>
                </div>
              </div>
            </div>

            {/* Right Column: Other Programs / Advisors Carousel List & Academic Strengths */}
            <div className="lg:col-span-5 p-6 sm:p-8 bg-[var(--theme-card-subtle)]/40 flex flex-col justify-between">
              <div>
                {/* Academic Strengths Pills */}
                <div className="mb-6">
                  <span className="text-xs sm:text-sm font-black text-[var(--theme-primary)] flex items-center gap-1.5 mb-3">
                    <Sparkles size={16} />
                    จุดเด่นทางวิชาการ (Academic Strengths)
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {currentUni.metadata.academic_strengths.map((str, sIdx) => (
                      <span
                        key={sIdx}
                        className="bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-title)] text-xs font-bold px-3 py-1.5 rounded-xl shadow-2xs"
                      >
                        {str}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Programs or Advisors Mini-Cards Carousel List */}
                {!isAdvisorTab ? (
                  /* Course Mini-Cards */
                  <>
                    <div className="mb-3.5 flex items-center justify-between">
                      <span className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] flex items-center gap-1.5">
                        <Award size={16} className="text-[var(--theme-accent)]" />
                        หลักสูตรเรือธงประจำจุดแข็ง (Flagship Programs)
                      </span>
                      <span className="text-xs text-[var(--theme-text-muted)] font-bold">
                        {activeCourseSlide + 1} จาก {currentPrograms.length} หลักสูตร
                      </span>
                    </div>

                    <div className="space-y-2.5">
                      {currentPrograms.map((prog, pIdx) => {
                        const isCurrent = activeCourseSlide === pIdx;
                        return (
                          <div
                            key={prog.id}
                            onClick={() => setActiveCourseSlide(pIdx)}
                            className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                              isCurrent
                                ? "bg-[var(--theme-card)] border-[var(--theme-primary)] shadow-sm translate-x-1 ring-2 ring-[var(--theme-primary)]/20"
                                : "bg-[var(--theme-card)]/80 hover:bg-[var(--theme-card)] border-[var(--theme-border)] shadow-2xs opacity-85 hover:opacity-100"
                            }`}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`text-xs font-black px-2 py-0.5 rounded-md ${
                                  isCurrent
                                    ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)]"
                                    : "bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)]"
                                }`}>
                                  {prog.degree_level || "หลักสูตร"}
                                </span>
                                <span className="text-xs text-[var(--theme-text-muted)] truncate font-semibold">
                                  {prog.faculty_th}
                                </span>
                              </div>
                              <h5 className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] truncate">
                                {prog.title_th}
                              </h5>
                            </div>

                            <div className="shrink-0 text-right">
                              <span className="text-xs font-black text-[var(--theme-accent)] block">
                                {prog.tuition_per_semester || "ตามประกาศ"}
                              </span>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onSelectCourseSearch(prog.title_th);
                                }}
                                className="text-xs font-bold text-[var(--theme-primary)] hover:underline inline-flex items-center gap-1 mt-0.5"
                              >
                                <span>ค้นหา</span>
                                <ArrowRight size={12} />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </>
                ) : (
                  /* Advisors Mini-Cards */
                  <>
                    <div className="mb-3.5 flex items-center justify-between">
                      <span className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] flex items-center gap-1.5">
                        <Users size={16} className="text-[var(--theme-accent)]" />
                        อาจารย์และนักวิจัยเด่น (Distinguished Faculty)
                      </span>
                      <span className="text-xs text-[var(--theme-text-muted)] font-bold">
                        {currentAdvisors.length > 0 ? `${activeAdvisorSlide + 1} จาก ${currentAdvisors.length} ท่าน` : "0 ท่าน"}
                      </span>
                    </div>

                    <div className="space-y-2.5">
                      {currentAdvisors.map((adv, aIdx) => {
                        const isCurrent = activeAdvisorSlide === aIdx;
                        return (
                          <div
                            key={adv.id}
                            onClick={() => setActiveAdvisorSlide(aIdx)}
                            className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                              isCurrent
                                ? "bg-[var(--theme-card)] border-[var(--theme-primary)] shadow-sm translate-x-1 ring-2 ring-[var(--theme-primary)]/20"
                                : "bg-[var(--theme-card)]/80 hover:bg-[var(--theme-card)] border-[var(--theme-border)] shadow-2xs opacity-85 hover:opacity-100"
                            }`}
                          >
                            <div className="flex items-center gap-3 min-w-0 flex-1">
                              <img
                                src={adv.image_url || getAdvisorAvatarUrl(adv.full_name_th || adv.full_name || adv.first_name)}
                                alt={adv.full_name_th}
                                loading="lazy"
                                decoding="async"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = getAdvisorAvatarUrl(adv.full_name_th || adv.full_name || adv.first_name);
                                }}
                                className="w-9 h-9 rounded-xl object-cover border border-[var(--theme-border)] shrink-0"
                              />
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2 mb-0.5">
                                  <span className={`text-[10px] font-black px-1.5 py-0.2 rounded ${
                                    isCurrent
                                      ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)]"
                                      : "bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)]"
                                  }`}>
                                    {adv.academic_title_th || "อาจารย์"}
                                  </span>
                                  <span className="text-[11px] text-[var(--theme-text-muted)] truncate font-semibold">
                                    {adv.department_th || adv.faculty_th}
                                  </span>
                                </div>
                                <h5 className="text-xs sm:text-sm font-black text-[var(--theme-text-title)] truncate">
                                  {adv.full_name_th || adv.full_name}
                                </h5>
                              </div>
                            </div>

                            <div className="shrink-0 text-right">
                              <Link
                                href={`/advisor/${adv.id}`}
                                onClick={(e) => e.stopPropagation()}
                                className="text-xs font-bold text-[var(--theme-primary)] hover:underline inline-flex items-center gap-1 mt-0.5"
                              >
                                <span>โปรไฟล์</span>
                                <ArrowRight size={12} />
                              </Link>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}
              </div>

              {/* Bottom University Navigator Dots */}
              <div className="pt-5 mt-5 border-t border-[var(--theme-border-subtle)] flex items-center justify-between">
                <span className="text-xs text-[var(--theme-text-muted)] font-semibold">
                  สถาบันที่ {selectedUniIdx + 1} จาก {highlights.length} สถาบัน
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setSelectedUniIdx((prev) => (prev > 0 ? prev - 1 : highlights.length - 1));
                      setActiveCourseSlide(0);
                      setActiveAdvisorSlide(0);
                    }}
                    className="px-3 py-1.5 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-xs font-bold text-[var(--theme-text-title)] cursor-pointer shadow-2xs"
                  >
                    ← ก่อนหน้า
                  </button>
                  <button
                    onClick={() => {
                      setSelectedUniIdx((prev) => (prev < highlights.length - 1 ? prev + 1 : 0));
                      setActiveCourseSlide(0);
                      setActiveAdvisorSlide(0);
                    }}
                    className="px-3 py-1.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-xs font-bold text-[var(--theme-primary-contrast)] cursor-pointer shadow-2xs"
                  >
                    ถัดไป →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

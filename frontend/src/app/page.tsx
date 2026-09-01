"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Search,
  BookOpen,
  Users,
  Loader2,
  Scale,
  TrendingUp,
  AlertCircle,
  Sparkles,
  Compass,
  Award,
  ArrowRight,
  X,
  Building2
} from "lucide-react";
import { FacultyMember, SearchMatchResult, Course, ResearchLab } from "@/types";
import { API_BASE_URL } from "@/lib/config";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { CourseCard } from "@/components/CourseCard";
import { AdvisorCard } from "@/components/AdvisorCard";
import { LabCard } from "@/components/LabCard";
import { FilterBar } from "@/components/FilterBar";
import { ComparisonModal } from "@/components/ComparisonModal";
import { ColdEmailModal } from "@/components/ColdEmailModal";
import { LabInquiryModal } from "@/components/LabInquiryModal";
import { SavedBookmarksModal } from "@/components/SavedBookmarksModal";
import { FeaturedProgramsShowcase } from "@/components/FeaturedProgramsShowcase";
import { CourseDetailModal } from "@/components/CourseDetailModal";
import { searchApiCache } from "@/lib/dsa";

const readSavedIds = (storageKey: string): string[] => {
  if (typeof window === "undefined") return [];

  try {
    const saved = window.localStorage.getItem(storageKey);
    const parsed: unknown = saved ? JSON.parse(saved) : [];
    return Array.isArray(parsed) && parsed.every((value): value is string => typeof value === "string")
      ? parsed
      : [];
  } catch {
    return [];
  }
};

export default function Home() {
  const [activeTab, setActiveTab] = useState<"courses" | "advisors" | "labs">("courses");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDegree, setSelectedDegree] = useState("all");
  const [selectedUni, setSelectedUni] = useState("all");

  const [courses, setCourses] = useState<Course[]>([]);
  const [advisors, setAdvisors] = useState<SearchMatchResult[]>([]);
  const [labs, setLabs] = useState<ResearchLab[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Comparison Matrix State
  const [comparedCourses, setComparedCourses] = useState<Course[]>([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  // Wishlist / Bookmarks State
  const [savedCourses, setSavedCourses] = useState<string[]>(() => readSavedIds("thai_educenter_saved_courses"));
  const [savedAdvisors, setSavedAdvisors] = useState<string[]>(() => readSavedIds("thai_educenter_saved_advisors"));
  const [showSavedModal, setShowSavedModal] = useState(false);

  // Selected Course Detail Modal State
  const [selectedCourseForDetail, setSelectedCourseForDetail] = useState<Course | null>(null);

  // Cold Email Modal State
  const [selectedAdvisorForEmail, setSelectedAdvisorForEmail] = useState<FacultyMember | null>(null);

  // Lab Inquiry Modal State
  const [selectedLabForInquiry, setSelectedLabForInquiry] = useState<ResearchLab | null>(null);

  // Search input ref for keyboard shortcut focus
  const searchInputRef = useRef<HTMLInputElement>(null);
  // Results section ref for auto-scrolling
  const resultsSectionRef = useRef<HTMLElement>(null);

  // Keyboard shortcut listener (Press '/' to focus search, 'Escape' to blur)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === "/" &&
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "TEXTAREA"
      ) {
        e.preventDefault();
        searchInputRef.current?.focus();
      } else if (e.key === "Escape" && document.activeElement === searchInputRef.current) {
        searchInputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  async function fetchInitialData() {
    try {
      setLoading(true);
      const [coursesRes, facultyRes, labsRes] = await Promise.allSettled([
        fetch(`${API_BASE_URL}/courses/?limit=24`),
        fetch(`${API_BASE_URL}/faculty/?limit=24`),
        fetch(`${API_BASE_URL}/labs/?limit=24`),
      ]);

      if (coursesRes.status === "fulfilled" && coursesRes.value.ok) {
        const data = await coursesRes.value.json();
        setCourses(Array.isArray(data) ? data : (data.results ?? []));
      }

      if (facultyRes.status === "fulfilled" && facultyRes.value.ok) {
        const data = await facultyRes.value.json();
        const list = Array.isArray(data) ? data : (data.results ?? []);
        setAdvisors(list.map((f: FacultyMember) => ({ faculty: f, match_score: 90 })));
      }

      if (labsRes.status === "fulfilled" && labsRes.value.ok) {
        const data = await labsRes.value.json();
        const list = Array.isArray(data) ? data : (data.results ?? []);
        setLabs(list);
      }
    } catch (err) {
      console.warn("Backend loading default catalog data error", err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch initial catalog data on load (courses, faculty advisors, and research labs)
  useEffect(() => {
    const timerId = window.setTimeout(() => {
      void fetchInitialData();
    }, 0);

    return () => window.clearTimeout(timerId);
  }, []);

  const toggleBookmarkCourse = (id: string) => {
    setSavedCourses((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      try {
        localStorage.setItem("thai_educenter_saved_courses", JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const toggleBookmarkAdvisor = (id: string) => {
    setSavedAdvisors((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      try {
        localStorage.setItem("thai_educenter_saved_advisors", JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const toggleCompareCourse = (course: Course) => {
    setComparedCourses((prev) => {
      const exists = prev.some((c) => c.id === course.id);
      if (exists) {
        return prev.filter((c) => c.id !== course.id);
      } else {
        if (prev.length >= 4) {
          alert("คุณสามารถเปรียบเทียบหลักสูตรพร้อมกันได้สูงสุด 4 หลักสูตรครับ");
          return prev;
        }
        return [...prev, course];
      }
    });
  };

  const scrollToResults = () => {
    setTimeout(() => {
      if (resultsSectionRef.current) {
        resultsSectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, 100);
  };

  const executeSearch = async (
    queryText?: string,
    uniFilter?: string,
    degFilter?: string,
    tabOverride?: "courses" | "advisors" | "labs",
    shouldScroll: boolean = true
  ) => {
    const queryToUse = queryText !== undefined ? queryText : searchQuery;
    const uniToUse = uniFilter !== undefined ? uniFilter : selectedUni;
    const degToUse = degFilter !== undefined ? degFilter : selectedDegree;
    const currentTab = tabOverride !== undefined ? tabOverride : activeTab;

    if (shouldScroll) {
      scrollToResults();
    }

    const cacheKey = `${currentTab}:${queryToUse.trim()}:${uniToUse}:${degToUse}`;
    const cachedData = searchApiCache.get(cacheKey);
    if (cachedData) {
      if (currentTab === "courses") {
        setCourses(cachedData as Course[]);
      } else if (currentTab === "advisors") {
        setAdvisors(cachedData as SearchMatchResult[]);
      } else {
        setLabs(cachedData as ResearchLab[]);
      }
      setErrorMsg(null);
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    try {
      if (currentTab === "courses") {
        const res = await fetch(`${API_BASE_URL}/courses/search`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: queryToUse,
            university: uniToUse === "all" ? null : uniToUse,
            degree_level: degToUse === "all" ? null : degToUse,
            top_k: 24,
          }),
        });

        if (res.ok) {
          const data = await res.json();
          const list = Array.isArray(data) ? data : (data.results ?? []);
          searchApiCache.put(cacheKey, list);
          setCourses(list);
        } else {
          setErrorMsg("ไม่พบหลักสูตรที่ตรงกับคำค้นหา ลองปรับเปลี่ยนคำค้นหาอีกครั้งครับ");
        }
      } else if (currentTab === "advisors") {
        if (!queryToUse.trim()) {
          const uniParam = uniToUse && uniToUse !== "all" ? `&university=${encodeURIComponent(uniToUse)}` : "";
          const res = await fetch(`${API_BASE_URL}/faculty/?limit=24${uniParam}`);
          if (res.ok) {
            const data = await res.json();
            const list = Array.isArray(data) ? data : (data.results ?? []);
            const formatted = list.map((f: FacultyMember) => ({ faculty: f, match_score: 85 }));
            searchApiCache.put(cacheKey, formatted);
            setAdvisors(formatted);
          }
        } else {
          const res = await fetch(`${API_BASE_URL}/search/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              query: queryToUse,
              university: uniToUse === "all" ? null : uniToUse,
              top_k: 15,
            }),
          });

          if (res.ok) {
            const data = await res.json();
            const list = Array.isArray(data) ? data : (data.results ?? []);
            searchApiCache.put(cacheKey, list);
            setAdvisors(list);
          } else {
            setErrorMsg("เกิดข้อผิดพลาดในการจับคู่อาจารย์ที่ปรึกษา กรุณาลองใหม่อีกครั้ง");
          }
        }
      } else {
        // Labs Tab Search
        if (!queryToUse.trim()) {
          const uniParam = uniToUse && uniToUse !== "all" ? `&university=${encodeURIComponent(uniToUse)}` : "";
          const res = await fetch(`${API_BASE_URL}/labs/?limit=24${uniParam}`);
          if (res.ok) {
            const data = await res.json();
            const list = Array.isArray(data) ? data : (data.results ?? []);
            searchApiCache.put(cacheKey, list);
            setLabs(list);
          }
        } else {
          const res = await fetch(`${API_BASE_URL}/labs/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              query: queryToUse,
              university: uniToUse === "all" ? null : uniToUse,
              top_k: 20,
            }),
          });

          if (res.ok) {
            const data = await res.json();
            const list = Array.isArray(data) ? data : (data.results ?? []);
            searchApiCache.put(cacheKey, list);
            setLabs(list);
          } else {
            setErrorMsg("เกิดข้อผิดพลาดในการค้นหาห้องปฏิบัติการ กรุณาลองใหม่อีกครั้ง");
          }
        }
      }
    } catch (err) {
      console.error(err);
      setErrorMsg("ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ กรุณาลองใหม่ในภายหลัง");
    } finally {
      setLoading(false);
    }
  };

  // Popular Academic Disciplines
  const popularTopics = [
    { label: "แพทยศาสตร์ & ทันตแพทย์", query: "แพทยศาสตร์ ทันตแพทยศาสตร์" },
    { label: "วิศวกรรมปัญญาประดิษฐ์ & หุ่นยนต์", query: "วิศวกรรมหุ่นยนต์ ปัญญาประดิษฐ์ AI" },
    { label: "วิทยาการข้อมูล & ไซเบอร์", query: "วิทยาการข้อมูล ความมั่นคงไซเบอร์ Data Science" },
    { label: "บริหารธุรกิจ & MBA", query: "บริหารธุรกิจ การจัดการ การตลาด MBA" },
    { label: "นวัตกรรมบูรณาการ (BAScii)", query: "BAScii นวัตกรรมบูรณาการ" },
    { label: "นิเทศศาสตร์ & สื่อสร้างสรรค์", query: "นิเทศศาสตร์ ภาพยนตร์และสื่อดิจิทัล" },
  ];

  return (
    <div className="min-h-screen bg-[var(--theme-bg)] text-[var(--theme-text-body)] flex flex-col selection:bg-[var(--theme-primary)] selection:text-[var(--theme-primary-contrast)] font-sans antialiased">
      {/* Editorial Header */}
      <Header
        savedCount={savedCourses.length + savedAdvisors.length}
        onOpenSavedModal={() => setShowSavedModal(true)}
      />

      {/* New Academic Command Center hero */}
      <section className="relative overflow-hidden border-b border-[var(--theme-border)] bg-[var(--theme-bg-subtle)]">
        <div aria-hidden="true" className="pointer-events-none absolute -right-32 -top-40 h-96 w-96 rounded-full bg-[var(--theme-primary)]/10 blur-3xl" />
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-48 left-1/3 h-96 w-96 rounded-full bg-[var(--theme-accent)]/10 blur-3xl" />

        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.1fr_.9fr] lg:gap-16 lg:px-8 lg:py-20">
          <div className="flex flex-col justify-center">
            <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-[var(--theme-primary-border)] bg-[var(--theme-primary-subtle)] px-3.5 py-1.5 text-xs font-black text-[var(--theme-primary)]">
              <Sparkles size={14} className="text-[var(--theme-accent)]" aria-hidden="true" />
              <span>Thai academic discovery, redesigned</span>
            </div>

            <h1 className="max-w-3xl text-4xl font-black leading-[1.08] tracking-tight text-[var(--theme-text-title)] sm:text-6xl">
              วางแผนอนาคตทางการศึกษา
              <span className="mt-2 block text-[var(--theme-primary)]">ด้วยข้อมูลที่ใช่สำหรับคุณ</span>
            </h1>
            <p className="mt-6 max-w-2xl text-base font-medium leading-relaxed text-[var(--theme-text-muted)] sm:text-lg">
              ค้นหาหลักสูตร อาจารย์ที่ปรึกษา และห้องวิจัยชั้นนำในพื้นที่เดียว พร้อม AI ช่วยเชื่อมโยงเส้นทางการเรียนกับเป้าหมายวิจัยของคุณ
            </p>

            <div className="mt-8 rounded-[1.75rem] border border-[var(--theme-border)] bg-[var(--theme-card)] p-3 shadow-xl shadow-[var(--theme-primary-glow)]/10 sm:p-4">
              <div role="tablist" aria-label="ประเภทการค้นหา" className="grid grid-cols-3 gap-1 rounded-2xl bg-[var(--theme-card-subtle)] p-1">
                {([
                  ["courses", BookOpen, "หลักสูตร"],
                  ["advisors", Users, "อาจารย์ที่ปรึกษา"],
                  ["labs", Sparkles, "ห้องวิจัย"],
                ] as const).map(([tab, Icon, label]) => (
                  <button
                    key={tab}
                    role="tab"
                    aria-selected={activeTab === tab}
                    onClick={() => {
                      setActiveTab(tab);
                      executeSearch(searchQuery, selectedUni, selectedDegree, tab);
                    }}
                    className={`flex min-h-11 items-center justify-center gap-2 rounded-xl px-2 py-2.5 text-xs font-black transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)] sm:text-sm ${
                      activeTab === tab
                        ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-md"
                        : "text-[var(--theme-text-muted)] hover:bg-[var(--theme-card)] hover:text-[var(--theme-text-title)]"
                    }`}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    <span>{label}</span>
                  </button>
                ))}
              </div>

              <div className="group/search relative mt-3">
                <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[var(--theme-text-muted)] group-focus-within/search:text-[var(--theme-primary)]" aria-hidden="true" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && executeSearch()}
                  placeholder={
                    activeTab === "courses"
                      ? "เช่น วิศวกรรมคอมพิวเตอร์, การเงิน, แพทยศาสตร์"
                      : activeTab === "advisors"
                      ? "เช่น NLP, พลังงานหมุนเวียน, วิทยาการข้อมูล"
                      : "เช่น Robotics, Clean Energy, Genomics"
                  }
                  aria-label="ค้นหาหลักสูตร อาจารย์ หรือห้องวิจัย"
                  className="min-h-14 w-full rounded-2xl border border-[var(--theme-border)] bg-[var(--theme-bg)] pl-12 pr-32 text-sm font-semibold text-[var(--theme-text-title)] placeholder:text-[var(--theme-text-muted)] focus:border-[var(--theme-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)]/25 sm:text-base"
                />
                <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1.5">
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={() => {
                        setSearchQuery("");
                        searchInputRef.current?.focus();
                      }}
                      aria-label="ล้างคำค้นหา"
                      className="rounded-lg p-2 text-[var(--theme-text-muted)] transition hover:bg-[var(--theme-card-subtle)] hover:text-[var(--theme-text-title)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)]"
                    >
                      <X className="h-4 w-4" aria-hidden="true" />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => executeSearch()}
                    disabled={loading}
                    className="flex min-h-10 items-center gap-2 rounded-xl bg-[var(--theme-primary)] px-3.5 text-xs font-black text-[var(--theme-primary-contrast)] transition hover:bg-[var(--theme-primary-hover)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 sm:px-4 sm:text-sm"
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Search className="h-4 w-4" aria-hidden="true" />}
                    <span>ค้นหา</span>
                  </button>
                </div>
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="mr-1 flex items-center gap-1 text-xs font-black text-[var(--theme-text-muted)]">
                  <TrendingUp className="h-3.5 w-3.5 text-[var(--theme-accent)]" aria-hidden="true" />
                  เริ่มจากหัวข้อยอดนิยม
                </span>
                {popularTopics.slice(0, 4).map((topic) => (
                  <button
                    key={topic.query}
                    type="button"
                    onClick={() => {
                      setSearchQuery(topic.query);
                      executeSearch(topic.query);
                    }}
                    className="rounded-full border border-[var(--theme-border)] bg-[var(--theme-card-subtle)] px-3 py-1.5 text-xs font-bold text-[var(--theme-text-body)] transition hover:border-[var(--theme-primary)] hover:text-[var(--theme-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)]"
                  >
                    {topic.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center">
            <div className="relative w-full overflow-hidden rounded-[2rem] bg-[var(--theme-card)] dark:bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] p-6 text-[var(--theme-text-title)] shadow-xl sm:p-8">
              <div aria-hidden="true" className="absolute -right-14 -top-14 h-48 w-48 rounded-full border-[24px] border-[var(--theme-primary)]/10 pointer-events-none" />
              <div aria-hidden="true" className="absolute -bottom-20 -left-10 h-48 w-48 rounded-full border-[24px] border-[var(--theme-accent)]/10 pointer-events-none" />
              <div className="relative">
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)] border border-[var(--theme-primary-border)] px-3 py-1 text-xs font-black tracking-wide">
                    YOUR NEXT MOVE
                  </span>
                  <Compass className="h-6 w-6 text-[var(--theme-accent)]" aria-hidden="true" />
                </div>
                <h2 className="mt-8 max-w-sm text-2xl font-black leading-tight sm:text-3xl text-[var(--theme-text-title)]">
                  จากคำถามสั้น ๆ สู่เส้นทางที่ชัดเจนขึ้น
                </h2>
                <p className="mt-4 max-w-sm text-sm font-medium leading-relaxed text-[var(--theme-text-muted)]">
                  เลือกเครื่องมือที่ตรงกับช่วงเวลาของคุณ แล้วเริ่มสำรวจได้ทันที
                </p>

                <div className="mt-8 grid gap-3">
                  <Link
                    href="/career-discovery"
                    className="flex items-center gap-3 rounded-2xl bg-[var(--theme-card-subtle)] dark:bg-[var(--theme-card)] border border-[var(--theme-border)] p-3.5 transition hover:border-[var(--theme-primary)] hover:shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)] group"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--theme-accent)] text-[var(--theme-accent-contrast)]">
                      <Compass className="h-5 w-5" aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-black text-[var(--theme-text-title)] group-hover:text-[var(--theme-primary)] transition-colors">
                        ค้นหาตัวตนและสายอาชีพ
                      </div>
                      <div className="mt-0.5 text-xs text-[var(--theme-text-muted)]">
                        แบบประเมิน RIASEC 5 นาที
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[var(--theme-text-muted)] group-hover:text-[var(--theme-primary)] group-hover:translate-x-0.5 transition-all" aria-hidden="true" />
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab("advisors");
                      setSearchQuery("");
                      executeSearch("", selectedUni, selectedDegree, "advisors");
                    }}
                    className="flex items-center gap-3 rounded-2xl bg-[var(--theme-card-subtle)] dark:bg-[var(--theme-card)] border border-[var(--theme-border)] p-3.5 text-left transition hover:border-[var(--theme-primary)] hover:shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-primary)] group cursor-pointer"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)]">
                      <Users className="h-5 w-5" aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-black text-[var(--theme-text-title)] group-hover:text-[var(--theme-primary)] transition-colors">
                        ดูอาจารย์ที่ปรึกษาทั้งหมด
                      </div>
                      <div className="mt-0.5 text-xs text-[var(--theme-text-muted)]">
                        ค้นหาคนที่เข้าใจหัวข้อวิจัย
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[var(--theme-text-muted)] group-hover:text-[var(--theme-primary)] group-hover:translate-x-0.5 transition-all" aria-hidden="true" />
                  </button>
                </div>

                <div className="mt-8 grid grid-cols-3 gap-3 border-t border-[var(--theme-border)] pt-5">
                  <div>
                    <div className="text-xl font-black text-[var(--theme-text-title)]">2.8K+</div>
                    <div className="mt-1 text-[11px] font-semibold text-[var(--theme-text-muted)]">หลักสูตร</div>
                  </div>
                  <div>
                    <div className="text-xl font-black text-[var(--theme-text-title)]">1K+</div>
                    <div className="mt-1 text-[11px] font-semibold text-[var(--theme-text-muted)]">นักวิจัย</div>
                  </div>
                  <div>
                    <div className="text-xl font-black text-[var(--theme-text-title)]">25+</div>
                    <div className="mt-1 text-[11px] font-semibold text-[var(--theme-text-muted)]">มหาวิทยาลัย</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 🌟 Signature Spotlight / University Highlights Promotional Showcase */}
      <section className="border-b border-[var(--theme-border)] bg-[var(--theme-bg)] py-4 sm:py-6">
        <FeaturedProgramsShowcase
          activeTab={activeTab}
          onSelectUniversity={(uniName) => {
            setSelectedUni(uniName);
            executeSearch(searchQuery, uniName, selectedDegree, activeTab);
          }}
          onSelectCourseSearch={(courseTitle) => {
            setSearchQuery(courseTitle);
            setActiveTab("courses");
            executeSearch(courseTitle, selectedUni, selectedDegree, "courses");
          }}
          onSelectCourseDetail={(course) => setSelectedCourseForDetail(course)}
          savedCourses={savedCourses}
          savedAdvisors={savedAdvisors}
          onToggleBookmarkCourse={toggleBookmarkCourse}
          onToggleBookmarkAdvisor={toggleBookmarkAdvisor}
          onOpenColdEmail={(advisor) => setSelectedAdvisorForEmail(advisor)}
        />
      </section>

      {/* Main Catalog View */}
      <main
        ref={resultsSectionRef}
        id="search-results"
        className="flex-1 mx-auto w-full max-w-[1440px] scroll-mt-20 px-4 py-12 sm:px-6 lg:px-8 lg:py-16"
      >
        <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <div className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] text-[var(--theme-primary)]">
              <span className="h-2 w-2 rounded-full bg-[var(--theme-accent)]" aria-hidden="true" />
              Explore the ecosystem
            </div>
            <h2 className="text-2xl font-black tracking-tight text-[var(--theme-text-title)] sm:text-3xl">
              {activeTab === "courses" ? "หลักสูตรที่น่าสนใจ" : activeTab === "advisors" ? "อาจารย์ที่ปรึกษาที่ตรงกับคุณ" : "ห้องวิจัยและศูนย์ความเป็นเลิศ"}
            </h2>
            <p className="mt-2 max-w-2xl text-sm font-medium text-[var(--theme-text-muted)]">
              เลือกดูข้อมูลแบบละเอียด เปรียบเทียบตัวเลือก หรือบันทึกสิ่งที่สนใจไว้กลับมาดูภายหลัง
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-[var(--theme-text-muted)]">
            <Award className="h-4 w-4 text-[var(--theme-accent)]" aria-hidden="true" />
            ข้อมูลคัดสรรจากมหาวิทยาลัยทั่วประเทศ
          </div>
        </div>

        {/* Filter Controls */}
        <div className="mb-7 rounded-3xl border border-[var(--theme-border)] bg-[var(--theme-card)] p-3 shadow-sm sm:p-4">
          <FilterBar
            activeTab={activeTab}
            selectedUni={selectedUni}
            selectedDegree={selectedDegree}
            onSelectUni={(uni) => {
              setSelectedUni(uni);
              executeSearch(searchQuery, uni, selectedDegree);
            }}
            onSelectDegree={(deg) => {
              setSelectedDegree(deg);
              executeSearch(searchQuery, selectedUni, deg);
            }}
          />
        </div>

        {/* Status Error Display */}
        {errorMsg && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-xs sm:text-sm font-semibold flex items-center gap-2 shadow-xs">
            <AlertCircle className="w-4 h-4 text-rose-700 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Results Counter & Meta */}
        <div className="flex items-center justify-between text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold">
          <div>
            <span>แสดงผลลัพธ์: </span>
            <strong className="text-[var(--theme-text-title)] font-black text-sm sm:text-base">
              {activeTab === "courses"
                ? `${courses.length} หลักสูตร`
                : activeTab === "advisors"
                ? `${advisors.length} ท่าน`
                : `${labs.length} ห้องปฏิบัติการ`}
            </strong>
            {searchQuery && (
              <span className="text-[var(--theme-text-muted)]"> สำหรับคำค้นหา &ldquo;{searchQuery}&rdquo;</span>
            )}
          </div>

          {activeTab === "courses" && comparedCourses.length > 0 && (
            <button
              onClick={() => setShowComparisonModal(true)}
              className="text-xs sm:text-sm font-black text-[var(--theme-primary)] hover:underline flex items-center gap-1.5 cursor-pointer bg-[var(--theme-primary-subtle)] px-3.5 py-1.5 rounded-xl border border-[var(--theme-primary-border)]"
            >
              <Scale className="w-4 h-4" />
              <span>เปิดตารางเปรียบเทียบ ({comparedCourses.length})</span>
            </button>
          )}
        </div>

        {/* Loading Spinner Skeleton / Content Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] space-y-4 animate-pulse"
              >
                <div className="flex items-center justify-between">
                  <div className="h-5 w-20 bg-[var(--theme-card-subtle)] rounded-md" />
                  <div className="h-5 w-16 bg-[var(--theme-card-subtle)] rounded-md" />
                </div>
                <div className="h-6 w-3/4 bg-[var(--theme-card-subtle)] rounded-md" />
                <div className="h-4 w-1/2 bg-[var(--theme-card-subtle)] rounded-md" />
                <div className="h-16 w-full bg-[var(--theme-card-subtle)] rounded-xl" />
              </div>
            ))}
          </div>
        ) : activeTab === "courses" ? (
          courses.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {courses.map((c) => (
                <CourseCard
                  key={c.id}
                  course={c}
                  isSaved={savedCourses.includes(c.id)}
                  isCompared={comparedCourses.some((item) => item.id === c.id)}
                  onToggleBookmark={toggleBookmarkCourse}
                  onToggleCompare={toggleCompareCourse}
                  onSelectCourse={(course) => setSelectedCourseForDetail(course)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-16 bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl space-y-3">
              <BookOpen className="w-10 h-10 text-[var(--theme-text-muted)] mx-auto" />
              <h3 className="text-base sm:text-lg font-black text-[var(--theme-text-title)]">
                ไม่พบหลักสูตรการศึกษาที่ตรงกับเงื่อนไข
              </h3>
              <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] max-w-sm mx-auto font-medium">
                ลองปรับลดเงื่อนไข หรือค้นหาด้วยคำหลักอื่น เช่น วิศวกรรมศาสตร์, ปัญญาประดิษฐ์, นิติศาสตร์
              </p>
            </div>
          )
        ) : activeTab === "advisors" ? (
          advisors.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {advisors.map((item) => (
                <AdvisorCard
                  key={item.faculty.id}
                  matchItem={item}
                  isSaved={savedAdvisors.includes(item.faculty.id)}
                  onToggleBookmark={toggleBookmarkAdvisor}
                  onOpenColdEmail={(advisor) => setSelectedAdvisorForEmail(advisor)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-16 bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl space-y-3">
              <Users className="w-10 h-10 text-[var(--theme-text-muted)] mx-auto" />
              <h3 className="text-base sm:text-lg font-black text-[var(--theme-text-title)]">
                ไม่พบคณาจารย์ที่ปรึกษาที่ตรงกับเงื่อนไข
              </h3>
              <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] max-w-sm mx-auto font-medium">
                ลองระบุหัวข้อวิจัยที่กว้างขึ้น หรือเลือกค้นหาทุกมหาวิทยาลัย
              </p>
            </div>
          )
        ) : labs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {labs.map((lab) => (
              <LabCard
                key={lab.id}
                lab={lab}
                onOpenInquiry={(targetLab) => setSelectedLabForInquiry(targetLab)}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl space-y-3">
            <Building2 className="w-10 h-10 text-[var(--theme-text-muted)] mx-auto" />
            <h3 className="text-base sm:text-lg font-black text-[var(--theme-text-title)]">
              ไม่พบห้องปฏิบัติการหรือศูนย์วิจัยที่ตรงกับเงื่อนไข
            </h3>
            <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] max-w-sm mx-auto font-medium">
              ลองระบุคำค้นหาที่กว้างขึ้น เช่น AI, Robotics, Renewable Energy, Clean Energy หรือเลือกค้นหาทุกมหาวิทยาลัย
            </p>
          </div>
        )}
      </main>

      {/* Course Detail In-App Modal */}
      <CourseDetailModal
        course={selectedCourseForDetail}
        isOpen={!!selectedCourseForDetail}
        onClose={() => setSelectedCourseForDetail(null)}
        isSaved={selectedCourseForDetail ? savedCourses.includes(selectedCourseForDetail.id) : false}
        onToggleBookmark={toggleBookmarkCourse}
      />

      {/* Comparison Matrix Modal */}
      <ComparisonModal
        courses={comparedCourses}
        isOpen={showComparisonModal}
        onClose={() => setShowComparisonModal(false)}
        onClearAll={() => setComparedCourses([])}
      />

      {/* Cold Email AI Assistant Modal */}
      {selectedAdvisorForEmail && (
        <ColdEmailModal
          advisor={selectedAdvisorForEmail}
          onClose={() => setSelectedAdvisorForEmail(null)}
        />
      )}

      {/* Lab Inquiry AI Assistant Modal */}
      {selectedLabForInquiry && (
        <LabInquiryModal
          lab={selectedLabForInquiry}
          onClose={() => setSelectedLabForInquiry(null)}
        />
      )}

      {/* Saved Bookmarks Modal */}
      <SavedBookmarksModal
        isOpen={showSavedModal}
        onClose={() => setShowSavedModal(false)}
        savedCourses={savedCourses}
        savedAdvisors={savedAdvisors}
        allCourses={courses}
        allAdvisors={advisors}
        onRemoveCourse={toggleBookmarkCourse}
        onRemoveAdvisor={toggleBookmarkAdvisor}
      />

      {/* 🚀 World-Class Floating Comparison Dock (Apple / Raycast Style) */}
      {activeTab === "courses" && comparedCourses.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 w-[92%] max-w-2xl animate-float">
          <div className="floating-dock p-3 sm:p-4 rounded-2xl flex items-center justify-between gap-3 shadow-2xl">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center flex-shrink-0 shadow-sm">
                <Scale className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs sm:text-sm font-black text-[var(--theme-text-title)]">
                    เปรียบเทียบหลักสูตร ({comparedCourses.length}/4)
                  </span>
                </div>
                <div className="flex items-center gap-1.5 overflow-hidden text-[11px] text-[var(--theme-text-muted)] truncate">
                  {comparedCourses.map((c) => (
                    <span key={c.id} className="truncate max-w-[120px] font-bold">
                      • {c.title_th}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={() => setComparedCourses([])}
                className="px-2.5 py-2 text-xs font-bold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] hover:bg-[var(--theme-card-subtle)] rounded-xl transition cursor-pointer"
              >
                ล้าง
              </button>
              <button
                onClick={() => setShowComparisonModal(true)}
                className="px-4 py-2 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-black flex items-center gap-1.5 shadow-md shadow-[var(--theme-primary-glow)] transition cursor-pointer hover:scale-102 active:scale-98"
              >
                <span>เปิดตารางวิเคราะห์</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Editorial Footer */}
      <Footer />
    </div>
  );
}

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
  GraduationCap,
  Command,
  SlidersHorizontal,
  X,
  ChevronRight
} from "lucide-react";
import { FacultyMember, SearchMatchResult, Course } from "@/types";
import { API_BASE_URL } from "@/lib/config";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { CourseCard } from "@/components/CourseCard";
import { AdvisorCard } from "@/components/AdvisorCard";
import { FilterBar } from "@/components/FilterBar";
import { ComparisonModal } from "@/components/ComparisonModal";
import { ColdEmailModal } from "@/components/ColdEmailModal";
import { SavedBookmarksModal } from "@/components/SavedBookmarksModal";
import { FeaturedProgramsShowcase } from "@/components/FeaturedProgramsShowcase";
import { CourseDetailModal } from "@/components/CourseDetailModal";
import { searchApiCache } from "@/lib/dsa";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"courses" | "advisors">("courses");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDegree, setSelectedDegree] = useState("all");
  const [selectedUni, setSelectedUni] = useState("all");

  const [courses, setCourses] = useState<Course[]>([]);
  const [advisors, setAdvisors] = useState<SearchMatchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchExecuted, setSearchExecuted] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Comparison Matrix State
  const [comparedCourses, setComparedCourses] = useState<Course[]>([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  // Wishlist / Bookmarks State
  const [savedCourses, setSavedCourses] = useState<string[]>([]);
  const [savedAdvisors, setSavedAdvisors] = useState<string[]>([]);
  const [showSavedModal, setShowSavedModal] = useState(false);

  // Selected Course Detail Modal State
  const [selectedCourseForDetail, setSelectedCourseForDetail] = useState<Course | null>(null);

  // Cold Email Modal State
  const [selectedAdvisorForEmail, setSelectedAdvisorForEmail] = useState<FacultyMember | null>(null);

  // Search input ref for keyboard shortcut focus
  const searchInputRef = useRef<HTMLInputElement>(null);

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

  // Load Saved Bookmarks from LocalStorage
  useEffect(() => {
    try {
      const savedC = localStorage.getItem("thai_educenter_saved_courses");
      if (savedC) setSavedCourses(JSON.parse(savedC));
      const savedA = localStorage.getItem("thai_educenter_saved_advisors");
      if (savedA) setSavedAdvisors(JSON.parse(savedA));
    } catch (e) {
      console.warn("Could not load bookmarks from storage");
    }
  }, []);

  // Fetch initial catalog data on load (both courses and faculty advisors)
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [coursesRes, facultyRes] = await Promise.allSettled([
        fetch(`${API_BASE_URL}/courses/?limit=24`),
        fetch(`${API_BASE_URL}/faculty/?limit=24`),
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
    } catch (err) {
      console.warn("Backend loading default catalog data error", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleBookmarkCourse = (id: string) => {
    setSavedCourses((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      try {
        localStorage.setItem("thai_educenter_saved_courses", JSON.stringify(next));
      } catch (e) {}
      return next;
    });
  };

  const toggleBookmarkAdvisor = (id: string) => {
    setSavedAdvisors((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      try {
        localStorage.setItem("thai_educenter_saved_advisors", JSON.stringify(next));
      } catch (e) {}
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

  const executeSearch = async (
    queryText?: string,
    uniFilter?: string,
    degFilter?: string,
    tabOverride?: "courses" | "advisors"
  ) => {
    const queryToUse = queryText !== undefined ? queryText : searchQuery;
    const uniToUse = uniFilter !== undefined ? uniFilter : selectedUni;
    const degToUse = degFilter !== undefined ? degFilter : selectedDegree;
    const currentTab = tabOverride !== undefined ? tabOverride : activeTab;

    const cacheKey = `${currentTab}:${queryToUse.trim()}:${uniToUse}:${degToUse}`;
    const cachedData = searchApiCache.get(cacheKey);
    if (cachedData) {
      if (currentTab === "courses") {
        setCourses(cachedData);
      } else {
        setAdvisors(cachedData);
      }
      setSearchExecuted(true);
      setErrorMsg(null);
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSearchExecuted(true);

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
      } else {
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

      {/* Hero Exploration Section with Clean Minimalist Layout */}
      <section className="relative pt-14 pb-16 px-4 sm:px-6 lg:px-8 border-b border-[var(--theme-border)] bg-[var(--theme-bg)]">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-primary)] text-xs font-bold">
            <Sparkles size={14} className="text-[var(--theme-accent)]" />
            <span>AI-Powered Thai Academic & Research Discovery</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-[var(--theme-text-title)] leading-tight">
            ค้นหาหลักสูตรการศึกษา <br className="hidden sm:inline" />
            <span className="text-[var(--theme-primary)]">
              และอาจารย์ที่ปรึกษางานวิจัย
            </span>
          </h1>

          <p className="text-[var(--theme-text-muted)] text-sm sm:text-base max-w-2xl mx-auto leading-relaxed font-medium">
            สืบค้นข้อมูลหลักสูตรปริญญาตรี ปริญญาโท ปริญญาเอก และจับคู่อาจารย์ที่ปรึกษาวิทยานิพนธ์ด้วย AI จากมหาวิทยาลัยชั้นนำทั่วประเทศไทย
          </p>

          {/* Minimal Tab Selector */}
          <div className="inline-flex p-1 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)]">
            <button
              onClick={() => setActiveTab("courses")}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
                activeTab === "courses"
                  ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-xs"
                  : "text-[var(--theme-text-body)] hover:text-[var(--theme-primary)]"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>หลักสูตรการศึกษา (Curricula)</span>
            </button>

            <button
              onClick={() => setActiveTab("advisors")}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
                activeTab === "advisors"
                  ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-xs"
                  : "text-[var(--theme-text-body)] hover:text-[var(--theme-primary)]"
              }`}
            >
              <Users className="w-4 h-4" />
              <span>อาจารย์ที่ปรึกษางานวิจัย (Advisors)</span>
            </button>
          </div>

          {/* Minimal Clean Search Box */}
          <div className="relative max-w-2xl mx-auto">
            <div className="relative flex items-center group/search">
              <Search className="absolute left-4.5 w-5 h-5 text-[var(--theme-text-muted)] group-focus-within/search:text-[var(--theme-primary)]" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && executeSearch()}
                placeholder={
                  activeTab === "courses"
                    ? "ค้นหาหลักสูตร หรือสาขาวิชา เช่น วิศวกรรมคอมพิวเตอร์, การเงิน, แพทยศาสตร์..."
                    : "ระบุหัวข้อวิจัย หรือความสนใจ เช่น Natural Language Processing, พลังงานหมุนเวียน..."
                }
                className="w-full pl-12 pr-36 py-4 rounded-xl bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] text-sm sm:text-base font-semibold focus:outline-none focus:border-[var(--theme-primary)] focus:ring-1 focus:ring-[var(--theme-primary)] transition-colors"
              />

              {/* Keyboard Shortcut Badge & Action Button */}
              <div className="absolute right-2 flex items-center gap-1.5">
                {!searchQuery && (
                  <span className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[11px] font-mono text-[var(--theme-text-muted)] mr-1">
                    <span>กด</span>
                    <kbd className="font-bold text-[var(--theme-text-title)]">/</kbd>
                  </span>
                )}
                {searchQuery && (
                  <button
                    onClick={() => {
                      setSearchQuery("");
                      searchInputRef.current?.focus();
                    }}
                    className="p-1.5 rounded-md text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] hover:bg-[var(--theme-card-subtle)] transition cursor-pointer"
                    title="ล้างคำค้นหา"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => executeSearch()}
                  disabled={loading}
                  className="px-4.5 py-2.5 rounded-lg bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-bold transition flex items-center gap-2 disabled:opacity-50 cursor-pointer"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  <span>ค้นหา</span>
                </button>
              </div>
            </div>
          </div>

          {/* Popular Search Suggestions */}
          <div className="flex flex-wrap items-center justify-center gap-2.5 pt-1">
            <span className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-black flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-[var(--theme-accent)]" /> หมวดหมู่ยอดนิยม:
            </span>
            {popularTopics.map((t, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setSearchQuery(t.query);
                  executeSearch(t.query);
                }}
                className="px-3.5 py-1.5 rounded-xl bg-[var(--theme-card)]/80 hover:bg-[var(--theme-card)] text-xs font-bold text-[var(--theme-text-body)] border border-[var(--theme-border)] hover:border-[var(--theme-primary)] hover:text-[var(--theme-primary)] shadow-2xs hover:shadow-xs transition-all cursor-pointer"
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Institutional Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 max-w-2xl mx-auto pt-6 border-t border-[var(--theme-border-subtle)]">
            <div className="p-4.5 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] shadow-xs hover:border-[var(--theme-primary)] transition-all">
              <div className="text-2xl sm:text-3xl font-black text-[var(--theme-primary)]">2,800+</div>
              <div className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-bold mt-1">หลักสูตรระดับอุดมศึกษา</div>
            </div>
            <div className="p-4.5 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] shadow-xs hover:border-[var(--theme-accent)] transition-all">
              <div className="text-2xl sm:text-3xl font-black text-[var(--theme-accent)]">1,000+</div>
              <div className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-bold mt-1">อาจารย์และนักวิจัย</div>
            </div>
            <div className="p-4.5 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] shadow-xs col-span-2 sm:col-span-1 hover:border-[var(--theme-primary)] transition-all">
              <div className="text-2xl sm:text-3xl font-black text-[var(--theme-primary)]">25+</div>
              <div className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-bold mt-1">มหาวิทยาลัยชั้นนำ</div>
            </div>
          </div>
        </div>
      </section>

      {/* 🌟 Signature Spotlight / University Highlights Promotional Showcase */}
      <FeaturedProgramsShowcase
        onSelectUniversity={(uniName) => {
          setSelectedUni(uniName);
          setActiveTab("courses");
          executeSearch("", uniName, selectedDegree, "courses");
        }}
        onSelectCourseSearch={(courseTitle) => {
          setSearchQuery(courseTitle);
          setActiveTab("courses");
          executeSearch(courseTitle, selectedUni, selectedDegree, "courses");
        }}
        onSelectCourseDetail={(course) => setSelectedCourseForDetail(course)}
        savedCourses={savedCourses}
        onToggleBookmarkCourse={toggleBookmarkCourse}
      />

      {/* Main Catalog View */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Filter Controls */}
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
              {activeTab === "courses" ? `${courses.length} หลักสูตร` : `${advisors.length} ท่าน`}
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
        ) : advisors.length > 0 ? (
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

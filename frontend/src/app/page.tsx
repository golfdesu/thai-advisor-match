"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  BookOpen,
  Users,
  Loader2,
  Scale,
  TrendingUp,
  AlertCircle
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

  // Cold Email Modal State
  const [selectedAdvisorForEmail, setSelectedAdvisorForEmail] = useState<FacultyMember | null>(null);

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

      {/* Hero Exploration Section */}
      <section className="relative pt-12 pb-16 px-4 sm:px-6 lg:px-8 border-b border-[var(--theme-border)] bg-linear-to-b from-[var(--theme-card)] via-[var(--theme-bg)] to-[var(--theme-card-subtle)]">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-muted)] text-xs font-semibold shadow-2xs">
            <span>ฐานข้อมูลการศึกษาและคณาจารย์ระดับอุดมศึกษาไทย</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-[var(--theme-text-title)] leading-tight">
            ค้นหาหลักสูตรการศึกษา <br className="hidden sm:inline" />
            <span className="text-[var(--theme-primary)] transition-colors">
              และอาจารย์ที่ปรึกษางานวิจัย
            </span>
          </h1>

          <p className="text-[var(--theme-text-muted)] text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
            รวบรวมข้อมูลหลักสูตรปริญญาตรี ปริญญาโท ปริญญาเอก และความเชี่ยวชาญของคณาจารย์จากมหาวิทยาลัยชั้นนำทั่วประเทศ
          </p>

          {/* Tab Selector */}
          <div className="inline-flex p-1 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] shadow-2xs">
            <button
              onClick={() => setActiveTab("courses")}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer ${
                activeTab === "courses"
                  ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-sm"
                  : "text-[var(--theme-text-body)] hover:text-[var(--theme-primary)]"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>หลักสูตรการศึกษา (Curricula)</span>
            </button>

            <button
              onClick={() => setActiveTab("advisors")}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer ${
                activeTab === "advisors"
                  ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-sm"
                  : "text-[var(--theme-text-body)] hover:text-[var(--theme-primary)]"
              }`}
            >
              <Users className="w-4 h-4" />
              <span>อาจารย์ที่ปรึกษางานวิจัย (Advisors)</span>
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative max-w-2xl mx-auto">
            <div className="relative flex items-center">
              <Search className="absolute left-4.5 w-5 h-5 text-[var(--theme-text-muted)]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && executeSearch()}
                placeholder={
                  activeTab === "courses"
                    ? "ค้นหาชื่อหลักสูตร หรือสาขาวิชา เช่น วิศวกรรมคอมพิวเตอร์, การเงิน, แพทยศาสตร์..."
                    : "ระบุหัวข้อวิจัย หรือความสนใจ เช่น Natural Language Processing, พลังงานหมุนเวียน..."
                }
                className="w-full pl-12 pr-28 py-4 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] focus:border-transparent shadow-sm transition-all"
              />
              <button
                onClick={() => executeSearch()}
                disabled={loading}
                className="absolute right-2 px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm disabled:opacity-50 cursor-pointer"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                <span>ค้นหา</span>
              </button>
            </div>
          </div>

          {/* Popular Search Suggestions */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
            <span className="text-xs text-[var(--theme-text-muted)] font-semibold flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-[var(--theme-accent)]" /> หมวดหมู่แนะนำ:
            </span>
            {popularTopics.map((t, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setSearchQuery(t.query);
                  executeSearch(t.query);
                }}
                className="px-3 py-1 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[11px] font-medium text-[var(--theme-text-body)] border border-[var(--theme-border)] hover:border-[var(--theme-primary)] hover:text-[var(--theme-primary)] shadow-2xs transition-all cursor-pointer"
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Institutional Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-w-2xl mx-auto pt-6 border-t border-[var(--theme-border)]">
            <div className="p-3.5 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] shadow-2xs">
              <div className="text-xl font-extrabold text-[var(--theme-primary)]">2,800+</div>
              <div className="text-xs text-[var(--theme-text-muted)] font-medium">หลักสูตรระดับอุดมศึกษา</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] shadow-2xs">
              <div className="text-xl font-extrabold text-[var(--theme-accent)]">1,000+</div>
              <div className="text-xs text-[var(--theme-text-muted)] font-medium">อาจารย์และนักวิจัย</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] shadow-2xs col-span-2 sm:col-span-1">
              <div className="text-xl font-extrabold text-[var(--theme-primary)]">25+</div>
              <div className="text-xs text-[var(--theme-text-muted)] font-medium">มหาวิทยาลัยชั้นนำ</div>
            </div>
          </div>
        </div>
      </section>

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
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-700 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Results Counter & Meta */}
        <div className="flex items-center justify-between text-xs text-[var(--theme-text-muted)]">
          <div>
            <span>แสดงผลลัพธ์: </span>
            <strong className="text-[var(--theme-text-title)]">
              {activeTab === "courses" ? `${courses.length} หลักสูตร` : `${advisors.length} ท่าน`}
            </strong>
            {searchQuery && (
              <span className="text-[var(--theme-text-muted)]"> สำหรับคำค้นหา &ldquo;{searchQuery}&rdquo;</span>
            )}
          </div>

          {activeTab === "courses" && comparedCourses.length > 0 && (
            <button
              onClick={() => setShowComparisonModal(true)}
              className="text-xs font-bold text-[var(--theme-primary)] hover:underline flex items-center gap-1 cursor-pointer"
            >
              <Scale className="w-3.5 h-3.5" />
              <span>เปิดตารางเปรียบเทียบ ({comparedCourses.length})</span>
            </button>
          )}
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center space-y-3 bg-[var(--theme-card)]/60 rounded-3xl border border-[var(--theme-border)]">
            <Loader2 className="w-8 h-8 text-[var(--theme-primary)] animate-spin" />
            <p className="text-xs font-semibold text-[var(--theme-text-muted)]">กำลังประมวลผลข้อมูลการค้นหา...</p>
          </div>
        ) : activeTab === "courses" ? (
          /* COURSES GRID */
          !Array.isArray(courses) || courses.length === 0 ? (
            <div className="p-16 text-center rounded-3xl bg-[var(--theme-card)] border border-[var(--theme-border)] space-y-3 shadow-2xs">
              <BookOpen className="w-10 h-10 text-[var(--theme-text-muted)] mx-auto" />
              <h3 className="text-base font-bold text-[var(--theme-text-title)]">ไม่พบหลักสูตรที่ตรงกับเงื่อนไข</h3>
              <p className="text-xs text-[var(--theme-text-muted)]">
                ลองปรับเปลี่ยนคำค้นหา หรือเลือกตัวกรองระดับการศึกษาใหม่อีกครั้ง
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {courses.map((course) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  isSaved={savedCourses.includes(course.id)}
                  isCompared={comparedCourses.some((c) => c.id === course.id)}
                  onToggleBookmark={toggleBookmarkCourse}
                  onToggleCompare={toggleCompareCourse}
                />
              ))}
            </div>
          )
        ) : (
          /* ADVISORS GRID */
          !Array.isArray(advisors) || advisors.length === 0 ? (
            <div className="p-16 text-center rounded-3xl bg-[var(--theme-card)] border border-[var(--theme-border)] space-y-3 shadow-2xs">
              <Users className="w-10 h-10 text-[var(--theme-text-muted)] mx-auto" />
              <h3 className="text-base font-bold text-[var(--theme-text-title)]">ไม่พบคณาจารย์ที่ตรงกับเงื่อนไข</h3>
              <p className="text-xs text-[var(--theme-text-muted)]">
                ลองระบุหัวข้อวิจัยเป็นภาษาไทยหรืออังกฤษ เช่น &quot;Biomedical Engineering&quot;, &quot;พลังงานแสงอาทิตย์&quot;
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
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
          )
        )}
      </main>

      {/* Floating Comparison Dock */}
      {comparedCourses.length > 0 && (
        <aside className="fixed bottom-6 inset-x-0 mx-auto max-w-xl z-30 px-4">
          <div className="p-3.5 rounded-2xl bg-slate-900/95 backdrop-blur-md text-white shadow-2xl border border-slate-700 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-semibold">
                เลือกเปรียบเทียบ {comparedCourses.length}/4 หลักสูตร
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setComparedCourses([])}
                className="text-[11px] text-slate-400 hover:text-white px-2 py-1 cursor-pointer"
              >
                ล้าง
              </button>
              <button
                onClick={() => setShowComparisonModal(true)}
                className="px-4 py-1.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold shadow-sm flex items-center gap-1.5 cursor-pointer"
              >
                <span>เปิดตารางเปรียบเทียบ</span>
              </button>
            </div>
          </div>
        </aside>
      )}

      {/* Modals */}
      <ComparisonModal
        isOpen={showComparisonModal}
        courses={comparedCourses}
        onClose={() => setShowComparisonModal(false)}
        onClearAll={() => setComparedCourses([])}
      />

      <ColdEmailModal
        advisor={selectedAdvisorForEmail}
        onClose={() => setSelectedAdvisorForEmail(null)}
      />

      <SavedBookmarksModal
        isOpen={showSavedModal}
        savedCourses={savedCourses}
        savedAdvisors={savedAdvisors}
        allCourses={courses}
        allAdvisors={advisors}
        onClose={() => setShowSavedModal(false)}
        onRemoveCourse={toggleBookmarkCourse}
        onRemoveAdvisor={toggleBookmarkAdvisor}
      />

      {/* Editorial Academic Footer */}
      <Footer />
    </div>
  );
}

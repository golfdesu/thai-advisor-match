"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  Search,
  GraduationCap,
  Sparkles,
  Building2,
  BookOpen,
  Users,
  Compass,
  ArrowRight,
  TrendingUp,
  Award,
  CheckCircle2,
  Filter,
  Bookmark,
  ExternalLink,
  ChevronRight,
  School,
  Mail,
  FileText,
  Loader2,
  Copy,
  Check,
  X,
  Send,
  AlertCircle,
  BarChart3,
  Heart,
  Layers,
  Scale,
  Flame,
  Globe,
  SlidersHorizontal,
  ChevronDown,
  Briefcase,
  DollarSign,
  Clock,
  BookCheck,
  Share2,
  Trash2
} from "lucide-react";
import { FacultyMember, SearchMatchResult, Course } from "@/types";
import { API_BASE_URL, getAdvisorAvatarUrl } from "@/lib/config";

// Helper function to infer Selectivity Badge
function getSelectivityBadge(course: Course) {
  const title = (course.title_th + " " + (course.title_en || "")).toLowerCase();
  const uni = (course.university_th + " " + course.university).toLowerCase();

  if (
    title.includes("แพทย์") ||
    title.includes("ทันตแพทย์") ||
    title.includes("medicine") ||
    title.includes("dentistry") ||
    (uni.includes("จุฬา") && (title.includes("วิศวกรรม") || title.includes("พาณิชยศาสตร์") || title.includes("ai"))) ||
    (uni.includes("ธรรมศาสตร์") && (title.includes("นิติศาสตร์") || title.includes("siit") || title.includes("พาณิชยศาสตร์")))
  ) {
    return { label: "การแข่งขันสูงมาก 🔥", color: "bg-rose-100 text-[#5B0F18] border-rose-300 font-semibold" };
  }
  if (
    title.includes("นานาชาติ") ||
    title.includes("international") ||
    title.includes("bascii") ||
    title.includes("balac") ||
    title.includes("bba") ||
    title.includes("ise")
  ) {
    return { label: "หลักสูตรนานาชาติ 🌐", color: "bg-amber-100 text-amber-900 border-amber-300 font-semibold" };
  }
  if (
    title.includes("ดิจิทัล") ||
    title.includes("หุ่นยนต์") ||
    title.includes("ai") ||
    title.includes("data") ||
    title.includes("ภาพยนตร์") ||
    title.includes("ศิลปกรรม")
  ) {
    return { label: "เน้นทักษะ & Portfolio 🎨", color: "bg-orange-100 text-orange-900 border-orange-300 font-semibold" };
  }
  return { label: "รับตรง / Admission ทั่วไป 🎯", color: "bg-stone-100 text-stone-800 border-stone-300 font-semibold" };
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<"courses" | "advisors">("courses");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDegree, setSelectedDegree] = useState("all");
  const [selectedUni, setSelectedUni] = useState("all");
  const [selectedDiscipline, setSelectedDiscipline] = useState("all");

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
  const [emailPurpose, setEmailPurpose] = useState("thesis_inquiry");
  const [studentName, setStudentName] = useState("");
  const [studentBackground, setStudentBackground] = useState("");
  const [researchTopic, setResearchTopic] = useState("");
  const [intendedDegree, setIntendedDegree] = useState("Master's Degree");
  const [emailLanguage, setEmailLanguage] = useState<"th" | "en">("th");
  const [generatedEmail, setGeneratedEmail] = useState<{ subject: string; body: string; tips: string[] } | null>(null);
  const [emailLoading, setEmailLoading] = useState(false);
  const [copied, setCopied] = useState(false);

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

  // Fetch initial courses from API on load
  useEffect(() => {
    fetchInitialCourses();
  }, []);

  const fetchInitialCourses = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/courses/?limit=24`);
      if (res.ok) {
        const data = await res.json();
        setCourses(data);
      }
    } catch (err) {
      console.warn("Backend loading default sample courses");
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

  const executeSearch = async (queryText?: string, uniFilter?: string, degFilter?: string, tabOverride?: "courses" | "advisors") => {
    const queryToUse = queryText !== undefined ? queryText : searchQuery;
    const uniToUse = uniFilter !== undefined ? uniFilter : selectedUni;
    const degToUse = degFilter !== undefined ? degFilter : selectedDegree;
    const currentTab = tabOverride !== undefined ? tabOverride : activeTab;

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
          setCourses(Array.isArray(data) ? data : (data.results ?? []));
        } else {
          setErrorMsg("ไม่พบหลักสูตรที่ตรงกับคำค้นหา ลองปรับเปลี่ยนคำค้นหาอีกครั้งครับ");
        }
      } else {
        if (!queryToUse.trim()) {
          const res = await fetch(`${API_BASE_URL}/faculty/?limit=20`);
          if (res.ok) {
            const data = await res.json();
            const list = Array.isArray(data) ? data : (data.results ?? []);
            setAdvisors(list.map((f: FacultyMember) => ({ faculty: f, match_score: 90 })));
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
            setAdvisors(Array.isArray(data) ? data : (data.results ?? []));
          } else {
            setErrorMsg("เกิดข้อผิดพลาดในการจับคู่อาจารย์ที่ปรึกษา AI กรุณาลองใหม่อีกครั้ง");
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

  const handleGenerateColdEmail = async () => {
    if (!selectedAdvisorForEmail) return;
    setEmailLoading(true);
    setGeneratedEmail(null);

    try {
      const res = await fetch(`${API_BASE_URL}/search/cold-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          faculty_id: selectedAdvisorForEmail.id,
          student_name: studentName.trim() || "นักศึกษาผู้สนใจ",
          student_background: studentBackground.trim() || "นักศึกษาที่มีความสนใจด้านงานวิจัย",
          research_topic: researchTopic.trim() || selectedAdvisorForEmail.research_interests?.[0] || "หัวข้อวิจัยที่สอดคล้องกับความเชี่ยวชาญ",
          intended_degree: intendedDegree,
          language: emailLanguage,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setGeneratedEmail(data);
      } else {
        alert("ไม่สามารถสร้างอีเมลได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง");
      }
    } catch (e) {
      alert("เกิดข้อผิดพลาดในการสร้างอีเมล");
    } finally {
      setEmailLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!generatedEmail) return;
    const fullText = `หัวข้อ: ${generatedEmail.subject}\n\n${generatedEmail.body}`;
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Trending Queries & Quick Filters
  const trendingTags = [
    { label: "🩺 แพทย์ & ทันตะ กสพท", query: "แพทยศาสตร์ ทันตแพทยศาสตร์ กสพท" },
    { label: "🤖 วิศวะหุ่นยนต์ & AI", query: "วิศวกรรมหุ่นยนต์ ปัญญาประดิษฐ์ AI" },
    { label: "💡 BAScii & ScII จุฬาฯ", query: "BAScii นวัตกรรมบูรณาการ จุฬาลงกรณ์" },
    { label: "📊 Data Science & Cyber", query: "วิทยาการข้อมูล ความมั่นคงไซเบอร์ Data Science" },
    { label: "🎬 ภาพยนตร์ & สื่อดิจิทัล", query: "ภาพยนตร์และสื่อดิจิทัล นิเทศศาสตร์" },
    { label: "💼 BBA & Sasin MBA", query: "บริหารธุรกิจ BBA Sasin MBA" },
    { label: "🌊 ทางทะเล & โลจิสติกส์", query: "วิทยาศาสตร์ทางทะเล โลจิสติกส์พาณิชยนาวี" },
  ];

  return (
    <div className="min-h-screen bg-[#F8F1E7] text-stone-800 flex flex-col selection:bg-[#5B0F18] selection:text-white font-sans antialiased">
      {/* Top Banner Navigation */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[#F8F1E7]/90 border-b border-stone-300 px-4 lg:px-8 py-3.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#5B0F18] flex items-center justify-center shadow-md text-white">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight text-[#5B0F18]">Thai EduCenter</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-rose-100 text-[#5B0F18] border border-rose-300">
                AI Discovery
              </span>
            </div>
            <p className="text-xs text-stone-600">ระบบค้นหาหลักสูตรและจับคู่อาจารย์ที่ปรึกษา AI ทั่วประเทศ</p>
          </div>
        </div>

        <nav className="flex items-center gap-3">
          <Link
            href="/career-discovery"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white hover:bg-stone-50 text-xs font-bold text-stone-700 border border-stone-300 transition-all hover:border-[#5B0F18] shadow-sm"
          >
            <Compass className="w-4 h-4 text-amber-600 animate-spin-slow" />
            <span className="hidden sm:inline">แบบทดสอบอาชีพ</span> RIASEC Quiz
          </Link>

          <button
            onClick={() => setShowSavedModal(true)}
            className="relative flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white hover:bg-stone-50 text-xs font-bold text-stone-700 border border-stone-300 transition-all hover:border-[#5B0F18] shadow-sm"
          >
            <Bookmark className="w-4 h-4 text-[#5B0F18]" />
            <span className="hidden sm:inline">รายการที่บันทึก</span>
            {(savedCourses.length > 0 || savedAdvisors.length > 0) && (
              <span className="w-5 h-5 rounded-full bg-[#5B0F18] text-white text-[10px] font-bold flex items-center justify-center">
                {savedCourses.length + savedAdvisors.length}
              </span>
            )}
          </button>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16 px-4 lg:px-8 border-b border-stone-300 bg-gradient-to-b from-[#F8F1E7] to-[#EFE4D2]">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-rose-100/80 border border-rose-300 text-[#5B0F18] text-xs font-bold shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#5B0F18]" />
            <span>AI Semantic Match 2.0 • ดัชนีหลักสูตรและอาจารย์ระดับประเทศ</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-stone-900 leading-tight">
            ค้นพบหลักสูตรและอาจารย์ที่ปรึกษา <br className="hidden sm:inline" />
            <span className="text-[#5B0F18]">
              ที่ตรงกับอนาคตและงานวิจัยของคุณ
            </span>
          </h1>

          <p className="text-stone-700 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed font-medium">
            สำรวจกว่า 2,800+ หลักสูตร ป.ตรี ป.โท ป.เอก และจับคู่อาจารย์ที่ปรึกษากว่า 1,000+ ท่าน จากมหาวิทยาลัยชั้นนำทั่วไทยด้วย AI Vector Embedding
          </p>

          {/* Tab Switcher */}
          <div className="inline-flex p-1.5 rounded-2xl bg-stone-200/80 border border-stone-300 shadow-inner">
            <button
              onClick={() => {
                setActiveTab("courses");
                executeSearch(searchQuery, selectedUni, selectedDegree, "courses");
              }}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                activeTab === "courses"
                  ? "bg-[#5B0F18] text-white shadow-md"
                  : "text-stone-700 hover:text-[#5B0F18]"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              ค้นหาหลักสูตร (Courses)
            </button>

            <button
              onClick={() => {
                setActiveTab("advisors");
                executeSearch(searchQuery, selectedUni, selectedDegree, "advisors");
              }}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                activeTab === "advisors"
                  ? "bg-[#5B0F18] text-white shadow-md"
                  : "text-stone-700 hover:text-[#5B0F18]"
              }`}
            >
              <Users className="w-4 h-4" />
              แมตช์อาจารย์ที่ปรึกษา (Advisor AI)
            </button>
          </div>

          {/* Search Box */}
          <div className="relative max-w-2xl mx-auto">
            <div className="relative flex items-center">
              <Search className="absolute left-4 w-5 h-5 text-stone-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && executeSearch()}
                placeholder={
                  activeTab === "courses"
                    ? "ค้นหาหลักสูตร เช่น วิศวะ AI, แพทยศาสตร์, BAScii, Data Science..."
                    : "พิมพ์หัวข้อวิจัย/วิทยานิพนธ์ เช่น การประมวลผลภาษาไทย NLP, หุ่นยนต์การแพทย์..."
                }
                className="w-full pl-12 pr-28 py-4 rounded-2xl bg-white border border-stone-300 text-stone-900 placeholder-stone-400 text-sm focus:outline-none focus:ring-2 focus:ring-[#5B0F18] focus:border-transparent shadow-md transition-all"
              />
              <button
                onClick={() => executeSearch()}
                disabled={loading}
                className="absolute right-2 px-4 py-2.5 rounded-xl bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-md disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>ค้นหา</span>
              </button>
            </div>
          </div>

          {/* Trending Search Chips */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            <span className="text-xs text-stone-600 font-bold flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-[#5B0F18]" /> ยอดฮิต:
            </span>
            {trendingTags.map((t, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setSearchQuery(t.query);
                  executeSearch(t.query);
                }}
                className="px-3 py-1 rounded-full bg-white hover:bg-rose-50 text-[11px] font-semibold text-stone-700 border border-stone-300 hover:border-[#5B0F18] hover:text-[#5B0F18] shadow-xs transition-all"
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Live System Counter Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-3xl mx-auto pt-6 border-t border-stone-300">
            <div className="p-3.5 rounded-2xl bg-white border border-stone-200 shadow-xs">
              <div className="text-xl font-extrabold text-[#5B0F18]">2,808+</div>
              <div className="text-xs text-stone-600 font-medium">หลักสูตรมาตรฐาน</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-white border border-stone-200 shadow-xs">
              <div className="text-xl font-extrabold text-[#5B0F18]">1,009+</div>
              <div className="text-xs text-stone-600 font-medium">อาจารย์ที่ปรึกษา</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-white border border-stone-200 shadow-xs">
              <div className="text-xl font-extrabold text-[#5B0F18]">25+</div>
              <div className="text-xs text-stone-600 font-medium">มหาวิทยาลัยชั้นนำ</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-white border border-stone-200 shadow-xs">
              <div className="text-xl font-extrabold text-emerald-700">100%</div>
              <div className="text-xs text-stone-600 font-medium">AI เวกเตอร์ความแม่นยำ</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 lg:px-8 py-8 space-y-6">
        {/* Filter Controls Bar */}
        <div className="p-4 rounded-2xl bg-white border border-stone-300 shadow-sm flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-bold text-stone-700">
              <SlidersHorizontal className="w-4 h-4 text-[#5B0F18]" />
              <span>ตัวกรอง:</span>
            </div>

            {/* University Dropdown */}
            <select
              value={selectedUni}
              onChange={(e) => {
                setSelectedUni(e.target.value);
                executeSearch(searchQuery, e.target.value, selectedDegree);
              }}
              className="px-3 py-1.5 rounded-lg bg-stone-50 border border-stone-300 text-xs text-stone-800 font-medium focus:outline-none focus:ring-1 focus:ring-[#5B0F18]"
            >
              <option value="all">ทุกมหาวิทยาลัย (All Universities)</option>
              <option value="จุฬาลงกรณ์มหาวิทยาลัย">จุฬาลงกรณ์มหาวิทยาลัย (CU)</option>
              <option value="มหาวิทยาลัยมหิดล">มหาวิทยาลัยมหิดล (MU)</option>
              <option value="มหาวิทยาลัยธรรมศาสตร์">มหาวิทยาลัยธรรมศาสตร์ (TU)</option>
              <option value="มหาวิทยาลัยเชียงใหม่">มหาวิทยาลัยเชียงใหม่ (CMU)</option>
              <option value="มหาวิทยาลัยเกษตรศาสตร์">มหาวิทยาลัยเกษตรศาสตร์ (KU)</option>
              <option value="มหาวิทยาลัยขอนแก่น">มหาวิทยาลัยขอนแก่น (KKU)</option>
              <option value="มหาวิทยาลัยสงขลานครินทร์">มหาวิทยาลัยสงขลานครินทร์ (PSU)</option>
              <option value="มหาวิทยาลัยเทคโนโลยีสุรนารี">มหาวิทยาลัยเทคโนโลยีสุรนารี (SUT)</option>
              <option value="สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง">สจล. ลาดกระบัง (KMITL)</option>
              <option value="มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี">มจธ. บางมด (KMUTT)</option>
              <option value="มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ">มจพ. พระนครเหนือ (KMUTNB)</option>
              <option value="มหาวิทยาลัยศรีนครินทรวิโรฒ">มศว (SWU)</option>
              <option value="มหาวิทยาลัยศิลปากร">มหาวิทยาลัยศิลปากร (SU)</option>
              <option value="มหาวิทยาลัยบูรพา">มหาวิทยาลัยบูรพา (BUU)</option>
              <option value="มหาวิทยาลัยนเรศวร">มหาวิทยาลัยนเรศวร (NU)</option>
              <option value="มหาวิทยาลัยแม่ฟ้าหลวง">มหาวิทยาลัยแม่ฟ้าหลวง (MFU)</option>
              <option value="มหาวิทยาลัยพะเยา">มหาวิทยาลัยพะเยา (UP)</option>
              <option value="มหาวิทยาลัยรังสิต">มหาวิทยาลัยรังสิต (RSU)</option>
              <option value="มหาวิทยาลัยกรุงเทพ">มหาวิทยาลัยกรุงเทพ (BU)</option>
            </select>

            {/* Degree Level Filter */}
            {activeTab === "courses" && (
              <div className="flex items-center gap-1 p-0.5 rounded-lg bg-stone-100 border border-stone-200">
                {[
                  { id: "all", label: "ทุกระดับ" },
                  { id: "ปริญญาตรี", label: "ป.ตรี" },
                  { id: "ปริญญาโท", label: "ป.โท" },
                  { id: "ปริญญาเอก", label: "ป.เอก" },
                ].map((deg) => (
                  <button
                    key={deg.id}
                    onClick={() => {
                      setSelectedDegree(deg.id);
                      executeSearch(searchQuery, selectedUni, deg.id);
                    }}
                    className={`px-3 py-1 rounded-md text-[11px] font-bold transition-all ${
                      selectedDegree === deg.id
                        ? "bg-[#5B0F18] text-white shadow-xs"
                        : "text-stone-600 hover:text-stone-900"
                    }`}
                  >
                    {deg.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Right side stats & comparison launcher */}
          <div className="flex items-center gap-3">
            {comparedCourses.length > 0 && (
              <button
                onClick={() => setShowComparisonModal(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold shadow-sm transition-all animate-pulse"
              >
                <Scale className="w-3.5 h-3.5" />
                <span>เปรียบเทียบ ({comparedCourses.length}/4)</span>
              </button>
            )}

            <div className="text-xs text-stone-600 font-medium">
              พบ <span className="font-extrabold text-[#5B0F18]">{activeTab === "courses" ? courses.length : advisors.length}</span> รายการ
            </div>
          </div>
        </div>

        {/* Error Message Alert */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-3">
            <AlertCircle className="w-4 h-4 text-[#5B0F18] flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Search Results Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map((idx) => (
              <div key={idx} className="p-5 rounded-2xl bg-white border border-stone-200 space-y-4 animate-pulse">
                <div className="h-4 bg-stone-200 rounded w-1/3" />
                <div className="h-6 bg-stone-200 rounded w-4/5" />
                <div className="h-16 bg-stone-100 rounded w-full" />
                <div className="flex gap-2">
                  <div className="h-5 bg-stone-200 rounded w-16" />
                  <div className="h-5 bg-stone-200 rounded w-20" />
                </div>
              </div>
            ))}
          </div>
        ) : activeTab === "courses" ? (
          /* COURSES LIST */
          !Array.isArray(courses) || courses.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white border border-stone-200 space-y-3 shadow-xs">
              <BookOpen className="w-10 h-10 text-stone-400 mx-auto" />
              <h3 className="text-base font-bold text-stone-800">ไม่พบหลักสูตรที่ตรงกับเงื่อนไข</h3>
              <p className="text-xs text-stone-500">ลองปรับเปลี่ยนคำค้นหา หรือเลือกตัวกรองมหาวิทยาลัยเป็น &quot;ทุกมหาวิทยาลัย&quot;</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {courses.map((course) => {
                const badge = getSelectivityBadge(course);
                const isCompared = comparedCourses.some((c) => c.id === course.id);
                const isSaved = savedCourses.includes(course.id);

                return (
                  <div
                    key={course.id}
                    className={`group relative p-5 rounded-2xl bg-white border transition-all flex flex-col justify-between hover:shadow-lg hover:-translate-y-0.5 ${
                      isCompared ? "border-[#5B0F18] ring-2 ring-[#5B0F18]/20" : "border-stone-200 hover:border-stone-400"
                    }`}
                  >
                    <div className="space-y-3">
                      {/* Top Badges */}
                      <div className="flex items-center justify-between gap-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badge.color}`}>
                          {badge.label}
                        </span>

                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => toggleCompareCourse(course)}
                            title="เปรียบเทียบหลักสูตร"
                            className={`p-1.5 rounded-lg border text-xs transition-all ${
                              isCompared
                                ? "bg-[#5B0F18] border-[#5B0F18] text-white"
                                : "bg-stone-50 border-stone-200 text-stone-600 hover:text-stone-900"
                            }`}
                          >
                            <Scale className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => toggleBookmarkCourse(course.id)}
                            title="บันทึกรายการโปรด"
                            className={`p-1.5 rounded-lg border text-xs transition-all ${
                              isSaved
                                ? "bg-rose-50 border-rose-300 text-rose-600"
                                : "bg-stone-50 border-stone-200 text-stone-600 hover:text-stone-900"
                            }`}
                          >
                            <Heart className={`w-3.5 h-3.5 ${isSaved ? "fill-rose-600 text-rose-600" : ""}`} />
                          </button>
                        </div>
                      </div>

                      {/* Course Title & Degree */}
                      <div>
                        <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#5B0F18]">
                          <span>{course.degree_level}</span>
                          {course.degree_name && <span>• {course.degree_name}</span>}
                        </div>
                        <h3 className="text-sm font-bold text-stone-900 group-hover:text-[#5B0F18] transition-colors leading-snug line-clamp-2 mt-0.5">
                          {course.title_th}
                        </h3>
                        {course.title_en && (
                          <p className="text-[11px] text-stone-500 italic line-clamp-1 mt-0.5">{course.title_en}</p>
                        )}
                      </div>

                      {/* University & Faculty */}
                      <div className="flex items-center gap-2 text-xs text-stone-600">
                        <Building2 className="w-3.5 h-3.5 text-stone-400 flex-shrink-0" />
                        <span className="truncate">
                          {course.university_th} • {course.faculty_th}
                        </span>
                      </div>

                      {/* Tuition & Duration Meta */}
                      <div className="grid grid-cols-2 gap-2 p-2.5 rounded-xl bg-stone-50 border border-stone-200 text-[11px]">
                        <div>
                          <span className="text-stone-500 block text-[10px]">ค่าเทอม / ภาคเรียน:</span>
                          <span className="font-bold text-emerald-800">
                            {course.tuition_per_semester || "ตามประกาศมหาวิทยาลัย"}
                          </span>
                        </div>
                        <div>
                          <span className="text-stone-500 block text-[10px]">ระยะเวลา / หน่วยกิต:</span>
                          <span className="font-bold text-stone-700">
                            {course.duration_years || "4 ปี"} {course.total_credits ? `(${course.total_credits})` : ""}
                          </span>
                        </div>
                      </div>

                      {/* Highlights */}
                      {course.curriculum_highlights && course.curriculum_highlights.length > 0 && (
                        <p className="text-xs text-stone-600 line-clamp-2 leading-relaxed">
                          {course.curriculum_highlights[0]}
                        </p>
                      )}
                    </div>

                    {/* Bottom Actions */}
                    <div className="pt-4 mt-3 border-t border-stone-100 flex items-center justify-between">
                      {course.career_paths && course.career_paths.length > 0 ? (
                        <span className="text-[10px] text-stone-600 truncate max-w-[180px] font-medium">
                          🎯 {course.career_paths[0]}
                        </span>
                      ) : (
                        <span className="text-[10px] text-stone-400">หลักสูตรมาตรฐาน</span>
                      )}

                      {course.website_url ? (
                        <a
                          href={course.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-bold text-[#5B0F18] hover:underline transition-colors"
                        >
                          <span>ดูรายละเอียด</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="text-xs text-stone-400">ข้อมูลทางการ</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )
        ) : (
          /* ADVISORS LIST */
          !Array.isArray(advisors) || advisors.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white border border-stone-200 space-y-3 shadow-xs">
              <Users className="w-10 h-10 text-stone-400 mx-auto" />
              <h3 className="text-base font-bold text-stone-800">ไม่พบอาจารย์ที่ปรึกษาที่ตรงกับหัวข้อ</h3>
              <p className="text-xs text-stone-500">ลองพิมพ์คำค้นหาเป็นภาษาไทยหรืออังกฤษ เช่น &quot;Natural Language Processing&quot;, &quot;พลังงานสะอาด&quot;</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {advisors.map((item) => {
                const f = item.faculty;
                const isSaved = savedAdvisors.includes(f.id);

                return (
                  <div
                    key={f.id}
                    className="group relative p-5 rounded-2xl bg-white border border-stone-200 hover:border-[#5B0F18] transition-all flex flex-col justify-between hover:shadow-lg hover:-translate-y-0.5"
                  >
                    <div className="space-y-4">
                      {/* Top Header Avatar & Match Score */}
                      <div className="flex items-start justify-between gap-3">
                        <Link
                          href={`/advisor/${f.id}`}
                          className="flex items-center gap-3 flex-1 min-w-0 hover:opacity-90 transition group/avatar"
                        >
                          <img
                            src={f.image_url || getAdvisorAvatarUrl(f.first_name)}
                            alt={f.full_name_th}
                            loading="lazy"
                            decoding="async"
                            onError={(e) => {
                              (e.target as HTMLImageElement).src = getAdvisorAvatarUrl(f.first_name);
                            }}
                            className="w-12 h-12 rounded-xl object-cover border border-stone-200 bg-stone-100 flex-shrink-0 group-hover/avatar:scale-105 transition-transform"
                          />
                          <div className="min-w-0">
                            <span className="text-[10px] font-bold text-[#5B0F18] block truncate max-w-[150px]">
                              {f.academic_title_th || "อาจารย์"}
                            </span>
                            <h3 className="text-sm font-bold text-stone-900 group-hover:text-[#5B0F18] transition-colors leading-snug truncate">
                              {f.full_name_th || `${f.first_name} ${f.last_name}`}
                            </h3>
                            <p className="text-[11px] text-stone-500 truncate max-w-[160px]">
                              {f.university_th}
                            </p>
                          </div>
                        </Link>

                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          {item.match_score && (
                            <span className="px-2 py-1 rounded-lg bg-rose-50 border border-rose-200 text-[#5B0F18] text-xs font-extrabold flex items-center gap-1">
                              <Sparkles className="w-3 h-3 text-[#5B0F18]" />
                              {item.match_score}%
                            </span>
                          )}

                          <button
                            onClick={() => toggleBookmarkAdvisor(f.id)}
                            className={`p-1.5 rounded-lg border text-xs transition-all ${
                              isSaved
                                ? "bg-rose-50 border-rose-300 text-rose-600"
                                : "bg-stone-50 border-stone-200 text-stone-600 hover:text-stone-900"
                            }`}
                          >
                            <Heart className={`w-3.5 h-3.5 ${isSaved ? "fill-rose-600 text-rose-600" : ""}`} />
                          </button>
                        </div>
                      </div>

                      {/* Faculty & Department */}
                      <div className="text-xs text-stone-600 flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-stone-400 flex-shrink-0" />
                        <span className="truncate">{f.faculty_th} • {f.department_th}</span>
                      </div>

                      {/* Research Interests Tags */}
                      {f.research_interests && f.research_interests.length > 0 && (
                        <div className="space-y-1.5">
                          <span className="text-[10px] uppercase font-bold tracking-wider text-stone-500">สาขาความเชี่ยวชาญ:</span>
                          <div className="flex flex-wrap gap-1.5">
                            {f.research_interests.slice(0, 3).map((ri, rIdx) => (
                              <span
                                key={rIdx}
                                className="px-2 py-0.5 rounded-md bg-stone-100 border border-stone-200 text-[11px] text-stone-700 font-medium"
                              >
                                {ri}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* AI Match Explanation */}
                      {item.ai_explanation && (
                        <div className="p-2.5 rounded-xl bg-rose-50/70 border border-rose-200 text-[11px] text-stone-700 leading-relaxed">
                          💡 <span className="font-bold text-[#5B0F18]">ทำไมถึงแมตช์:</span> {item.ai_explanation}
                        </div>
                      )}
                    </div>

                    {/* Bottom Actions */}
                    <div className="pt-4 mt-3 border-t border-stone-100 flex items-center justify-between gap-2">
                      <Link
                        href={`/advisor/${f.id}`}
                        className="text-xs font-bold text-stone-600 hover:text-[#5B0F18] transition-colors"
                      >
                        ดูประวัติเต็ม
                      </Link>

                      <button
                        onClick={() => {
                          setSelectedAdvisorForEmail(f);
                          setResearchTopic(searchQuery || f.research_interests?.[0] || "");
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold transition-all shadow-sm"
                      >
                        <Mail className="w-3.5 h-3.5" />
                        <span>ติดต่อ AI Email</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )
        )}
      </main>

      {/* FLOATING COMPARISON DOCK */}
      {comparedCourses.length > 0 && (
        <aside aria-label="แถบเปรียบเทียบหลักสูตร" className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 w-[95%] max-w-2xl p-3.5 rounded-2xl bg-white/95 border border-stone-300 shadow-2xl backdrop-blur-xl flex items-center justify-between gap-3 animate-in fade-in slide-in-from-bottom-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#5B0F18] text-white flex items-center justify-center font-bold text-sm shadow-md">
              {comparedCourses.length}
            </div>
            <div>
              <div className="text-xs font-bold text-stone-900">กำลังเปรียบเทียบหลักสูตร ({comparedCourses.length}/4)</div>
              <div className="text-[11px] text-stone-500 truncate max-w-[280px]">
                {comparedCourses.map((c) => c.title_th).join(", ")}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setComparedCourses([])}
              className="p-2 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-600 text-xs"
              title="ล้างทั้งหมด"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowComparisonModal(true)}
              className="px-4 py-2 rounded-xl bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold shadow-md flex items-center gap-1.5"
            >
              <Scale className="w-3.5 h-3.5" />
              <span>เปิดตารางเปรียบเทียบ</span>
            </button>
          </div>
        </aside>
      )}

      {/* COMPARISON MATRIX MODAL */}
      {showComparisonModal && (
        <div className="fixed inset-0 z-50 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-stone-300 rounded-3xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95">
            {/* Header */}
            <div className="px-6 py-4 border-b border-stone-200 flex items-center justify-between bg-stone-50">
              <div className="flex items-center gap-2.5">
                <Scale className="w-5 h-5 text-[#5B0F18]" />
                <h2 className="text-base font-bold text-stone-900">ตารางเปรียบเทียบหลักสูตร (Course Comparison Matrix)</h2>
              </div>
              <button
                onClick={() => setShowComparisonModal(false)}
                className="p-1.5 rounded-lg bg-white hover:bg-stone-100 text-stone-500 hover:text-stone-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Matrix Content Table */}
            <div className="flex-1 overflow-auto p-6">
              <div className="min-w-[700px]">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-stone-200">
                      <th className="p-3 text-stone-700 font-bold w-1/5 bg-stone-100 rounded-l-xl">เกณฑ์การเปรียบเทียบ</th>
                      {comparedCourses.map((c) => (
                        <th key={c.id} className="p-3 text-stone-900 font-bold w-1/5">
                          <div className="space-y-1">
                            <span className="text-[10px] font-bold text-[#5B0F18] block">{c.university_th}</span>
                            <span className="line-clamp-2">{c.title_th}</span>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-200 text-stone-700">
                    <tr>
                      <td className="p-3 font-bold text-stone-700 bg-stone-50">ระดับปริญญา</td>
                      {comparedCourses.map((c) => (
                        <td key={c.id} className="p-3 font-bold text-[#5B0F18]">
                          {c.degree_level} {c.degree_name ? `(${c.degree_name})` : ""}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-bold text-stone-700 bg-stone-50">คณะ / ภาควิชา</td>
                      {comparedCourses.map((c) => (
                        <td key={c.id} className="p-3 font-medium">
                          {c.faculty_th} <br />
                          <span className="text-stone-500 text-[11px]">{c.department_th || "-"}</span>
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-bold text-stone-700 bg-stone-50">ค่าเทอม / ภาคเรียน</td>
                      {comparedCourses.map((c) => (
                        <td key={c.id} className="p-3 font-bold text-emerald-800">
                          {c.tuition_per_semester || "ตามประกาศมหาวิทยาลัย"}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-bold text-stone-700 bg-stone-50">ระยะเวลา & หน่วยกิต</td>
                      {comparedCourses.map((c) => (
                        <td key={c.id} className="p-3 font-medium">
                          {c.duration_years || "4 ปี"} / {c.total_credits || "ตามโครงสร้าง"}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-bold text-stone-700 bg-stone-50">ระดับการแข่งขัน</td>
                      {comparedCourses.map((c) => {
                        const badge = getSelectivityBadge(c);
                        return (
                          <td key={c.id} className="p-3">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badge.color}`}>
                              {badge.label}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                    <tr>
                      <td className="p-3 font-bold text-stone-700 bg-stone-50">จุดเด่นหลักสูตร</td>
                      {comparedCourses.map((c) => (
                        <td key={c.id} className="p-3 text-[11px] text-stone-700 leading-relaxed">
                          {c.curriculum_highlights && c.curriculum_highlights.length > 0 ? (
                            <ul className="list-disc list-inside space-y-1">
                              {c.curriculum_highlights.slice(0, 2).map((h, i) => (
                                <li key={i}>{h}</li>
                              ))}
                            </ul>
                          ) : (
                            "-"
                          )}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-bold text-stone-700 bg-stone-50">เส้นทางอาชีพ</td>
                      {comparedCourses.map((c) => (
                        <td key={c.id} className="p-3 text-[11px] text-stone-700 font-medium">
                          {c.career_paths && c.career_paths.length > 0 ? c.career_paths.join(", ") : "-"}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-3 font-bold text-stone-700 bg-stone-50">ลิงก์เว็บไซต์ทางการ</td>
                      {comparedCourses.map((c) => (
                        <td key={c.id} className="p-3">
                          {c.website_url ? (
                            <a
                              href={c.website_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[#5B0F18] font-bold hover:underline inline-flex items-center gap-1"
                            >
                              <span>เข้าสู่เว็บไซต์</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            "-"
                          )}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-stone-200 bg-stone-50 flex items-center justify-between">
              <button
                onClick={() => setComparedCourses([])}
                className="text-xs text-rose-700 font-bold hover:underline"
              >
                ล้างการเปรียบเทียบทั้งหมด
              </button>
              <button
                onClick={() => setShowComparisonModal(false)}
                className="px-5 py-2 rounded-xl bg-stone-800 hover:bg-stone-900 text-white text-xs font-bold"
              >
                ปิดหน้าต่าง
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SAVED ITEMS / BOOKMARKS MODAL */}
      {showSavedModal && (
        <div className="fixed inset-0 z-50 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-stone-300 rounded-3xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95">
            <div className="px-6 py-4 border-b border-stone-200 flex items-center justify-between bg-stone-50">
              <div className="flex items-center gap-2">
                <Bookmark className="w-5 h-5 text-[#5B0F18]" />
                <h2 className="text-base font-bold text-stone-900">รายการที่บันทึกไว้ (Saved Bookmarks)</h2>
              </div>
              <button
                onClick={() => setShowSavedModal(false)}
                className="p-1.5 rounded-lg bg-white hover:bg-stone-100 text-stone-500 hover:text-stone-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-6 space-y-4">
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-stone-600 uppercase tracking-wider">
                  หลักสูตรที่บันทึก ({savedCourses.length})
                </h4>
                {savedCourses.length === 0 ? (
                  <p className="text-xs text-stone-500 italic">ยังไม่มีหลักสูตรที่บันทึกไว้</p>
                ) : (
                  <div className="space-y-2">
                    {savedCourses.map((id) => (
                      <div key={id} className="p-3 rounded-xl bg-stone-50 border border-stone-200 flex items-center justify-between">
                        <span className="text-xs font-semibold text-stone-800">ID: {id}</span>
                        <button
                          onClick={() => toggleBookmarkCourse(id)}
                          className="text-xs text-rose-700 font-bold hover:underline"
                        >
                          ลบออก
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2 pt-4 border-t border-stone-200">
                <h4 className="text-xs font-bold text-stone-600 uppercase tracking-wider">
                  อาจารย์ที่ปรึกษาที่บันทึก ({savedAdvisors.length})
                </h4>
                {savedAdvisors.length === 0 ? (
                  <p className="text-xs text-stone-500 italic">ยังไม่มีอาจารย์ที่บันทึกไว้</p>
                ) : (
                  <div className="space-y-2">
                    {savedAdvisors.map((id) => (
                      <div key={id} className="p-3 rounded-xl bg-stone-50 border border-stone-200 flex items-center justify-between">
                        <span className="text-xs font-semibold text-stone-800">ID: {id}</span>
                        <button
                          onClick={() => toggleBookmarkAdvisor(id)}
                          className="text-xs text-rose-700 font-bold hover:underline"
                        >
                          ลบออก
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="px-6 py-4 border-t border-stone-200 bg-stone-50 flex justify-end">
              <button
                onClick={() => setShowSavedModal(false)}
                className="px-5 py-2 rounded-xl bg-stone-800 hover:bg-stone-900 text-white text-xs font-bold"
              >
                ปิด
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI COLD EMAIL GENERATOR MODAL */}
      {selectedAdvisorForEmail && (
        <div className="fixed inset-0 z-50 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-stone-300 rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-stone-200 flex items-center justify-between bg-stone-50">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#5B0F18] text-white flex items-center justify-center">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-stone-900">AI Cold Email Assistant</h2>
                  <p className="text-[11px] text-stone-500">
                    ร่างอีเมลติดต่อ {selectedAdvisorForEmail.full_name_th} ({selectedAdvisorForEmail.university_th})
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedAdvisorForEmail(null);
                  setGeneratedEmail(null);
                }}
                className="p-1.5 rounded-lg bg-white hover:bg-stone-100 text-stone-500 hover:text-stone-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Form & Output */}
            <div className="flex-1 overflow-auto p-6 space-y-4">
              {!generatedEmail ? (
                <div className="space-y-3.5 text-xs">
                  <div>
                    <label className="block text-stone-700 font-bold mb-1">ชื่อของคุณ (Student Name)</label>
                    <input
                      type="text"
                      value={studentName}
                      onChange={(e) => setStudentName(e.target.value)}
                      placeholder="เช่น นายสมชาย ใจดี"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-stone-50 border border-stone-300 text-stone-900 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#5B0F18]"
                    />
                  </div>

                  <div>
                    <label className="block text-stone-700 font-bold mb-1">ประวัติการศึกษา / ภูมิหลัง (Background)</label>
                    <input
                      type="text"
                      value={studentBackground}
                      onChange={(e) => setStudentBackground(e.target.value)}
                      placeholder="เช่น จบ ป.ตรี วิศวะคอมพิวเตอร์ หรือ กำลังศึกษา ป.ตรี ปี 4"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-stone-50 border border-stone-300 text-stone-900 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#5B0F18]"
                    />
                  </div>

                  <div>
                    <label className="block text-stone-700 font-bold mb-1">หัวข้อวิจัยที่สนใจ (Research Topic)</label>
                    <textarea
                      rows={3}
                      value={researchTopic}
                      onChange={(e) => setResearchTopic(e.target.value)}
                      placeholder="เช่น สนใจงานวิจัยด้าน NLP ภาษาไทย เพื่อการคัดกรองโรคทางการแพทย์"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-stone-50 border border-stone-300 text-stone-900 placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#5B0F18]"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-stone-700 font-bold mb-1">ระดับการศึกษาที่วางแผน</label>
                      <select
                        value={intendedDegree}
                        onChange={(e) => setIntendedDegree(e.target.value)}
                        className="w-full px-3.5 py-2 rounded-xl bg-stone-50 border border-stone-300 text-stone-900 focus:outline-none focus:ring-1 focus:ring-[#5B0F18]"
                      >
                        <option value="Master's Degree">ปริญญาโท (Master&apos;s)</option>
                        <option value="Doctoral Degree (Ph.D.)">ปริญญาเอก (Ph.D.)</option>
                        <option value="Bachelor's Thesis">โครงงาน ป.ตรี (Senior Project)</option>
                        <option value="Research Internship">ฝึกงานวิจัย (Internship)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-stone-700 font-bold mb-1">ภาษาของอีเมล</label>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setEmailLanguage("th")}
                          className={`flex-1 py-2 rounded-xl font-bold border transition-all ${
                            emailLanguage === "th"
                              ? "bg-[#5B0F18] border-[#5B0F18] text-white"
                              : "bg-stone-100 border-stone-200 text-stone-600"
                          }`}
                        >
                          ภาษาไทย
                        </button>
                        <button
                          type="button"
                          onClick={() => setEmailLanguage("en")}
                          className={`flex-1 py-2 rounded-xl font-bold border transition-all ${
                            emailLanguage === "en"
                              ? "bg-[#5B0F18] border-[#5B0F18] text-white"
                              : "bg-stone-100 border-stone-200 text-stone-600"
                          }`}
                        >
                          English
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                /* Generated Output */
                <div className="space-y-4 text-xs">
                  <div className="p-4 rounded-xl bg-stone-50 border border-stone-200 space-y-3">
                    <div>
                      <span className="text-stone-500 text-[10px] uppercase font-bold block mb-1">หัวข้ออีเมล (Subject):</span>
                      <p className="font-bold text-stone-900 select-all">{generatedEmail.subject}</p>
                    </div>

                    <div className="pt-3 border-t border-stone-200">
                      <span className="text-stone-500 text-[10px] uppercase font-bold block mb-1">เนื้อความ (Body):</span>
                      <pre className="font-sans text-stone-800 whitespace-pre-wrap select-all leading-relaxed bg-white p-3 rounded-lg border border-stone-200">
                        {generatedEmail.body}
                      </pre>
                    </div>
                  </div>

                  {/* Tips */}
                  {generatedEmail.tips && generatedEmail.tips.length > 0 && (
                    <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 space-y-1">
                      <span className="font-bold block">💡 คำแนะนำในการส่งอีเมล:</span>
                      <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                        {generatedEmail.tips.map((tip, idx) => (
                          <li key={idx}>{tip}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-stone-200 bg-stone-50 flex items-center justify-between">
              {!generatedEmail ? (
                <>
                  <span className="text-[11px] text-stone-500">สร้างด้วย Google Gemini API</span>
                  <button
                    onClick={handleGenerateColdEmail}
                    disabled={emailLoading}
                    className="px-5 py-2.5 rounded-xl bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-md disabled:opacity-50"
                  >
                    {emailLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    <span>{emailLoading ? "กำลังสร้างอีเมล..." : "สร้างอีเมลติดต่อ"}</span>
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setGeneratedEmail(null)}
                    className="text-xs text-stone-500 hover:text-stone-900 underline font-medium"
                  >
                    แก้ไขข้อมูลใหม่อีกครั้ง
                  </button>
                  <div className="flex gap-2">
                    <button
                      onClick={copyToClipboard}
                      className="px-4 py-2 rounded-xl bg-stone-800 hover:bg-stone-900 text-white text-xs font-bold flex items-center gap-1.5"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? "คัดลอกแล้ว!" : "คัดลอกข้อความ"}</span>
                    </button>
                    {selectedAdvisorForEmail.email && (
                      <a
                        href={`mailto:${selectedAdvisorForEmail.email}?subject=${encodeURIComponent(generatedEmail.subject)}&body=${encodeURIComponent(generatedEmail.body)}`}
                        className="px-4 py-2 rounded-xl bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold flex items-center gap-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>เปิดในโปรแกรมเมล</span>
                      </a>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-stone-300 bg-[#EFE4D2] px-4 lg:px-8 py-8 text-center text-xs text-stone-600 space-y-2">
        <p>© 2026 Thai EduCenter & Advisor Match. ขับเคลื่อนด้วยระบบค้นหาความหมายเชิงลึก (AI Vector Embeddings) และฐานข้อมูลมหาวิทยาลัยไทย</p>
        <p className="text-[11px] text-stone-500">รวบรวมข้อมูลอย่างถูกต้องตามหลักวิชาการและ PDPA เพื่อสนับสนุนการศึกษาไทย</p>
      </footer>
    </div>
  );
}

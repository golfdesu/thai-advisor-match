"use client";

import React, { useState, useEffect } from "react";
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
  AlertCircle
} from "lucide-react";

interface FacultyMember {
  id: string;
  university: string;
  university_th: string;
  faculty: string;
  faculty_th: string;
  department: string;
  department_th: string;
  academic_title_th?: string;
  first_name?: string;
  last_name?: string;
  full_name_th: string;
  full_name?: string;
  role?: string;
  email?: string;
  image_url?: string;
  profile_url?: string;
  education?: string[];
  research_interests?: string[];
  taught_courses?: string[];
  featured_publications?: {
    title: string;
    year?: number;
    venue?: string;
    citation_count?: number;
  }[];
  scholar_url?: string;
}

interface SearchMatchResult {
  faculty: FacultyMember;
  match_score: number;
  ai_explanation?: string;
  matched_keywords?: string[];
}

interface Course {
  id: string;
  title_th: string;
  title_en?: string;
  degree_level: string;
  degree_name?: string;
  university: string;
  university_th: string;
  faculty: string;
  faculty_th: string;
  department?: string;
  department_th?: string;
  program_type?: string;
  duration_years?: string;
  total_credits?: string;
  tuition_per_semester?: string;
  tuition_total?: string;
  description?: string;
  curriculum_highlights?: string[];
  career_paths?: string[];
  tags?: string[];
  website_url?: string;
  match_score?: number;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

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

  // Cold Email Modal State
  const [selectedAdvisorForEmail, setSelectedAdvisorForEmail] = useState<FacultyMember | null>(null);
  const [studentName, setStudentName] = useState("");
  const [studentBackground, setStudentBackground] = useState("");
  const [researchTopic, setResearchTopic] = useState("");
  const [intendedDegree, setIntendedDegree] = useState("Master's Degree");
  const [emailLanguage, setEmailLanguage] = useState<"th" | "en">("th");
  const [generatedEmail, setGeneratedEmail] = useState<{ subject: string; body: string; tips: string[] } | null>(null);
  const [emailLoading, setEmailLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Fetch initial courses from API on load
  useEffect(() => {
    fetchInitialCourses();
  }, []);

  const fetchInitialCourses = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${BACKEND_URL}/courses/`);
      if (res.ok) {
        const data = await res.json();
        setCourses(data);
      }
    } catch (err) {
      console.warn("Backend not yet running or courses empty, using fallback courses");
    } finally {
      setLoading(false);
    }
  };

  const executeSearch = async (queryText?: string) => {
    const queryToUse = queryText !== undefined ? queryText : searchQuery;
    setLoading(true);
    setErrorMsg(null);
    setSearchExecuted(true);

    try {
      if (activeTab === "courses") {
        const res = await fetch(`${BACKEND_URL}/courses/search`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: queryToUse,
            university: selectedUni === "all" ? null : selectedUni,
            degree_level: selectedDegree === "all" ? null : selectedDegree,
            top_k: 20
          })
        });

        if (!res.ok) throw new Error("ไม่สามารถค้นหาหลักสูตรได้");
        const data = await res.json();
        setCourses(data.results || []);
      } else {
        // Advisors Search
        const res = await fetch(`${BACKEND_URL}/search/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: queryToUse || "Computer Science and AI",
            university: selectedUni === "all" ? null : selectedUni,
            top_k: 12
          })
        });

        if (!res.ok) throw new Error("ไม่สามารถค้นหาอาจารย์ได้ (โปรดตรวจสอบว่า Backend กำลังรันอยู่)");
        const data = await res.json();
        setAdvisors(data.results || []);
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    executeSearch();
  };

  const handleQuickTagClick = (tag: string) => {
    setSearchQuery(tag);
    executeSearch(tag);
  };

  const handleGenerateEmail = async (advisor: FacultyMember) => {
    setSelectedAdvisorForEmail(advisor);
    setResearchTopic(searchQuery || advisor.research_interests?.[0] || "ปัญญาประดิษฐ์และวิทยาการข้อมูล");
    setStudentName("นาย ภัทรพล เจริญวิทย์");
    setStudentBackground("จบการศึกษาระดับปริญญาตรี วิศวกรรมคอมพิวเตอร์ มีประสบการณ์ทำวิจัยด้าน Machine Learning");
    setGeneratedEmail(null);
  };

  const submitEmailGeneration = async () => {
    if (!selectedAdvisorForEmail) return;
    setEmailLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/search/cold-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          faculty_id: selectedAdvisorForEmail.id,
          student_name: studentName,
          student_background: studentBackground,
          research_topic: researchTopic,
          intended_degree: intendedDegree,
          language: emailLanguage
        })
      });

      if (!res.ok) throw new Error("ไม่สามารถสร้างอีเมลได้");
      const data = await res.json();
      setGeneratedEmail(data);
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setEmailLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const quickTags = [
    "AI & Data Science",
    "วิศวกรรมไฟฟ้าและพลังงาน",
    "วิทยาการคอมพิวเตอร์",
    "FinTech & ธุรกิจ",
    "ชีวการแพทย์และเวชศาสตร์",
    "Machine Learning",
    "Microgrids"
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col selection:bg-blue-500 selection:text-white">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-sky-600 text-white text-xs md:text-sm py-2 px-4 text-center font-medium shadow-inner flex items-center justify-center gap-2">
        <Sparkles size={16} className="text-yellow-300 animate-pulse" />
        <span>ระบบเวอร์ชันใหม่: รวมหลักสูตรมหาวิทยาลัยและ AI แมตช์อาจารย์ที่ปรึกษาทั่วไทยแล้ววันนี้!</span>
      </div>

      {/* Navbar */}
      <header className="w-full bg-white/90 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <GraduationCap size={24} />
            </div>
            <div>
              <div className="flex items-center gap-1.5 font-black text-xl tracking-tight text-slate-900">
                <span>Thai</span>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">EduCenter</span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full ml-1">AI Live</span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">Thai Universities Course & Advisor Hub</p>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-600">
            <button
              onClick={() => {
                setActiveTab("courses");
                setSearchExecuted(false);
              }}
              className={`transition-colors flex items-center gap-1.5 ${activeTab === "courses" ? "text-blue-600 font-bold" : "hover:text-blue-600"}`}
            >
              <BookOpen size={16} /> ค้นหาหลักสูตร
            </button>
            <button
              onClick={() => {
                setActiveTab("advisors");
                setSearchExecuted(false);
                if (advisors.length === 0) {
                  setSearchQuery("ปัญญาประดิษฐ์ พลังงานทดแทน วิทยาการข้อมูล");
                }
              }}
              className={`transition-colors flex items-center gap-1.5 ${activeTab === "advisors" ? "text-blue-600 font-bold" : "hover:text-blue-600"}`}
            >
              <Users size={16} /> ค้นหาอาจารย์ที่ปรึกษา
            </button>
            <a
              href="/career-discovery"
              className="text-indigo-600 hover:text-indigo-700 font-bold transition-colors flex items-center gap-1.5 bg-indigo-50 px-3 py-1.5 rounded-xl border border-indigo-100"
            >
              <Sparkles size={15} className="text-indigo-500" />
              <span>ค้นหาตัวตน & คณะที่ใช่ (Quiz)</span>
            </a>
            <a href="https://github.com/golfdesu/thai-advisor-match" target="_blank" className="hover:text-blue-600 transition-colors flex items-center gap-1.5">
              <School size={16} /> สถาบันในระบบ
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <a
              href="/career-discovery"
              className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:opacity-95 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-md hover:shadow-lg transition flex items-center gap-1.5"
            >
              <Sparkles size={14} /> AI ค้นหาตัวตน
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 md:pt-16 md:pb-28 bg-gradient-to-b from-blue-50/70 via-slate-50 to-white">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-tr from-blue-300/20 via-indigo-300/20 to-sky-200/20 blur-3xl -z-10 pointer-events-none rounded-full" />

        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          {/* Tagline Badge */}
          <div className="inline-flex items-center gap-2 bg-blue-100/80 border border-blue-200 text-blue-800 px-4 py-1.5 rounded-full text-xs font-semibold mb-6 shadow-sm">
            <Sparkles size={14} className="text-blue-600" />
            <span>ค้นพบเส้นทางการเรียนรู้และงานวิจัยที่เหมาะสมที่สุดด้วย AI Semantic Matching</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-slate-900 tracking-tight leading-[1.15] mb-6">
            ศูนย์รวม <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-600">หลักสูตรมหาวิทยาลัย</span><br className="hidden sm:inline" />
            และอาจารย์ที่ปรึกษาวิทยานิพนธ์ทั่วไทย
          </h1>

          <p className="text-slate-600 text-base sm:text-lg max-w-3xl mx-auto mb-6 leading-relaxed font-normal">
            ค้นหาหลักสูตรระดับปริญญาตรี โท และเอก หรือใช้ AI แมตช์หัวข้อวิจัยกับอาจารย์ผู้เชี่ยวชาญจากมหาวิทยาลัยชั้นนำทั่วประเทศไทยได้อย่างแม่นยำ
          </p>

          {/* New Interactive Quiz Callout Banner */}
          <div className="max-w-2xl mx-auto mb-8 bg-gradient-to-r from-indigo-900 via-purple-900 to-slate-900 text-white p-4 sm:p-5 rounded-3xl shadow-lg border border-indigo-500/30 flex flex-col sm:flex-row items-center justify-between gap-4 text-left">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center flex-shrink-0">
                <Compass size={24} className="animate-spin" style={{ animationDuration: "12s" }} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm sm:text-base text-white">ยังไม่รู้จะเรียนต่อคณะไหนดี?</span>
                  <span className="text-[10px] font-black bg-pink-500 text-white px-2 py-0.5 rounded-full uppercase tracking-wider">ใหม่</span>
                </div>
                <p className="text-xs text-indigo-200 mt-0.5">ทำแบบประเมิน AI Career Quiz เพื่อค้นพบอาชีพและคณะที่ใช่ตามหลักจิตวิทยา</p>
              </div>
            </div>
            <a
              href="/career-discovery"
              className="bg-white hover:bg-indigo-50 text-indigo-900 text-xs font-black px-4 py-2.5 rounded-xl shadow-md transition flex items-center gap-1.5 flex-shrink-0 w-full sm:w-auto justify-center"
            >
              <span>เริ่มทำแบบประเมิน</span>
              <ArrowRight size={14} />
            </a>
          </div>

          {/* Dual Tab Switcher */}
          <div className="inline-flex p-1.5 bg-slate-200/80 rounded-2xl mb-6 shadow-inner border border-slate-300/60">
            <button
              onClick={() => {
                setActiveTab("courses");
                setErrorMsg(null);
              }}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${
                activeTab === "courses"
                  ? "bg-white text-blue-700 shadow-md scale-[1.02]"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <BookOpen size={18} />
              <span>ค้นหาหลักสูตรการสอน</span>
            </button>
            <button
              onClick={() => {
                setActiveTab("advisors");
                setErrorMsg(null);
              }}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${
                activeTab === "advisors"
                  ? "bg-white text-indigo-700 shadow-md scale-[1.02]"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Users size={18} />
              <span>ค้นหาอาจารย์ที่ปรึกษา (AI Match)</span>
            </button>
          </div>

          {/* Unified Smart Search Form */}
          <form onSubmit={handleSearch} className="max-w-4xl mx-auto bg-white p-3 sm:p-4 rounded-3xl shadow-xl shadow-slate-200/70 border border-slate-200 text-left">
            <div className="flex flex-col md:flex-row gap-3">
              {/* Text Search Input */}
              <div className="flex-[2] relative flex items-center bg-slate-50 rounded-2xl border border-slate-200 px-4 py-3 focus-within:border-blue-500 focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-100 transition">
                <Search className="text-slate-400 mr-3 flex-shrink-0" size={20} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={
                    activeTab === "courses"
                      ? "พิมพ์ชื่อหลักสูตร, คณะ หรือความสนใจ (เช่น AI, Data, การเงิน, ชีวการแพทย์)..."
                      : "พิมพ์หัวข้อวิจัยที่สนใจ (เช่น Microgrids, Machine Learning, Clinical AI)..."
                  }
                  className="w-full bg-transparent focus:outline-none text-slate-800 text-sm placeholder-slate-400 font-medium"
                />
              </div>

              {/* Select University */}
              <div className="flex-1 relative flex items-center bg-slate-50 rounded-2xl border border-slate-200 px-3 py-3 focus-within:border-blue-500 focus-within:bg-white transition">
                <Building2 className="text-slate-400 mr-2 flex-shrink-0" size={18} />
                <select
                  value={selectedUni}
                  onChange={(e) => setSelectedUni(e.target.value)}
                  className="w-full bg-transparent focus:outline-none text-slate-700 text-sm font-medium cursor-pointer"
                >
                  <option value="all">ทุกมหาวิทยาลัย</option>
                  <option value="Chiang Mai University">มหาวิทยาลัยเชียงใหม่ (CMU)</option>
                  <option value="Chulalongkorn University">จุฬาลงกรณ์มหาวิทยาลัย (CU)</option>
                  <option value="Thammasat University">มหาวิทยาลัยธรรมศาสตร์ (TU)</option>
                  <option value="Mahidol University">มหาวิทยาลัยมหิดล (MU)</option>
                  <option value="Kasetsart University">มหาวิทยาลัยเกษตรศาสตร์ (KU)</option>
                  <option value="Khon Kaen University">มหาวิทยาลัยขอนแก่น (KKU)</option>
                  <option value="Prince of Songkla University">มหาวิทยาลัยสงขลานครินทร์ (PSU)</option>
                  <option value="King Mongkut's Institute of Technology Ladkrabang">สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง (KMITL)</option>
                  <option value="King Mongkut's University of Technology Thonburi">มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี (KMUTT)</option>
                  <option value="Srinakharinwirot University">มหาวิทยาลัยศรีนครินทรวิโรฒ (SWU)</option>
                  <option value="Naresuan University">มหาวิทยาลัยนเรศวร (NU)</option>
                  <option value="Burapha University">มหาวิทยาลัยบูรพา (BUU)</option>
                  <option value="Mahasarakham University">มหาวิทยาลัยมหาสารคาม (MSU)</option>
                  <option value="Suranaree University of Technology">มหาวิทยาลัยเทคโนโลยีสุรนารี (SUT)</option>
                  <option value="Mae Fah Luang University">มหาวิทยาลัยแม่ฟ้าหลวง (MFU)</option>
                  <option value="National Institute of Development Administration">สถาบันบัณฑิตพัฒนบริหารศาสตร์ (NIDA)</option>
                  <option value="Silpakorn University">มหาวิทยาลัยศิลปากร (SU)</option>
                </select>
              </div>

              {/* Select Degree (Courses tab) */}
              {activeTab === "courses" && (
                <div className="flex-1 relative flex items-center bg-slate-50 rounded-2xl border border-slate-200 px-3 py-3 focus-within:border-blue-500 focus-within:bg-white transition">
                  <GraduationCap className="text-slate-400 mr-2 flex-shrink-0" size={18} />
                  <select
                    value={selectedDegree}
                    onChange={(e) => setSelectedDegree(e.target.value)}
                    className="w-full bg-transparent focus:outline-none text-slate-700 text-sm font-medium cursor-pointer"
                  >
                    <option value="all">ทุกระดับปริญญา</option>
                    <option value="bachelor">ปริญญาตรี</option>
                    <option value="master">ปริญญาโท</option>
                    <option value="doctorate">ปริญญาเอก</option>
                    <option value="certificate">ประกาศนียบัตร</option>
                  </select>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold px-7 py-3.5 rounded-2xl shadow-md hover:shadow-lg transition flex items-center justify-center gap-2 flex-shrink-0 disabled:opacity-50"
              >
                {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
                <span>{loading ? "กำลังค้นหา..." : "ค้นหา"}</span>
              </button>
            </div>

            {/* Quick Keyword Chips */}
            <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center flex-wrap gap-2 text-xs text-slate-500">
              <span className="font-semibold flex items-center gap-1 text-slate-400">
                <TrendingUp size={13} /> คำค้นยายอดนิยม:
              </span>
              {quickTags.map((tag, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleQuickTagClick(tag)}
                  className="bg-slate-100 hover:bg-blue-50 hover:text-blue-600 text-slate-600 px-2.5 py-1 rounded-lg transition font-medium"
                >
                  #{tag}
                </button>
              ))}
            </div>
          </form>

          {/* Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mt-12 text-slate-600">
            <div className="bg-white/80 backdrop-blur border border-slate-200/80 p-4 rounded-2xl text-center shadow-xs">
              <div className="text-2xl sm:text-3xl font-black text-blue-600">{courses.length > 0 ? `${courses.length}+` : "2,500+"}</div>
              <div className="text-xs font-semibold text-slate-500 mt-1">หลักสูตรในฐานข้อมูล</div>
            </div>
            <div className="bg-white/80 backdrop-blur border border-slate-200/80 p-4 rounded-2xl text-center shadow-xs">
              <div className="text-2xl sm:text-3xl font-black text-indigo-600">850+</div>
              <div className="text-xs font-semibold text-slate-500 mt-1">อาจารย์ & นักวิจัย</div>
            </div>
            <div className="bg-white/80 backdrop-blur border border-slate-200/80 p-4 rounded-2xl text-center shadow-xs">
              <div className="text-2xl sm:text-3xl font-black text-emerald-600">30+</div>
              <div className="text-xs font-semibold text-slate-500 mt-1">มหาวิทยาลัยชั้นนำ</div>
            </div>
            <div className="bg-white/80 backdrop-blur border border-slate-200/80 p-4 rounded-2xl text-center shadow-xs">
              <div className="text-2xl sm:text-3xl font-black text-amber-500 flex items-center justify-center gap-1">
                <Sparkles size={22} /> 98%
              </div>
              <div className="text-xs font-semibold text-slate-500 mt-1">AI Match Accuracy</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full">
        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-8 p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-center gap-3 text-amber-800 text-sm">
            <AlertCircle size={20} className="text-amber-600 flex-shrink-0" />
            <div>
              <p className="font-bold">คำแนะนำ:</p>
              <p>{errorMsg} (หากยังไม่ได้เปิด Backend ให้รัน <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono text-xs">python -m app.main</code> ในโฟลเดอร์ backend)</p>
            </div>
          </div>
        )}

        {/* Section Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-8 gap-4">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-1 flex items-center gap-1.5">
              <Compass size={16} />
              {activeTab === "courses" ? "Curriculum Directory" : "AI Semantic Faculty Directory"}
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-slate-900">
              {activeTab === "courses"
                ? `หลักสูตรมหาวิทยาลัย (${courses.length} รายการ)`
                : `อาจารย์ที่ปรึกษาวิทยานิพนธ์ ${searchExecuted ? `(${advisors.length} รายการที่ตรงกับคุณ)` : ""}`}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">เรียงตาม:</span>
            <span className="bg-white border border-slate-200 text-blue-600 text-xs font-bold px-3 py-1.5 rounded-lg shadow-xs">
              {activeTab === "advisors" ? "ความเหมาะสมสูงสุด (% Match)" : "หลักสูตรยอดนิยม"}
            </span>
          </div>
        </div>

        {/* Tab 1: Courses Cards View */}
        {activeTab === "courses" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {courses.map((course) => (
              <div
                key={course.id}
                className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm hover:shadow-md hover:border-blue-300 transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1 rounded-full border border-blue-100">
                        {course.degree_level}
                      </span>
                      <span className="bg-slate-100 text-slate-600 text-xs font-medium px-2.5 py-1 rounded-full">
                        {course.program_type || "ภาคปกติ"}
                      </span>
                    </div>
                    {course.degree_name && (
                      <span className="text-xs font-bold text-slate-500 bg-slate-50 px-2.5 py-1 rounded-full border border-slate-100">
                        {course.degree_name}
                      </span>
                    )}
                  </div>

                  <h3 className="text-lg sm:text-xl font-bold text-slate-900 group-hover:text-blue-600 transition-colors leading-snug mb-2">
                    {course.title_th}
                  </h3>
                  {course.title_en && (
                    <p className="text-xs text-slate-400 font-medium mb-3">{course.title_en}</p>
                  )}

                  <div className="text-sm font-semibold text-slate-600 flex items-center gap-2 mb-4">
                    <Building2 size={16} className="text-slate-400 flex-shrink-0" />
                    <span>{course.university_th}</span>
                    <span className="text-slate-300">•</span>
                    <span className="text-slate-500 font-normal">{course.faculty_th}</span>
                  </div>

                  {course.description && (
                    <p className="text-xs text-slate-600 line-clamp-2 mb-4 leading-relaxed bg-slate-50/50 p-2.5 rounded-xl border border-slate-100">
                      {course.description}
                    </p>
                  )}

                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-2xl mb-4 border border-slate-100">
                    <div>
                      <span className="text-slate-400 block font-medium">ระยะเวลาศึกษา</span>
                      <span className="font-bold text-slate-700">{course.duration_years || "2-4 ปี"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block font-medium">ค่าธรรมเนียมการศึกษา</span>
                      <span className="font-bold text-slate-700">{course.tuition_per_semester || "ตามประกาศมหาวิทยาลัย"}</span>
                    </div>
                  </div>

                  {course.curriculum_highlights && course.curriculum_highlights.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {course.curriculum_highlights.slice(0, 3).map((hl, i) => (
                        <span key={i} className="text-[11px] font-medium bg-blue-50/60 text-blue-700 px-2 py-0.5 rounded-md border border-blue-100/50">
                          ✓ {hl}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                  <button className="text-xs font-bold text-slate-500 hover:text-slate-900 flex items-center gap-1 transition">
                    <Bookmark size={15} /> บันทึกหลักสูตร
                  </button>
                  {course.website_url ? (
                    <a
                      href={course.website_url}
                      target="_blank"
                      rel="noreferrer"
                      className="bg-slate-900 hover:bg-blue-600 text-white text-xs font-bold px-4 py-2.5 rounded-xl transition flex items-center gap-1.5"
                    >
                      <span>เว็บไซต์หลักสูตร</span>
                      <ExternalLink size={14} />
                    </a>
                  ) : (
                    <button className="bg-slate-900 hover:bg-blue-600 text-white text-xs font-bold px-4 py-2.5 rounded-xl transition flex items-center gap-1.5">
                      <span>ดูรายละเอียด</span>
                      <ChevronRight size={14} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Advisors Cards View */}
        {activeTab === "advisors" && (
          <div>
            {!searchExecuted && advisors.length === 0 && (
              <div className="text-center py-12 bg-white rounded-3xl border border-slate-200 p-8 mb-6">
                <Users size={48} className="text-indigo-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-slate-800 mb-2">ค้นหาอาจารย์ที่ปรึกษาด้วย AI</h3>
                <p className="text-slate-500 text-sm max-w-md mx-auto mb-6">
                  พิมพ์หัวข้อวิจัย หรือคำที่คุณสนใจในกล่องค้นหาด้านบน แล้วกดปุ่ม "ค้นหา" เพื่อให้ AI จับคู่และคำนวณ % Match ให้ทันทีครับ
                </p>
                <button
                  onClick={() => {
                    setSearchQuery("ปัญญาประดิษฐ์และพลังงานทดแทน");
                    handleSearch();
                  }}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-5 py-3 rounded-2xl shadow-sm transition inline-flex items-center gap-2"
                >
                  <Sparkles size={16} /> ลองค้นหาด้วยตัวอย่าง "ปัญญาประดิษฐ์และพลังงานทดแทน"
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {advisors.map((res) => {
                const advisor = res.faculty;
                return (
                  <div
                    key={advisor.id}
                    className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all flex flex-col justify-between group relative"
                  >
                    {/* Match Score Badge */}
                    <div className="absolute top-4 right-4 bg-gradient-to-r from-indigo-600 to-blue-600 text-white font-black text-xs px-2.5 py-1 rounded-full shadow-sm flex items-center gap-1">
                      <Sparkles size={12} />
                      <span>{res.match_score}% Match</span>
                    </div>

                    <div>
                      <div className="flex items-start gap-3 mb-4 pr-16">
                        <img
                          src={advisor.image_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(advisor.full_name_th)}&background=0D8ABC&color=fff&size=128`}
                          alt={advisor.full_name_th}
                          loading="lazy"
                          decoding="async"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(advisor.full_name_th)}&background=0D8ABC&color=fff&size=128`;
                          }}
                          className="w-14 h-14 rounded-2xl object-cover border-2 border-slate-100 shadow-xs flex-shrink-0"
                        />
                        <div>
                          <a 
                            href={`/advisor/${advisor.id}`} 
                            className="inline-flex items-center gap-1 hover:opacity-80 transition-opacity group-hover:text-indigo-600"
                          >
                            <h3 className="text-base font-bold text-slate-900 transition-colors leading-snug">
                              {advisor.full_name_th}
                            </h3>
                          </a>
                          {advisor.full_name && (
                            <p className="text-[11px] text-slate-400 truncate">{advisor.full_name}</p>
                          )}
                          <p className="text-xs text-indigo-600 font-semibold mt-0.5">{advisor.role || advisor.department_th}</p>
                        </div>
                      </div>

                      <div className="text-xs text-slate-500 mb-3">
                        <p>{advisor.faculty_th} • {advisor.university_th}</p>
                      </div>

                      {/* AI Match Explanation */}
                      {res.ai_explanation && (
                        <div className="bg-indigo-50/70 p-3 rounded-2xl border border-indigo-100/70 mb-4 text-xs text-indigo-950">
                          <span className="font-bold flex items-center gap-1 text-indigo-700 mb-1">
                            <Sparkles size={12} /> ทำไมถึงเหมาะกับคุณ:
                          </span>
                          <p className="leading-relaxed">{res.ai_explanation}</p>
                        </div>
                      )}

                      {/* Research Interests */}
                      {advisor.research_interests && advisor.research_interests.length > 0 && (
                        <div className="mb-4">
                          <div className="text-[11px] font-bold text-slate-600 mb-1.5">สาขาวิจัยเด่น:</div>
                          <div className="flex flex-wrap gap-1">
                            {advisor.research_interests.map((interest, i) => (
                              <span key={i} className="text-[10px] bg-slate-100 text-slate-700 font-medium px-2 py-0.5 rounded-md">
                                {interest}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                      <a
                        href={`/advisor/${advisor.id}`}
                        className="text-indigo-600 hover:text-indigo-800 text-xs font-bold flex items-center gap-1 transition"
                      >
                        ดูโปรไฟล์เต็ม <ChevronRight size={14} />
                      </a>
                      <button
                        onClick={() => handleGenerateEmail(advisor)}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-3.5 py-2 rounded-xl transition flex items-center gap-1"
                      >
                        <Mail size={13} /> ติดต่ออาจารย์
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* Cold Email Generator Modal */}
      {selectedAdvisorForEmail && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
                  <Mail size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-lg">AI Cold Email Generator</h3>
                  <p className="text-xs text-slate-400">ร่างอีเมลติดต่อ {selectedAdvisorForEmail.full_name_th}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedAdvisorForEmail(null)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>

            {!generatedEmail ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">ชื่อ-นามสกุลของคุณ:</label>
                  <input
                    type="text"
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-blue-500 font-medium"
                    placeholder="เช่น นาย สมชาย ใจดี"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">ประวัติการศึกษา / ประสบการณ์ย่อ:</label>
                  <textarea
                    rows={2}
                    value={studentBackground}
                    onChange={(e) => setStudentBackground(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-blue-500 font-medium"
                    placeholder="เช่น จบ ป.ตรี วิศวกรรม มีประสบการณ์ทำโปรเจกต์ด้าน..."
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">หัวข้อวิจัยที่อยากทำ:</label>
                  <input
                    type="text"
                    value={researchTopic}
                    onChange={(e) => setResearchTopic(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-blue-500 font-medium"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">ระดับที่ต้องการศึกษา:</label>
                    <select
                      value={intendedDegree}
                      onChange={(e) => setIntendedDegree(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-medium"
                    >
                      <option value="ปริญญาโท (Master's Degree)">ปริญญาโท (Master's Degree)</option>
                      <option value="ปริญญาเอก (Ph.D.)">ปริญญาเอก (Ph.D.)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">ภาษาของอีเมล:</label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setEmailLanguage("th")}
                        className={`flex-1 py-2 rounded-xl text-xs font-bold border ${emailLanguage === "th" ? "bg-indigo-50 text-indigo-700 border-indigo-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}
                      >
                        ภาษาไทย (TH)
                      </button>
                      <button
                        type="button"
                        onClick={() => setEmailLanguage("en")}
                        className={`flex-1 py-2 rounded-xl text-xs font-bold border ${emailLanguage === "en" ? "bg-indigo-50 text-indigo-700 border-indigo-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}
                      >
                        English (EN)
                      </button>
                    </div>
                  </div>
                </div>

                <button
                  onClick={submitEmailGeneration}
                  disabled={emailLoading}
                  className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold py-3 rounded-xl shadow-md transition flex items-center justify-center gap-2 mt-4 disabled:opacity-50"
                >
                  {emailLoading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
                  <span>{emailLoading ? "AI กำลังร่างอีเมล..." : "สร้างอีเมลติดต่ออาจารย์ทันที"}</span>
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3">
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase">หัวข้ออีเมล (Subject):</span>
                    <p className="font-bold text-slate-800 text-sm mt-0.5">{generatedEmail.subject}</p>
                  </div>
                  <div className="border-t border-slate-200 pt-3">
                    <span className="text-xs font-bold text-slate-400 uppercase">เนื้อหา (Body):</span>
                    <pre className="whitespace-pre-wrap font-sans text-xs text-slate-700 mt-1 leading-relaxed bg-white p-3 rounded-xl border border-slate-100 max-h-60 overflow-y-auto">
                      {generatedEmail.body}
                    </pre>
                  </div>
                </div>

                {generatedEmail.tips && generatedEmail.tips.length > 0 && (
                  <div className="bg-blue-50 p-3 rounded-xl border border-blue-100 text-xs text-blue-800">
                    <span className="font-bold">💡 ข้อแนะนำก่อนส่ง:</span>
                    <ul className="list-disc list-inside mt-1 space-y-0.5 text-blue-700">
                      {generatedEmail.tips.map((tip, i) => (
                        <li key={i}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={() => setGeneratedEmail(null)}
                    className="flex-1 border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold py-2.5 rounded-xl text-xs transition"
                  >
                    แก้ไขข้อมูล
                  </button>
                  <button
                    onClick={() => copyToClipboard(`Subject: ${generatedEmail.subject}\n\n${generatedEmail.body}`)}
                    className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-xl text-xs shadow-md transition flex items-center justify-center gap-1.5"
                  >
                    {copied ? <Check size={16} /> : <Copy size={16} />}
                    <span>{copied ? "คัดลอกเรียบร้อยแล้ว!" : "คัดลอกอีเมล (Copy)"}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-10 px-4 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2 font-bold text-slate-800 text-sm">
            <GraduationCap className="text-blue-600" size={20} />
            <span>Thai EduCenter Platform</span>
          </div>
          <p>© 2026 Thai EduCenter & Thai Advisor Match. Open Source Academic Project.</p>
          <div className="flex gap-4">
            <a href="#" className="hover:text-blue-600">นโยบายความเป็นส่วนตัว</a>
            <a href="#" className="hover:text-blue-600">ข้อกำหนดการใช้งาน</a>
            <a href="#" className="hover:text-blue-600">ติดต่อเรา</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

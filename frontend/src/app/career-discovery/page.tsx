"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Compass,
  GraduationCap,
  Briefcase,
  Layers,
  Award,
  Zap,
  Brain,
  Target,
  RefreshCw,
  Share2,
  Copy,
  Check,
  ChevronRight,
  ExternalLink,
  BookOpen,
  Building2,
  Home as HomeIcon,
  Heart,
  TrendingUp,
  AlertCircle,
  Clock,
  Cpu,
  ShieldCheck,
  MapPin,
  Coffee
} from "lucide-react";
import riasecQuestions from "@/data/riasec_questions.json";
import lifestyleQuestions from "@/data/lifestyle_questions.json";
import { RiasecScore, CareerItem, Course as RecommendedCourse, CareerProfileResponse as QuizResultData } from "@/types";
import { API_BASE_URL } from "@/lib/config";

function RiasecRadarChart({ scores }: { scores: RiasecScore }) {
  const size = 320;
  const center = size / 2;
  const radius = 105;

  const traits = [
    { key: "realistic", label: "นักปฏิบัติ (R)", code: "R", color: "#ea580c" },
    { key: "investigative", label: "นักสืบค้น (I)", code: "I", color: "#2563eb" },
    { key: "artistic", label: "นักสร้างสรรค์ (A)", code: "A", color: "#db2777" },
    { key: "social", label: "นักสังคม (S)", code: "S", color: "#059669" },
    { key: "enterprising", label: "นักบริหาร (E)", code: "E", color: "#7c3aed" },
    { key: "conventional", label: "นักจัดระเบียบ (C)", code: "C", color: "#0891b2" }
  ];

  const totalAxes = traits.length;
  const angleStep = (Math.PI * 2) / totalAxes;

  // Calculate polygon points
  const points = traits.map((trait, index) => {
    const angle = index * angleStep - Math.PI / 2;
    const value = (scores as any)[trait.key] || 40;
    const r = (value / 100) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return `${x},${y}`;
  }).join(" ");

  const webRings = [0.25, 0.5, 0.75, 1.0];

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-[var(--theme-card)] rounded-3xl text-[var(--theme-text-body)] shadow-sm border border-[var(--theme-border)] relative overflow-hidden">
      <div className="w-full flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-xs font-bold text-[var(--theme-text-title)]">
          <ShieldCheck size={16} className="text-[var(--theme-primary)]" />
          <span>Holland RIASEC Profile</span>
        </div>
        <span className="text-[11px] font-mono text-[var(--theme-text-muted)] bg-[var(--theme-card-subtle)] px-2.5 py-0.5 rounded-full border border-[var(--theme-border)]">
          Standardized Metric
        </span>
      </div>

      <svg width={size} height={size} className="overflow-visible my-2">
        {/* Background Grid Rings (Light Gray) */}
        {webRings.map((scale, i) => {
          const ringPoints = traits.map((_, index) => {
            const angle = index * angleStep - Math.PI / 2;
            const r = scale * radius;
            const x = center + r * Math.cos(angle);
            const y = center + r * Math.sin(angle);
            return `${x},${y}`;
          }).join(" ");
          return (
            <polygon
              key={i}
              points={ringPoints}
              fill="none"
              stroke="currentColor"
              className="text-[var(--theme-border)]"
              strokeWidth="1"
              strokeDasharray={scale === 1 ? "none" : "3,3"}
            />
          );
        })}

        {/* Radial Axis Lines */}
        {traits.map((_, index) => {
          const angle = index * angleStep - Math.PI / 2;
          const x = center + radius * Math.cos(angle);
          const y = center + radius * Math.sin(angle);
          return <line key={index} x1={center} y1={center} x2={x} y2={y} stroke="currentColor" className="text-[var(--theme-border)]" strokeWidth="1" />;
        })}

        {/* Value Polygon with Light Gradient Fill */}
        <polygon
          points={points}
          fill="var(--theme-primary)"
          fillOpacity="0.25"
          stroke="var(--theme-primary)"
          strokeWidth="2.5"
          className="transition-all duration-700 ease-out"
        />

        {/* Data Nodes & Labels */}
        {traits.map((trait, index) => {
          const angle = index * angleStep - Math.PI / 2;
          const value = (scores as any)[trait.key] || 40;
          const nodeR = (value / 100) * radius;
          const nodeX = center + nodeR * Math.cos(angle);
          const nodeY = center + nodeR * Math.sin(angle);

          const labelR = radius + 22;
          const labelX = center + labelR * Math.cos(angle);
          const labelY = center + labelR * Math.sin(angle);

          return (
            <g key={index}>
              <circle cx={nodeX} cy={nodeY} r="4.5" fill={trait.color} stroke="#ffffff" strokeWidth="2" />
              <text
                x={labelX}
                y={labelY + 4}
                textAnchor="middle"
                fontSize="10.5"
                fontWeight="700"
                fill={trait.color}
                className="select-none font-sans"
              >
                {trait.code}: {Math.round(value)}%
              </text>
            </g>
          );
        })}
      </svg>

      {/* Trait Legend Badges */}
      <div className="grid grid-cols-3 gap-2 w-full mt-2 pt-3 border-t border-[var(--theme-border)] text-[11px]">
        {traits.map((t, idx) => (
          <div key={idx} className="flex items-center gap-1.5 bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] px-2.5 py-1 rounded-lg">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: t.color }}></span>
            <span className="text-[var(--theme-text-body)] font-medium truncate">{t.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function CareerDiscoveryPage() {
  const [tier, setTier] = useState<"quick" | "standard" | "deep" | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<any, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);
  const [result, setResult] = useState<QuizResultData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Cycling status messages for engaging UI feedback while AI computes
  const loadingStages = [
    { text: "กำลังประมวลผล DNA ความถนัดทางการศึกษา...", sub: "ระบบกำลังสังเคราะห์โมเดล RIASEC 6 มิติ" },
    { text: "กำลังวิเคราะห์จิตวิทยาและอาชีพที่เหมาะสม...", sub: "AI กำลังสร้าง Archetype และเส้นทางอาชีพอนาคต" },
    { text: "กำลังค้นหาและจับคู่หลักสูตรมหาวิทยาลัย...", sub: "แมปปิ้งเวกเตอร์ 768 มิติกับหลักสูตรปริญญาตรีทั่วประเทศ" }
  ];

  // Stable deterministic pseudo-random generator seeded by Tier & ID to prevent hydration/re-render resets
  const activeQuestions = useMemo(() => {
    if (!tier) return [];

    let totalRiasec = 18;
    let totalLifestyle = 6;
    if (tier === "quick") { totalRiasec = 12; totalLifestyle = 0; }
    else if (tier === "standard") { totalRiasec = 18; totalLifestyle = 6; }
    else if (tier === "deep") { totalRiasec = 36; totalLifestyle = 14; }

    const grouped: Record<string, typeof riasecQuestions> = { R: [], I: [], A: [], S: [], E: [], C: [] };
    riasecQuestions.forEach(q => {
      if (grouped[q.dimension]) {
        grouped[q.dimension].push({ ...q });
      }
    });

    const selectedRiasec: any[] = [];
    const dimensions = ["R", "I", "A", "S", "E", "C"];
    let i = 0;
    while (selectedRiasec.length < totalRiasec) {
      const dim = dimensions[i % 6];
      if (grouped[dim] && grouped[dim].length > 0) {
        const q = grouped[dim].shift()!;
        selectedRiasec.push({
          id: q.id,
          category: `ความสนใจและกิจกรรม (${q.dimension})`,
          type: "likert" as const,
          question: q.text,
          dimension: q.dimension
        });
      }
      i++;
    }

    const validLifestyleQuestions = (lifestyleQuestions as any[]).filter(
      (q) => q.type !== "free_text" && Array.isArray(q.options) && q.options.length > 0
    );
    const selectedLifestyle = validLifestyleQuestions.slice(0, totalLifestyle).map(q => ({
      ...q,
      question: q.text,
      category: `ไลฟ์สไตล์ & บริบทมหาวิทยาลัย (${q.category})`
    }));

    return [...selectedRiasec, ...selectedLifestyle];
  }, [tier]);

  const currentQ = activeQuestions[currentStep];
  const progressPct = activeQuestions.length > 0 ? Math.round(((currentStep + 1) / activeQuestions.length) * 100) : 0;

  const handleSelectOption = (questionId: any, value: any, isMulti: boolean = false) => {
    if (isMulti) {
      const currentList: string[] = answers[questionId] || [];
      if (currentList.includes(value)) {
        setAnswers({ ...answers, [questionId]: currentList.filter((item) => item !== value) });
      } else {
        setAnswers({ ...answers, [questionId]: [...currentList, value] });
      }
    } else {
      setAnswers({ ...answers, [questionId]: value });
    }
  };

  const handleNext = () => {
    if (currentStep < activeQuestions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setLoadingStage(0);
    setError(null);

    // Dynamic progress stage ticker
    const interval = setInterval(() => {
      setLoadingStage((prev) => (prev < 2 ? prev + 1 : prev));
    }, 1400);

    const formattedAnswers: any[] = [];
    const freeTextAnswers: Record<string, string> = {};

    activeQuestions.forEach((q) => {
      if (q.type === "free_text") {
        freeTextAnswers[q.id.toString()] = answers[q.id] || "";
      } else {
        const val = answers[q.id] ?? (q.type === "likert" ? 3 : (q.options?.[0]?.value || ""));
        let optionLabel: string | undefined = undefined;
        if (q.options && Array.isArray(q.options)) {
          const matchedOpt = q.options.find((opt: any) => opt.value === val);
          if (matchedOpt) optionLabel = matchedOpt.text;
        }

        formattedAnswers.push({
          question_id: q.id,
          dimension: q.dimension,
          category: q.category,
          value: val,
          label: optionLabel
        });
      }
    });

    try {
      const res = await fetch(`${API_BASE_URL}/career-quiz/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tier: tier || "standard",
          answers: formattedAnswers,
          free_text_answers: freeTextAnswers
        })
      });

      if (!res.ok) {
        throw new Error("ไม่สามารถวิเคราะห์ผลลัพธ์ได้ กรุณาลองใหม่อีกครั้ง");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์");
    } finally {
      clearInterval(interval);
      setIsSubmitting(false);
    }
  };

  const copyShareResult = () => {
    if (!result) return;
    const text = `ผลวิเคราะห์ความถนัดทางการศึกษาและอาชีพ โดย AI Thai EduCenter:\n- บุคลิกภาพเด่น: ${result.archetype_title} (Holland Code: ${result.archetype_code})\n- คำนิยาม: "${result.share_quote}"\n\nเข้าทำแบบประเมินและค้นหาหลักสูตรมหาวิทยาลัยได้ที่: ${window.location.href}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const resetQuiz = () => {
    setTier(null);
    setCurrentStep(0);
    setAnswers({});
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[var(--theme-bg)] text-[var(--theme-text-body)] flex flex-col selection:bg-[var(--theme-primary)] selection:text-[var(--theme-primary-contrast)] font-sans antialiased">
      {/* Top Navbar */}
      <header className="border-b border-[var(--theme-border)] bg-[var(--theme-card)]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 text-[var(--theme-text-title)] hover:text-[var(--theme-primary)] transition">
            <div className="w-9 h-9 rounded-xl bg-[var(--theme-primary)] flex items-center justify-center text-[var(--theme-primary-contrast)] shadow-md">
              <GraduationCap size={19} />
            </div>
            <div>
              <span className="font-black text-lg tracking-tight text-[var(--theme-primary)]">Thai EduCenter</span>
              <span className="hidden sm:inline-block text-[10px] font-bold uppercase tracking-wider bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] px-2 py-0.5 rounded-full ml-2 border border-[var(--theme-accent-border)]">
                Career Profiler
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-xs font-semibold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] transition flex items-center gap-1.5 bg-[var(--theme-card-subtle)] px-3.5 py-1.5 rounded-xl border border-[var(--theme-border)] shadow-xs"
            >
              <HomeIcon size={14} />
              <span>กลับหน้าหลัก</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 py-8 sm:py-12 flex flex-col justify-center">
        {/* VIEW 1: Tier Selection Mode */}
        {!tier && !result && (
          <div className="text-center animate-fadeIn">
            <div className="inline-flex items-center gap-2 bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-muted)] px-3.5 py-1 rounded-full text-xs font-semibold mb-6 shadow-2xs">
              <Compass size={14} className="text-[var(--theme-primary)]" />
              <span>Holland RIASEC Psychometric Assessment</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-black text-[var(--theme-text-title)] tracking-tight leading-tight mb-4">
              ค้นหา <span className="text-[var(--theme-primary)]">ศักยภาพ & สาขาวิชาที่ใช่</span><br />
              ด้วยระบบประเมินจิตวิทยาการศึกษา
            </h1>

            <p className="text-[var(--theme-text-muted)] text-sm sm:text-base max-w-xl mx-auto mb-10 leading-relaxed font-normal">
              แบบประเมินความถนัดทางการศึกษาและวิชาชีพ ออกแบบตามกรอบจิตวิทยามาตรฐานสากล พร้อมจับคู่กับหลักสูตรระดับปริญญาตรีของมหาวิทยาลัยชั้นนำทั่วประเทศ
            </p>

            {/* 3 Tier Selection Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-left mb-8">
              {/* Quick Tier */}
              <button
                onClick={() => {
                  setTier("quick");
                  setCurrentStep(0);
                }}
                className="group bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] p-6 rounded-3xl border border-[var(--theme-border)] hover:border-[var(--theme-primary)] transition-all shadow-sm hover:shadow-md flex flex-col justify-between cursor-pointer"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-[var(--theme-card-subtle)] text-[var(--theme-text-title)] flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-[var(--theme-border)]">
                    <Zap size={22} className="text-[var(--theme-primary)]" />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--theme-primary)]">ระดับเร่งด่วน</span>
                    <span className="text-[10px] bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] px-2 py-0.5 rounded-full flex items-center gap-1 border border-[var(--theme-border)]">
                      <Clock size={10} /> 1-2 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-[var(--theme-text-title)] mb-2">Quick Scan</h3>
                  <p className="text-xs text-[var(--theme-text-muted)] leading-relaxed mb-4">
                    12 ข้อ (RIASEC 6 มิติ) ประเมินแนวโน้มความถนัดอย่างรวดเร็ว
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-[var(--theme-primary)] group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>

              {/* Standard Tier (Recommended) */}
              <button
                onClick={() => {
                  setTier("standard");
                  setCurrentStep(0);
                }}
                className="group bg-[var(--theme-card)] p-6 rounded-3xl border-2 border-[var(--theme-primary)] hover:border-[var(--theme-primary-hover)] transition-all shadow-md hover:shadow-lg flex flex-col justify-between relative overflow-hidden scale-[1.02] cursor-pointer"
              >
                <div className="absolute top-3 right-3 bg-[var(--theme-accent)] text-[var(--theme-accent-contrast)] font-bold text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded-full shadow-xs">
                  แนะนำ
                </div>
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)] flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-[var(--theme-primary-border)]">
                    <Target size={22} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--theme-primary)]">ระดับมาตรฐาน</span>
                    <span className="text-[10px] bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] px-2 py-0.5 rounded-full flex items-center gap-1 font-semibold border border-[var(--theme-accent-border)]">
                      <Clock size={10} /> 3-4 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-[var(--theme-text-title)] mb-2">Standard Match</h3>
                  <p className="text-xs text-[var(--theme-text-muted)] leading-relaxed mb-4">
                    24 ข้อ (RIASEC 18 ข้อ + Lifestyle 6 ข้อ) วิเคราะห์ความถนัดคู่กับสไตล์การใช้ชีวิตในรั้วมหาวิทยาลัย
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-[var(--theme-primary)] group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>

              {/* Deep Dive Tier */}
              <button
                onClick={() => {
                  setTier("deep");
                  setCurrentStep(0);
                }}
                className="group bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] p-6 rounded-3xl border border-[var(--theme-border)] hover:border-[var(--theme-accent)] transition-all shadow-sm hover:shadow-md flex flex-col justify-between cursor-pointer"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-[var(--theme-accent-border)]">
                    <Brain size={22} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--theme-accent)]">ระดับเจาะลึก</span>
                    <span className="text-[10px] bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] px-2 py-0.5 rounded-full flex items-center gap-1 border border-[var(--theme-border)]">
                      <Clock size={10} /> 7-10 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-[var(--theme-text-title)] mb-2">Deep Dive DNA</h3>
                  <p className="text-xs text-[var(--theme-text-muted)] leading-relaxed mb-4">
                    50 ข้อ (RIASEC 36 ข้อ + Lifestyle 14 ข้อ) วิเคราะห์เจาะลึกครอบคลุมทุกมิติชีวิตและการศึกษา
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-[var(--theme-accent)] group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>
            </div>

            <div className="text-xs text-[var(--theme-text-muted)] flex items-center justify-center gap-4">
              <span className="flex items-center gap-1"><ShieldCheck size={14} className="text-[var(--theme-primary)]" /> ผลการประเมินเพื่อการแนะแนวการศึกษา</span>
              <span>•</span>
              <span className="flex items-center gap-1"><Cpu size={14} className="text-[var(--theme-accent)]" /> วิเคราะห์ผ่าน AI Semantic Mapping</span>
            </div>
          </div>
        )}

        {/* VIEW 2: Submitting / Loading Screen */}
        {isSubmitting && (
          <div className="text-center py-20 animate-fadeIn max-w-lg mx-auto">
            <div className="relative w-16 h-16 mx-auto mb-6">
              <div className="w-16 h-16 rounded-2xl bg-[var(--theme-primary-subtle)] border border-[var(--theme-border)] flex items-center justify-center text-[var(--theme-primary)] shadow-md animate-pulse">
                <Sparkles size={28} />
              </div>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-[var(--theme-text-title)] mb-2 transition-all duration-300">
              {loadingStages[loadingStage]?.text || "กำลังประมวลผล DNA ความถนัดทางการศึกษา..."}
            </h2>
            <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] max-w-md mx-auto transition-all duration-300">
              {loadingStages[loadingStage]?.sub || "ระบบกำลังสังเคราะห์โมเดล RIASEC ร่วมกับหลักสูตรมหาวิทยาลัยและเส้นทางอาชีพอนาคต"}
            </p>
            <div className="flex items-center justify-center gap-1.5 mt-6">
              {loadingStages.map((_, idx) => (
                <div
                  key={idx}
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    idx === loadingStage
                      ? "w-8 bg-[var(--theme-primary)]"
                      : idx < loadingStage
                      ? "w-3 bg-[var(--theme-primary)] opacity-40"
                      : "w-3 bg-[var(--theme-border)]"
                  }`}
                />
              ))}
            </div>
          </div>
        )}

        {/* VIEW 3: Step-by-Step Question Interface */}
        {tier && !result && !isSubmitting && currentQ && (
          <div className="max-w-2xl mx-auto w-full animate-fadeIn">
            {/* Progress Bar & Header */}
            <div className="mb-6">
              <div className="flex justify-between items-center text-xs font-semibold text-[var(--theme-text-muted)] mb-2">
                <span className="flex items-center gap-1.5 text-[var(--theme-primary)] font-bold">
                  <Compass size={14} />
                  <span>{currentQ.category}</span>
                </span>
                <span className="font-mono text-[var(--theme-text-muted)]">
                  ข้อ {currentStep + 1} / {activeQuestions.length} ({progressPct}%)
                </span>
              </div>
              <div className="w-full bg-[var(--theme-card-subtle)] h-2 rounded-full overflow-hidden border border-[var(--theme-border)]">
                <div
                  className="bg-[var(--theme-primary)] h-full rounded-full transition-all duration-300"
                  style={{ width: `${progressPct}%` }}
                ></div>
              </div>
            </div>

            {/* Question Card */}
            <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl p-6 sm:p-8 shadow-sm backdrop-blur-md mb-6">
              <span className="inline-block bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] text-[11px] font-mono font-bold px-3 py-1 rounded-full mb-3 border border-[var(--theme-border)]">
                Item {currentStep + 1}
              </span>

              <h2 className="text-xl sm:text-2xl font-bold text-[var(--theme-text-title)] leading-snug mb-2">
                {currentQ.question}
              </h2>

              {/* INPUT TYPE 2: Likert 5-point Psychometric Scale */}
              {currentQ.type === "likert" && (
                <div className="mt-8">
                  <div className="grid grid-cols-5 gap-2 sm:gap-3">
                    {[
                      { val: 1, label: "ไม่ชอบเลย", num: "1" },
                      { val: 2, label: "ไม่ชอบ", num: "2" },
                      { val: 3, label: "เฉยๆ", num: "3" },
                      { val: 4, label: "ชอบ", num: "4" },
                      { val: 5, label: "ชอบมาก", num: "5" }
                    ].map((item) => {
                      const isSelected = answers[currentQ.id] === item.val;
                      return (
                        <button
                          key={item.val}
                          type="button"
                          onClick={() => handleSelectOption(currentQ.id, item.val, false)}
                          className={`p-3 sm:p-4 rounded-2xl border text-center transition-all flex flex-col items-center justify-between cursor-pointer ${
                            isSelected
                              ? "bg-[var(--theme-primary)] border-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-md scale-105"
                              : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:border-[var(--theme-border)] hover:bg-[var(--theme-card)]"
                          }`}
                        >
                          <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm mb-2 border ${
                            isSelected ? "bg-white text-[var(--theme-primary)] border-white" : "bg-[var(--theme-card)] text-[var(--theme-text-body)] border-[var(--theme-border)]"
                          }`}>
                            {item.num}
                          </span>
                          <span className={`text-[10px] sm:text-xs font-semibold leading-tight line-clamp-2 ${
                            isSelected ? "text-[var(--theme-primary-contrast)]" : "text-[var(--theme-text-body)]"
                          }`}>
                            {item.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-[11px] text-[var(--theme-text-muted)] mt-4 px-1 font-medium">
                    <span>ระดับ 1 : ไม่ชอบเลย</span>
                    <span>ระดับ 5 : ชอบมาก</span>
                  </div>
                </div>
              )}

              {/* INPUT TYPE 3: Single Choice */}
              {currentQ.type === "single_choice" && currentQ.options && (
                <div className="mt-8 flex flex-col gap-3">
                  {currentQ.options.map((opt: any) => {
                    const isSelected = answers[currentQ.id] === opt.value;
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => handleSelectOption(currentQ.id, opt.value, false)}
                        className={`p-4 rounded-2xl border text-left transition-all flex items-center justify-between cursor-pointer ${
                          isSelected
                            ? "bg-[var(--theme-primary)] border-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-md scale-[1.01]"
                            : "bg-[var(--theme-card)] border-[var(--theme-border)] text-[var(--theme-text-body)] hover:border-[var(--theme-border)] hover:bg-[var(--theme-card-subtle)]"
                        }`}
                      >
                        <span className="font-semibold text-sm sm:text-base">{opt.text}</span>
                        {isSelected && <CheckCircle2 size={20} className="text-[var(--theme-primary-contrast)]" />}
                      </button>
                    );
                  })}
                </div>
              )}

              {/* INPUT TYPE 4: Free Text */}
              {currentQ.type === "free_text" && (
                <div className="mt-8">
                  <textarea
                    rows={4}
                    value={answers[currentQ.id] || ""}
                    onChange={(e) => {
                      setAnswers(prev => ({ ...prev, [currentQ.id]: e.target.value }));
                    }}
                    placeholder="พิมพ์ความฝันของคุณที่นี่ได้เลย..."
                    className="w-full p-4 rounded-2xl border border-[var(--theme-border)] focus:border-[var(--theme-primary)] focus:ring-4 focus:ring-[var(--theme-primary-subtle)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] transition-all resize-none font-medium bg-[var(--theme-card)]"
                  />
                  <div className="mt-3 flex justify-end">
                     <button
                        type="button"
                        onClick={() => handleSelectOption(currentQ.id, answers[currentQ.id], false)}
                        className="bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)] hover:bg-[var(--theme-primary)] hover:text-[var(--theme-primary-contrast)] font-bold px-4 py-2 rounded-xl text-sm transition border border-[var(--theme-border)] cursor-pointer"
                     >
                       บันทึกคำตอบ
                     </button>
                  </div>
                </div>
              )}

            </div>

            {/* Bottom Actions */}
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={handlePrev}
                disabled={currentStep === 0}
                className="text-xs font-bold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] disabled:opacity-30 transition flex items-center gap-1.5 px-4 py-2.5 rounded-xl cursor-pointer"
              >
                <ArrowLeft size={16} /> ย้อนกลับ
              </button>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={resetQuiz}
                  className="text-xs font-semibold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] cursor-pointer"
                >
                  เริ่มใหม่
                </button>

                <button
                  type="button"
                  onClick={handleNext}
                  className="bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-sm font-bold px-6 py-3 rounded-2xl shadow-sm hover:shadow transition flex items-center gap-2 cursor-pointer"
                >
                  <span>{currentStep === activeQuestions.length - 1 ? "ดูผลการวิเคราะห์" : "ถัดไป"}</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 4: Full Comprehensive Results Report */}
        {result && (
          <div className="space-y-8 animate-fadeIn max-w-4xl mx-auto w-full">
            {/* Top Shareable Archetype Card */}
            <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl p-6 sm:p-10 shadow-sm relative overflow-hidden">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                <div className="inline-flex items-center gap-2 bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] px-3 py-1 rounded-full text-xs font-bold font-mono border border-[var(--theme-accent-border)]">
                  <Award size={14} className="text-[var(--theme-accent)]" />
                  <span>Holland Code: {result.archetype_code}</span>
                </div>

                <button
                  onClick={copyShareResult}
                  className="bg-[var(--theme-card-subtle)] hover:bg-[var(--theme-card)] text-[var(--theme-text-body)] text-xs font-bold px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 border border-[var(--theme-border)] shadow-xs cursor-pointer"
                >
                  {copied ? <Check size={14} className="text-emerald-600 dark:text-emerald-400" /> : <Copy size={14} />}
                  <span>{copied ? "คัดลอกข้อมูลแล้ว" : "คัดลอกผลการประเมิน"}</span>
                </button>
              </div>

              <h1 className="text-2xl sm:text-4xl font-black text-[var(--theme-text-title)] tracking-tight mb-2">
                {result.archetype_title}
              </h1>
              <p className="text-[var(--theme-text-muted)] text-sm sm:text-base font-medium mb-6 leading-relaxed">
                {result.archetype_description}
              </p>

              {/* Share Quote Banner */}
              <div className="bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] p-4 rounded-2xl text-xs sm:text-sm text-[var(--theme-text-body)] flex items-center gap-3 shadow-xs">
                <Compass size={18} className="text-[var(--theme-primary)] flex-shrink-0" />
                <span className="font-medium italic">&ldquo;{result.share_quote}&rdquo;</span>
              </div>
            </div>

            {/* Split Grid: Radar Chart + Personality Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Radar Chart */}
              <RiasecRadarChart scores={result.riasec_scores} />

              {/* Personality Summary & Strengths */}
              <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl p-6 sm:p-8 flex flex-col justify-between shadow-sm">
                <div>
                  <h3 className="text-base font-bold text-[var(--theme-text-title)] mb-3 flex items-center gap-2">
                    <Brain size={18} className="text-[var(--theme-primary)]" />
                    <span>บทวิเคราะห์คุณลักษณะและศักยภาพ</span>
                  </h3>
                  <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] leading-relaxed mb-6 font-normal">
                    {result.personality_summary}
                  </p>

                  <div className="text-xs font-bold text-[var(--theme-text-title)] mb-2">ทักษะและจุดเด่นหลัก:</div>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {result.strengths.map((str, idx) => (
                      <span
                        key={idx}
                        className="bg-[var(--theme-primary-subtle)] border border-[var(--theme-border)] text-[var(--theme-primary)] text-xs px-3 py-1 rounded-xl font-semibold"
                      >
                        ✓ {str}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="bg-[var(--theme-card-subtle)] p-3.5 rounded-2xl border border-[var(--theme-border)] text-xs text-[var(--theme-text-body)]">
                  <span className="font-bold text-[var(--theme-primary)] block mb-0.5">สภาพแวดล้อมการทำงานที่เหมาะสม:</span>
                  <span>{result.ideal_work_environment}</span>
                </div>
              </div>
            </div>

            {/* Lifestyle & Campus Life Alignment Card */}
            {(result.campus_vibe_match || result.learning_style_match) && (
              <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl p-6 sm:p-8 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-xl bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center shadow-xs">
                    <Compass size={18} />
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-[var(--theme-text-title)]">
                      สไตล์ชีวิตมหาวิทยาลัยที่ใช่คุณ (Campus & Lifestyle Match)
                    </h3>
                    <p className="text-xs text-[var(--theme-text-muted)]">
                      วิเคราะห์จากความต้องการด้านทำเล บรรยากาศแคมปัส และสไตล์การเรียนรู้ที่คุณเลือก
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                  {result.campus_vibe_match && (
                    <div className="bg-[var(--theme-card-subtle)] p-4 rounded-2xl border border-[var(--theme-border)] shadow-2xs">
                      <div className="flex items-center gap-2 text-[var(--theme-primary)] font-bold text-xs mb-1.5">
                        <MapPin size={15} className="text-[var(--theme-primary)]" />
                        <span>บรรยากาศ & ภูมิภาคมหาวิทยาลัยในฝัน</span>
                      </div>
                      <p className="text-xs sm:text-sm text-[var(--theme-text-body)] leading-relaxed">
                        {result.campus_vibe_match}
                      </p>
                    </div>
                  )}

                  {result.learning_style_match && (
                    <div className="bg-[var(--theme-card-subtle)] p-4 rounded-2xl border border-[var(--theme-border)] shadow-2xs">
                      <div className="flex items-center gap-2 text-[var(--theme-accent)] font-bold text-xs mb-1.5">
                        <Coffee size={15} className="text-[var(--theme-accent)]" />
                        <span>รูปแบบการเรียนรู้ที่ทำให้คุณเปล่งประกาย</span>
                      </div>
                      <p className="text-xs sm:text-sm text-[var(--theme-text-body)] leading-relaxed">
                        {result.learning_style_match}
                      </p>
                    </div>
                  )}
                </div>

                {result.lifestyle_highlights && result.lifestyle_highlights.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-[var(--theme-border)] flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-bold text-[var(--theme-text-title)]">ค่านิยมไลฟ์สไตล์:</span>
                    {result.lifestyle_highlights.map((hl, hIdx) => (
                      <span
                        key={hIdx}
                        className="bg-[var(--theme-card-subtle)] text-[var(--theme-text-body)] text-[11px] font-semibold px-2.5 py-0.5 rounded-lg border border-[var(--theme-border)]"
                      >
                        ✨ {hl}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Top Recommended Careers */}
            <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl p-6 sm:p-8 shadow-sm">
              <h3 className="text-lg font-bold text-[var(--theme-text-title)] mb-1 flex items-center gap-2">
                <Briefcase size={20} className="text-[var(--theme-primary)]" />
                <span>สาขาวิชาชีพที่สอดคล้อง (Career Alignment)</span>
              </h3>
              <p className="text-xs text-[var(--theme-text-muted)] mb-6">
                ประมวลผลจากความสอดคล้องระหว่างคะแนนทักษะและแนวโน้มความต้องการในตลาดงาน
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {result.top_careers.map((career, idx) => (
                  <div
                    key={idx}
                    className="bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] p-5 rounded-2xl flex flex-col justify-between hover:border-[var(--theme-primary)] transition-colors"
                  >
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-[10px] font-bold bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] px-2 py-0.5 rounded-md border border-[var(--theme-accent-border)]">
                          {career.growth_outlook}
                        </span>
                        <span className="text-xs font-mono font-bold text-[var(--theme-primary)]">{career.match_percentage}% Match</span>
                      </div>
                      <h4 className="font-bold text-[var(--theme-text-title)] text-sm mb-2">{career.title}</h4>
                      <p className="text-xs text-[var(--theme-text-muted)] line-clamp-3 leading-relaxed mb-4">
                        {career.description}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-1 pt-3 border-t border-[var(--theme-border)]">
                      {career.skills.map((skill, sIdx) => (
                        <span key={sIdx} className="text-[10px] bg-[var(--theme-card)] text-[var(--theme-text-body)] px-2 py-0.5 rounded-md border border-[var(--theme-border)] font-medium">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Undergraduate Programs (Direct Database Match) */}
            <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl p-6 sm:p-8 shadow-sm">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-6">
                <div>
                  <h3 className="text-lg font-bold text-[var(--theme-text-title)] flex items-center gap-2">
                    <BookOpen size={20} className="text-[var(--theme-primary)]" />
                    <span>หลักสูตรระดับปริญญาตรีที่แนะนำ</span>
                  </h3>
                  <p className="text-xs text-[var(--theme-text-muted)]">
                    ดึงข้อมูลตรงจากหลักสูตรมหาวิทยาลัยในระบบที่สอดคล้องกับเส้นทางอาชีพข้างต้น
                  </p>
                </div>
                <Link
                  href="/"
                  className="text-xs font-bold text-[var(--theme-primary)] hover:underline flex items-center gap-1"
                >
                  <span>สำรวจหลักสูตรทั้งหมด</span> <ChevronRight size={14} />
                </Link>
              </div>

              {result.recommended_courses && result.recommended_courses.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {result.recommended_courses.map((course) => (
                    <div
                      key={course.id}
                      className="bg-[var(--theme-card)] border border-[var(--theme-border)] hover:border-[var(--theme-primary)] p-5 rounded-2xl flex flex-col justify-between transition-all group shadow-xs hover:shadow-sm"
                    >
                      <div>
                        <div className="flex justify-between items-start gap-2 mb-2">
                          <span className="text-[10px] font-bold bg-[var(--theme-card-subtle)] text-[var(--theme-text-title)] px-2.5 py-0.5 rounded-full border border-[var(--theme-border)]">
                            {course.degree_level || "ปริญญาตรี"}
                          </span>
                          {course.match_score && (
                            <span className="text-xs font-mono font-bold text-[var(--theme-primary)] flex items-center gap-1">
                              ตรงสาย {course.match_score}%
                            </span>
                          )}
                        </div>

                        <h4 className="font-bold text-[var(--theme-text-title)] text-sm sm:text-base group-hover:text-[var(--theme-primary)] transition-colors leading-snug mb-1">
                          {course.title_th}
                        </h4>
                        {course.title_en && (
                          <p className="text-[11px] text-[var(--theme-text-muted)] mb-2 truncate">{course.title_en}</p>
                        )}

                        <div className="text-xs text-[var(--theme-text-body)] flex items-center gap-1.5 mb-3 font-medium">
                          <Building2 size={14} className="text-[var(--theme-text-muted)] flex-shrink-0" />
                          <span>{course.university_th}</span>
                          <span className="text-[var(--theme-text-muted)]">•</span>
                          <span className="text-[var(--theme-text-muted)] font-normal">{course.faculty_th}</span>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-[var(--theme-border)] flex items-center justify-between">
                        <span className="text-[11px] text-[var(--theme-text-muted)]">
                          {course.tuition_per_semester || "ตามประกาศมหาวิทยาลัย"}
                        </span>
                        {course.website_url ? (
                          <a
                            href={course.website_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-bold text-[var(--theme-primary-contrast)] bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] px-3 py-1.5 rounded-xl transition flex items-center gap-1 shadow-xs"
                          >
                            <span>ดูหลักสูตร</span> <ExternalLink size={12} />
                          </a>
                        ) : (
                          <Link
                            href="/"
                            className="text-xs font-bold text-[var(--theme-primary-contrast)] bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] px-3 py-1.5 rounded-xl transition flex items-center gap-1 shadow-xs"
                          >
                            <span>ดูในระบบ</span> <ChevronRight size={12} />
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-xs text-[var(--theme-text-muted)] bg-[var(--theme-card-subtle)] rounded-2xl border border-[var(--theme-border)]">
                  กำลังอัปเดตข้อมูลหลักสูตรที่สอดคล้อง
                </div>
              )}
            </div>

            {/* Growth & Preparation Advice Card */}
            <div className="bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] rounded-3xl p-6 sm:p-8 shadow-xs">
              <h3 className="text-base font-bold text-[var(--theme-primary)] mb-2 flex items-center gap-2">
                <TrendingUp size={18} className="text-[var(--theme-primary)]" />
                <span>คำแนะนำเพื่อการเตรียมความพร้อมทางวิชาการ</span>
              </h3>
              <p className="text-xs sm:text-sm text-[var(--theme-text-body)] leading-relaxed font-medium">
                {result.growth_advice}
              </p>
            </div>

            {/* Bottom Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                onClick={resetQuiz}
                className="bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-body)] text-xs font-bold px-6 py-3.5 rounded-2xl border border-[var(--theme-border)] shadow-xs transition flex items-center gap-2 w-full sm:w-auto justify-center cursor-pointer"
              >
                <RefreshCw size={15} />
                <span>ทำแบบประเมินใหม่อีกครั้ง</span>
              </button>

              <Link
                href="/"
                className="bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold px-8 py-3.5 rounded-2xl shadow-sm hover:shadow transition flex items-center gap-2 w-full sm:w-auto justify-center"
              >
                <BookOpen size={15} />
                <span>สำรวจหลักสูตรมหาวิทยาลัยทั้งหมด</span>
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

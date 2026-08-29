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
    <div className="flex flex-col items-center justify-center p-6 bg-white rounded-3xl text-stone-800 shadow-sm border border-stone-200 relative overflow-hidden">
      <div className="w-full flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-xs font-bold text-stone-800">
          <ShieldCheck size={16} className="text-[#5B0F18]" />
          <span>Holland RIASEC Profile</span>
        </div>
        <span className="text-[11px] font-mono text-stone-600 bg-stone-100 px-2.5 py-0.5 rounded-full border border-stone-200">
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
              stroke="#e7e5e4"
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
          return <line key={index} x1={center} y1={center} x2={x} y2={y} stroke="#e7e5e4" strokeWidth="1" />;
        })}

        {/* Value Polygon with Light Gradient Fill */}
        <polygon
          points={points}
          fill="url(#radarGradientLight)"
          fillOpacity="0.35"
          stroke="#5B0F18"
          strokeWidth="2.5"
          className="transition-all duration-700 ease-out"
        />

        <defs>
          <linearGradient id="radarGradientLight" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#5B0F18" stopOpacity="0.6" />
            <stop offset="50%" stopColor="#8B1E2D" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#be123c" stopOpacity="0.4" />
          </linearGradient>
        </defs>

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
      <div className="grid grid-cols-3 gap-2 w-full mt-2 pt-3 border-t border-stone-200 text-[11px]">
        {traits.map((t, idx) => (
          <div key={idx} className="flex items-center gap-1.5 bg-stone-50 border border-stone-200 px-2.5 py-1 rounded-lg">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: t.color }}></span>
            <span className="text-stone-700 font-medium truncate">{t.label}</span>
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
  const [result, setResult] = useState<QuizResultData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Filter questions based on chosen Tier
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

    const shuffle = <T,>(arr: T[]) => [...arr].sort(() => 0.5 - Math.random());
    Object.keys(grouped).forEach(key => {
      grouped[key] = shuffle(grouped[key]);
    });

    const selectedRiasec: any[] = [];
    const dimensions = ["R", "I", "A", "S", "E", "C"];
    let i = 0;
    while (selectedRiasec.length < totalRiasec) {
      const dim = dimensions[i % 6];
      if (grouped[dim] && grouped[dim].length > 0) {
        const q = grouped[dim].pop()!;
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
    const shuffledLifestyle = shuffle(validLifestyleQuestions);
    const selectedLifestyle = shuffledLifestyle.slice(0, totalLifestyle).map(q => ({
      ...q,
      question: q.text,
      category: `ไลฟ์สไตล์ & บริบทมหาวิทยาลัย (${q.category})`
    }));

    return [...shuffle(selectedRiasec), ...selectedLifestyle];
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
    setError(null);

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
    <div className="min-h-screen bg-[#F8F1E7] text-stone-800 flex flex-col selection:bg-[#5B0F18] selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-stone-300 bg-[#F8F1E7]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 text-stone-900 hover:text-[#5B0F18] transition">
            <div className="w-9 h-9 rounded-xl bg-[#5B0F18] flex items-center justify-center text-white shadow-md">
              <GraduationCap size={19} />
            </div>
            <div>
              <span className="font-black text-lg tracking-tight text-[#5B0F18]">Thai EduCenter</span>
              <span className="hidden sm:inline-block text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-[#5B0F18] px-2 py-0.5 rounded-full ml-2 border border-rose-300">
                Career Profiler
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-xs font-semibold text-stone-700 hover:text-stone-900 transition flex items-center gap-1.5 bg-white px-3.5 py-1.5 rounded-xl border border-stone-300 shadow-xs"
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
            <div className="inline-flex items-center gap-2 bg-rose-50 border border-rose-200 text-[#5B0F18] px-3.5 py-1 rounded-full text-xs font-semibold mb-6 shadow-xs">
              <Compass size={14} className="text-[#5B0F18]" />
              <span>Holland RIASEC Psychometric Assessment</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-black text-stone-900 tracking-tight leading-tight mb-4">
              ค้นหา <span className="text-[#5B0F18]">ศักยภาพ & สาขาวิชาที่ใช่</span><br />
              ด้วยระบบประเมินจิตวิทยาอาชีพ
            </h1>

            <p className="text-stone-600 text-sm sm:text-base max-w-xl mx-auto mb-10 leading-relaxed font-normal">
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
                className="group bg-white hover:bg-stone-50/90 p-6 rounded-3xl border border-stone-200 hover:border-amber-500 transition-all shadow-sm hover:shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-amber-200">
                    <Zap size={22} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-amber-700">ระดับเร่งด่วน</span>
                    <span className="text-[10px] bg-stone-100 text-stone-600 px-2 py-0.5 rounded-full flex items-center gap-1 border border-stone-200">
                      <Clock size={10} /> 1-2 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-stone-900 mb-2">Quick Scan</h3>
                  <p className="text-xs text-stone-600 leading-relaxed mb-4">
                    12 ข้อ (RIASEC 6 มิติ) ประเมินแนวโน้มความถนัดอย่างรวดเร็ว
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-amber-700 group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>

              {/* Standard Tier (Recommended) */}
              <button
                onClick={() => {
                  setTier("standard");
                  setCurrentStep(0);
                }}
                className="group bg-white p-6 rounded-3xl border-2 border-[#5B0F18] hover:border-[#4a0c13] transition-all shadow-md hover:shadow-lg flex flex-col justify-between relative overflow-hidden scale-[1.02]"
              >
                <div className="absolute top-3 right-3 bg-[#5B0F18] text-white font-bold text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded-full shadow-xs">
                  แนะนำ
                </div>
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-rose-50 text-[#5B0F18] flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-rose-200">
                    <Target size={22} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#5B0F18]">ระดับมาตรฐาน</span>
                    <span className="text-[10px] bg-rose-50 text-[#5B0F18] px-2 py-0.5 rounded-full flex items-center gap-1 font-semibold border border-rose-200">
                      <Clock size={10} /> 3-4 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-stone-900 mb-2">Standard Match</h3>
                  <p className="text-xs text-stone-600 leading-relaxed mb-4">
                    24 ข้อ (RIASEC 18 ข้อ + Lifestyle 6 ข้อ) วิเคราะห์ความถนัดคู่กับสไตล์การใช้ชีวิตในรั้วมหาวิทยาลัย
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-[#5B0F18] group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>

              {/* Deep Dive Tier */}
              <button
                onClick={() => {
                  setTier("deep");
                  setCurrentStep(0);
                }}
                className="group bg-white hover:bg-stone-50/90 p-6 rounded-3xl border border-stone-200 hover:border-rose-400 transition-all shadow-sm hover:shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-rose-50 text-rose-800 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-rose-200">
                    <Brain size={22} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-rose-800">ระดับเจาะลึก</span>
                    <span className="text-[10px] bg-stone-100 text-stone-600 px-2 py-0.5 rounded-full flex items-center gap-1 border border-stone-200">
                      <Clock size={10} /> 7-10 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-stone-900 mb-2">Deep Dive DNA</h3>
                  <p className="text-xs text-stone-600 leading-relaxed mb-4">
                    50 ข้อ (RIASEC 36 ข้อ + Lifestyle 14 ข้อ) วิเคราะห์เจาะลึกครอบคลุมทุกมิติชีวิตและการศึกษา
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-rose-800 group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>
            </div>

            <div className="text-xs text-stone-600 flex items-center justify-center gap-4">
              <span className="flex items-center gap-1"><ShieldCheck size={14} className="text-emerald-700" /> ผลการประเมินเพื่อการแนะแนวการศึกษา</span>
              <span>•</span>
              <span className="flex items-center gap-1"><Cpu size={14} className="text-[#5B0F18]" /> วิเคราะห์ผ่าน AI Semantic Mapping</span>
            </div>
          </div>
        )}

        {/* VIEW 2: Submitting / Loading Screen */}
        {isSubmitting && (
          <div className="text-center py-20 animate-fadeIn">
            <div className="relative w-16 h-16 mx-auto mb-6">
              <div className="w-16 h-16 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-[#5B0F18] shadow-md animate-pulse">
                <Sparkles size={28} />
              </div>
            </div>
            <h2 className="text-2xl font-black text-stone-900 mb-2">ระบบกำลังประมวลผลข้อมูลความถนัด...</h2>
            <p className="text-sm text-stone-600 max-w-md mx-auto">
              กำลังคำนวณสัดส่วนคะแนน RIASEC และประมวลผลความสอดคล้องกับหลักสูตรมหาวิทยาลัยในฐานข้อมูล
            </p>
          </div>
        )}

        {/* VIEW 3: Step-by-Step Question Interface */}
        {tier && !result && !isSubmitting && currentQ && (
          <div className="max-w-2xl mx-auto w-full animate-fadeIn">
            {/* Progress Bar & Header */}
            <div className="mb-6">
              <div className="flex justify-between items-center text-xs font-semibold text-stone-600 mb-2">
                <span className="flex items-center gap-1.5 text-[#5B0F18] font-bold">
                  <Compass size={14} />
                  <span>{currentQ.category}</span>
                </span>
                <span className="font-mono text-stone-600">
                  ข้อ {currentStep + 1} / {activeQuestions.length} ({progressPct}%)
                </span>
              </div>
              <div className="w-full bg-stone-200 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-[#5B0F18] h-full rounded-full transition-all duration-300"
                  style={{ width: `${progressPct}%` }}
                ></div>
              </div>
            </div>

            {/* Question Card */}
            <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-8 shadow-sm backdrop-blur-md mb-6">
              <span className="inline-block bg-stone-100 text-stone-700 text-[11px] font-mono font-bold px-3 py-1 rounded-full mb-3 border border-stone-200">
                Item {currentStep + 1}
              </span>

              <h2 className="text-xl sm:text-2xl font-bold text-stone-900 leading-snug mb-2">
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
                          className={`p-3 sm:p-4 rounded-2xl border text-center transition-all flex flex-col items-center justify-between ${
                            isSelected
                              ? "bg-[#5B0F18] border-[#5B0F18] text-white shadow-md scale-105"
                              : "bg-stone-50 border-stone-200 text-stone-700 hover:border-stone-300 hover:bg-stone-100"
                          }`}
                        >
                          <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm mb-2 border ${
                            isSelected ? "bg-white text-[#5B0F18] border-white" : "bg-white text-stone-700 border-stone-200"
                          }`}>
                            {item.num}
                          </span>
                          <span className={`text-[10px] sm:text-xs font-semibold leading-tight line-clamp-2 ${
                            isSelected ? "text-white" : "text-stone-700"
                          }`}>
                            {item.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-[11px] text-stone-600 mt-4 px-1 font-medium">
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
                        className={`p-4 rounded-2xl border text-left transition-all flex items-center justify-between ${
                          isSelected
                            ? "bg-[#5B0F18] border-[#5B0F18] text-white shadow-md scale-[1.01]"
                            : "bg-white border-stone-200 text-stone-700 hover:border-stone-300 hover:bg-stone-50"
                        }`}
                      >
                        <span className="font-semibold text-sm sm:text-base">{opt.text}</span>
                        {isSelected && <CheckCircle2 size={20} className="text-white" />}
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
                    className="w-full p-4 rounded-2xl border border-stone-300 focus:border-[#5B0F18] focus:ring-4 focus:ring-rose-100 text-stone-900 transition-all resize-none font-medium bg-white"
                  />
                  <div className="mt-3 flex justify-end">
                     <button
                        type="button"
                        onClick={() => handleSelectOption(currentQ.id, answers[currentQ.id], false)}
                        className="bg-rose-100 text-[#5B0F18] hover:bg-rose-200 font-bold px-4 py-2 rounded-xl text-sm transition border border-rose-300"
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
                className="text-xs font-bold text-stone-600 hover:text-stone-900 disabled:opacity-30 transition flex items-center gap-1.5 px-4 py-2.5 rounded-xl"
              >
                <ArrowLeft size={16} /> ย้อนกลับ
              </button>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={resetQuiz}
                  className="text-xs font-semibold text-stone-600 hover:text-stone-900"
                >
                  เริ่มใหม่
                </button>

                <button
                  type="button"
                  onClick={handleNext}
                  className="bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-sm font-bold px-6 py-3 rounded-2xl shadow-sm hover:shadow transition flex items-center gap-2"
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
            <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-10 shadow-sm relative overflow-hidden">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                <div className="inline-flex items-center gap-2 bg-rose-50 text-[#5B0F18] px-3 py-1 rounded-full text-xs font-bold font-mono border border-rose-200">
                  <Award size={14} className="text-amber-600" />
                  <span>Holland Code: {result.archetype_code}</span>
                </div>

                <button
                  onClick={copyShareResult}
                  className="bg-stone-50 hover:bg-stone-100 text-stone-700 text-xs font-bold px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 border border-stone-200 shadow-xs"
                >
                  {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                  <span>{copied ? "คัดลอกข้อมูลแล้ว" : "คัดลอกผลการประเมิน"}</span>
                </button>
              </div>

              <h1 className="text-2xl sm:text-4xl font-black text-stone-900 tracking-tight mb-2">
                {result.archetype_title}
              </h1>
              <p className="text-stone-600 text-sm sm:text-base font-medium mb-6 leading-relaxed">
                {result.archetype_description}
              </p>

              {/* Share Quote Banner */}
              <div className="bg-stone-50 border border-stone-200 p-4 rounded-2xl text-xs sm:text-sm text-stone-800 flex items-center gap-3 shadow-xs">
                <Compass size={18} className="text-[#5B0F18] flex-shrink-0" />
                <span className="font-medium italic">"{result.share_quote}"</span>
              </div>
            </div>

            {/* Split Grid: Radar Chart + Personality Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Radar Chart */}
              <RiasecRadarChart scores={result.riasec_scores} />

              {/* Personality Summary & Strengths */}
              <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-8 flex flex-col justify-between shadow-sm">
                <div>
                  <h3 className="text-base font-bold text-stone-900 mb-3 flex items-center gap-2">
                    <Brain size={18} className="text-[#5B0F18]" />
                    <span>บทวิเคราะห์คุณลักษณะและศักยภาพ</span>
                  </h3>
                  <p className="text-xs sm:text-sm text-stone-600 leading-relaxed mb-6 font-normal">
                    {result.personality_summary}
                  </p>

                  <div className="text-xs font-bold text-stone-800 mb-2">ทักษะและจุดเด่นหลัก:</div>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {result.strengths.map((str, idx) => (
                      <span
                        key={idx}
                        className="bg-rose-50 border border-rose-200 text-[#5B0F18] text-xs px-3 py-1 rounded-xl font-semibold"
                      >
                        ✓ {str}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="bg-stone-50 p-3.5 rounded-2xl border border-stone-200 text-xs text-stone-700">
                  <span className="font-bold text-[#5B0F18] block mb-0.5">สภาพแวดล้อมการทำงานที่เหมาะสม:</span>
                  <span>{result.ideal_work_environment}</span>
                </div>
              </div>
            </div>

            {/* NEW: Lifestyle & Campus Life Alignment Card */}
            {(result.campus_vibe_match || result.learning_style_match) && (
              <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-8 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-xl bg-emerald-700 text-white flex items-center justify-center shadow-xs">
                    <Compass size={18} />
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-stone-900">
                      สไตล์ชีวิตมหาวิทยาลัยที่ใช่คุณ (Campus & Lifestyle Match)
                    </h3>
                    <p className="text-xs text-stone-600">
                      วิเคราะห์จากความต้องการด้านทำเล บรรยากาศแคมปัส และสไตล์การเรียนรู้ที่คุณเลือก
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                  {result.campus_vibe_match && (
                    <div className="bg-stone-50 p-4 rounded-2xl border border-stone-200 shadow-2xs">
                      <div className="flex items-center gap-2 text-emerald-800 font-bold text-xs mb-1.5">
                        <MapPin size={15} className="text-emerald-700" />
                        <span>บรรยากาศ & ภูมิภาคมหาวิทยาลัยในฝัน</span>
                      </div>
                      <p className="text-xs sm:text-sm text-stone-700 leading-relaxed">
                        {result.campus_vibe_match}
                      </p>
                    </div>
                  )}

                  {result.learning_style_match && (
                    <div className="bg-stone-50 p-4 rounded-2xl border border-stone-200 shadow-2xs">
                      <div className="flex items-center gap-2 text-teal-800 font-bold text-xs mb-1.5">
                        <Coffee size={15} className="text-teal-700" />
                        <span>รูปแบบการเรียนรู้ที่ทำให้คุณเปล่งประกาย</span>
                      </div>
                      <p className="text-xs sm:text-sm text-stone-700 leading-relaxed">
                        {result.learning_style_match}
                      </p>
                    </div>
                  )}
                </div>

                {result.lifestyle_highlights && result.lifestyle_highlights.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-stone-200 flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-bold text-emerald-950">ค่านิยมไลฟ์สไตล์:</span>
                    {result.lifestyle_highlights.map((hl, hIdx) => (
                      <span
                        key={hIdx}
                        className="bg-emerald-50 text-emerald-900 text-[11px] font-semibold px-2.5 py-0.5 rounded-lg border border-emerald-200"
                      >
                        ✨ {hl}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Top Recommended Careers */}
            <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-8 shadow-sm">
              <h3 className="text-lg font-bold text-stone-900 mb-1 flex items-center gap-2">
                <Briefcase size={20} className="text-[#5B0F18]" />
                <span>สาขาวิชาชีพที่สอดคล้อง (Career Alignment)</span>
              </h3>
              <p className="text-xs text-stone-600 mb-6">
                ประมวลผลจากความสอดคล้องระหว่างคะแนนทักษะและแนวโน้มความต้องการในตลาดงาน
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {result.top_careers.map((career, idx) => (
                  <div
                    key={idx}
                    className="bg-stone-50 border border-stone-200 p-5 rounded-2xl flex flex-col justify-between hover:border-stone-300 transition-colors"
                  >
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-[10px] font-bold bg-rose-100 text-[#5B0F18] px-2 py-0.5 rounded-md border border-rose-200">
                          {career.growth_outlook}
                        </span>
                        <span className="text-xs font-mono font-bold text-emerald-700">{career.match_percentage}% Match</span>
                      </div>
                      <h4 className="font-bold text-stone-900 text-sm mb-2">{career.title}</h4>
                      <p className="text-xs text-stone-600 line-clamp-3 leading-relaxed mb-4">
                        {career.description}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-1 pt-3 border-t border-stone-200">
                      {career.skills.map((skill, sIdx) => (
                        <span key={sIdx} className="text-[10px] bg-white text-stone-700 px-2 py-0.5 rounded-md border border-stone-200 font-medium">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Undergraduate Programs (Direct Database Match) */}
            <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-8 shadow-sm">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-6">
                <div>
                  <h3 className="text-lg font-bold text-stone-900 flex items-center gap-2">
                    <BookOpen size={20} className="text-[#5B0F18]" />
                    <span>หลักสูตรระดับปริญญาตรีที่แนะนำ</span>
                  </h3>
                  <p className="text-xs text-stone-600">
                    ดึงข้อมูลตรงจากหลักสูตรมหาวิทยาลัยในระบบที่สอดคล้องกับเส้นทางอาชีพข้างต้น
                  </p>
                </div>
                <Link
                  href="/"
                  className="text-xs font-bold text-[#5B0F18] hover:underline flex items-center gap-1"
                >
                  <span>สำรวจหลักสูตรทั้งหมด</span> <ChevronRight size={14} />
                </Link>
              </div>

              {result.recommended_courses && result.recommended_courses.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {result.recommended_courses.map((course) => (
                    <div
                      key={course.id}
                      className="bg-white border border-stone-200 hover:border-[#5B0F18] p-5 rounded-2xl flex flex-col justify-between transition-all group shadow-xs hover:shadow-sm"
                    >
                      <div>
                        <div className="flex justify-between items-start gap-2 mb-2">
                          <span className="text-[10px] font-bold bg-rose-50 text-[#5B0F18] px-2.5 py-0.5 rounded-full border border-rose-200">
                            {course.degree_level || "ปริญญาตรี"}
                          </span>
                          {course.match_score && (
                            <span className="text-xs font-mono font-bold text-emerald-700 flex items-center gap-1">
                              <Sparkles size={12} className="text-emerald-600" /> {course.match_score}% Match
                            </span>
                          )}
                        </div>

                        <h4 className="font-bold text-stone-900 text-sm sm:text-base group-hover:text-[#5B0F18] transition-colors leading-snug mb-1">
                          {course.title_th}
                        </h4>
                        {course.title_en && (
                          <p className="text-[11px] text-stone-500 mb-2 truncate">{course.title_en}</p>
                        )}

                        <div className="text-xs text-stone-700 flex items-center gap-1.5 mb-3 font-medium">
                          <Building2 size={14} className="text-stone-400 flex-shrink-0" />
                          <span>{course.university_th}</span>
                          <span className="text-stone-400">•</span>
                          <span className="text-stone-600 font-normal">{course.faculty_th}</span>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-stone-100 flex items-center justify-between">
                        <span className="text-[11px] text-stone-600">
                          {course.tuition_per_semester || "ตามประกาศมหาวิทยาลัย"}
                        </span>
                        {course.website_url ? (
                          <a
                            href={course.website_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-bold text-white bg-[#5B0F18] hover:bg-[#4a0c13] px-3 py-1.5 rounded-xl transition flex items-center gap-1 shadow-xs"
                          >
                            <span>ดูหลักสูตร</span> <ExternalLink size={12} />
                          </a>
                        ) : (
                          <Link
                            href="/"
                            className="text-xs font-bold text-white bg-[#5B0F18] hover:bg-[#4a0c13] px-3 py-1.5 rounded-xl transition flex items-center gap-1 shadow-xs"
                          >
                            <span>ดูในระบบ</span> <ChevronRight size={12} />
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-xs text-stone-600 bg-stone-50 rounded-2xl border border-stone-200">
                  กำลังอัปเดตข้อมูลหลักสูตรที่สอดคล้อง
                </div>
              )}
            </div>

            {/* Growth & Preparation Advice Card */}
            <div className="bg-[#EFE4D2] border border-stone-300 rounded-3xl p-6 sm:p-8 shadow-xs">
              <h3 className="text-base font-bold text-[#5B0F18] mb-2 flex items-center gap-2">
                <TrendingUp size={18} className="text-[#5B0F18]" />
                <span>คำแนะนำเพื่อการเตรียมความพร้อมทางวิชาการ</span>
              </h3>
              <p className="text-xs sm:text-sm text-stone-800 leading-relaxed font-medium">
                {result.growth_advice}
              </p>
            </div>

            {/* Bottom Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                onClick={resetQuiz}
                className="bg-white hover:bg-stone-50 text-stone-800 text-xs font-bold px-6 py-3.5 rounded-2xl border border-stone-300 shadow-xs transition flex items-center gap-2 w-full sm:w-auto justify-center"
              >
                <RefreshCw size={15} />
                <span>ทำแบบประเมินใหม่อีกครั้ง</span>
              </button>

              <Link
                href="/"
                className="bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold px-8 py-3.5 rounded-2xl shadow-sm hover:shadow transition flex items-center gap-2 w-full sm:w-auto justify-center"
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

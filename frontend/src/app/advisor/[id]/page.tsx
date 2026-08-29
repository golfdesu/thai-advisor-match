"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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
  Loader2,
  AlertCircle
} from "lucide-react";
import { FacultyMember } from "@/types";
import { API_BASE_URL, getAdvisorAvatarUrl } from "@/lib/config";

export default function AdvisorProfilePage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [advisor, setAdvisor] = useState<FacultyMember | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchAdvisor = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/faculty/${id}`);
        if (!res.ok) {
          if (res.status === 404) throw new Error("ไม่พบข้อมูลอาจารย์ท่านนี้");
          throw new Error("เกิดข้อผิดพลาดในการดึงข้อมูล");
        }
        const data = await res.json();
        setAdvisor(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAdvisor();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F1E7] flex flex-col items-center justify-center">
        <Loader2 size={48} className="text-[#5B0F18] animate-spin mb-4" />
        <p className="text-stone-600 font-medium">กำลังโหลดข้อมูล...</p>
      </div>
    );
  }

  if (error || !advisor) {
    return (
      <div className="min-h-screen bg-[#F8F1E7] p-8 flex flex-col items-center justify-center text-center">
        <div className="bg-white p-8 rounded-3xl border border-stone-300 shadow-sm max-w-md w-full">
          <AlertCircle size={48} className="text-amber-600 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-stone-900 mb-2">ไม่พบข้อมูล</h2>
          <p className="text-stone-600 mb-6">{error || "อาจารย์ที่ปรึกษาไม่มีอยู่ในระบบ"}</p>
          <button
            onClick={() => router.push("/")}
            className="bg-[#5B0F18] hover:bg-[#4a0c13] text-white font-bold px-6 py-2.5 rounded-xl transition w-full shadow-sm"
          >
            กลับสู่หน้าหลัก
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8F1E7] text-stone-800 pb-20 selection:bg-[#5B0F18] selection:text-white">
      {/* Top Banner */}
      <div className="bg-[#5B0F18] h-48 md:h-64 w-full relative">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 pt-6">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-white bg-black/20 hover:bg-black/30 backdrop-blur-md px-4 py-2 rounded-xl transition text-sm font-bold shadow-sm"
          >
            <ArrowLeft size={16} /> กลับ
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 -mt-24 md:-mt-32 relative z-10">
        <div className="bg-white rounded-3xl shadow-xl shadow-stone-300/40 border border-stone-200 overflow-hidden">

          {/* Header Section */}
          <div className="p-6 md:p-10 flex flex-col md:flex-row gap-6 md:gap-8 items-start border-b border-stone-200">
            <img
              src={advisor.image_url || getAdvisorAvatarUrl(advisor.full_name_th)}
              alt={advisor.full_name_th}
              loading="lazy"
              decoding="async"
              onError={(e) => {
                (e.target as HTMLImageElement).src = getAdvisorAvatarUrl(advisor.full_name_th);
              }}
              className="w-32 h-32 md:w-40 md:h-40 rounded-3xl object-cover border-4 border-white shadow-lg flex-shrink-0 bg-stone-100"
            />
            <div className="flex-1 w-full">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div>
                  <h1 className="text-3xl md:text-4xl font-extrabold text-stone-900 mb-2 leading-tight">
                    {advisor.full_name_th}
                  </h1>
                  {advisor.full_name && (
                    <p className="text-stone-500 font-medium mb-3 text-lg">{advisor.full_name}</p>
                  )}

                  <div className="flex flex-wrap items-center gap-2 mb-4">
                    <span className="bg-rose-50 text-[#5B0F18] text-sm font-bold px-3 py-1 rounded-lg border border-rose-200 flex items-center gap-1.5">
                      <Award size={16} /> {advisor.role || "อาจารย์ประจำ"}
                    </span>
                    <span className="bg-stone-100 text-stone-700 text-sm font-semibold px-3 py-1 rounded-lg flex items-center gap-1.5">
                      <Building2 size={16} className="text-stone-400" />
                      {advisor.department_th}
                    </span>
                  </div>

                  <p className="text-stone-600 font-medium text-sm">
                    {advisor.faculty_th} • {advisor.university_th}
                  </p>
                </div>

                <div className="flex flex-col gap-2 w-full md:w-auto">
                  {advisor.email && (
                    <a
                      href={`mailto:${advisor.email}`}
                      className="bg-[#5B0F18] hover:bg-[#4a0c13] text-white font-bold px-5 py-2.5 rounded-xl transition shadow-md flex items-center justify-center gap-2 whitespace-nowrap"
                    >
                      <Mail size={18} /> ติดต่อผ่านอีเมล
                    </a>
                  )}
                  {advisor.profile_url && (
                    <a
                      href={advisor.profile_url}
                      target="_blank"
                      rel="noreferrer"
                      className="bg-stone-100 hover:bg-stone-200 text-stone-800 font-bold px-5 py-2.5 rounded-xl transition flex items-center justify-center gap-2 whitespace-nowrap border border-stone-200"
                    >
                      <span>เว็บมหาวิทยาลัย</span>
                      <ExternalLink size={16} />
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Content Grid */}
          <div className="p-6 md:p-10 grid grid-cols-1 md:grid-cols-3 gap-8">

            {/* Left Column - Main Info */}
            <div className="md:col-span-2 space-y-8">

              {/* Research Interests */}
              {advisor.research_interests && advisor.research_interests.length > 0 && (
                <section>
                  <h2 className="text-lg font-bold text-stone-900 mb-4 flex items-center gap-2">
                    <BookOpen className="text-[#5B0F18]" size={20} />
                    สาขาวิจัยและความเชี่ยวชาญ (Research Interests)
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {advisor.research_interests.map((interest, i) => (
                      <span key={i} className="bg-stone-100 border border-stone-200 text-stone-800 font-medium px-3.5 py-1.5 rounded-xl text-sm">
                        {interest}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Education */}
              {advisor.education && advisor.education.length > 0 && (
                <section>
                  <h2 className="text-lg font-bold text-stone-900 mb-4 flex items-center gap-2">
                    <GraduationCap className="text-[#5B0F18]" size={20} />
                    ประวัติการศึกษา (Education)
                  </h2>
                  <div className="space-y-3">
                    {advisor.education.map((edu, i) => (
                      <div key={i} className="flex gap-3 bg-stone-50 p-4 rounded-2xl border border-stone-200">
                        <div className="w-8 h-8 rounded-full bg-rose-100 text-[#5B0F18] flex items-center justify-center flex-shrink-0 mt-0.5">
                          <GraduationCap size={16} />
                        </div>
                        <p className="text-sm text-stone-700 font-medium leading-relaxed">{edu}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Publications */}
              {advisor.featured_publications && advisor.featured_publications.length > 0 && (
                <section>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-bold text-stone-900 flex items-center gap-2">
                      <FileText className="text-[#5B0F18]" size={20} />
                      ผลงานวิชาการและงานวิจัยเด่น (Publications)
                    </h2>
                    {advisor.scholar_url && (
                      <a href={advisor.scholar_url} target="_blank" rel="noreferrer" className="text-xs font-bold text-[#5B0F18] hover:underline flex items-center gap-1 bg-stone-100 border border-stone-200 px-3 py-1.5 rounded-lg transition">
                        Google Scholar <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                  <div className="space-y-3">
                    {advisor.featured_publications.map((pub, i) => (
                      <div key={i} className="bg-white p-4 rounded-2xl border border-stone-200 shadow-xs hover:border-[#5B0F18] transition">
                        <h4 className="font-bold text-sm text-stone-900 leading-snug mb-2">{pub.title}</h4>
                        <div className="flex flex-wrap items-center gap-3 text-xs text-stone-500 font-medium">
                          {pub.year && <span className="bg-stone-100 px-2 py-0.5 rounded-md text-stone-700 font-semibold">{pub.year}</span>}
                          {pub.venue && <span>{pub.venue}</span>}
                          {pub.citation_count !== undefined && pub.citation_count > 0 && (
                            <span className="text-stone-700 bg-stone-100 px-2 py-0.5 rounded-md border border-stone-200 font-medium">
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

            {/* Right Column - Sidebar */}
            <div className="space-y-6">

              {/* Taught Courses */}
              {advisor.taught_courses && advisor.taught_courses.length > 0 && (
                <div className="bg-white rounded-3xl border border-stone-200 p-6 shadow-sm">
                  <h3 className="text-base font-bold text-stone-900 mb-4 flex items-center gap-2">
                    <BookOpen className="text-[#5B0F18]" size={20} />
                    รายวิชาที่รับผิดชอบ
                  </h3>
                  <ul className="space-y-2">
                    {advisor.taught_courses.map((course, i) => (
                      <li key={i} className="flex gap-2 text-sm text-stone-700 font-medium">
                        <span className="text-[#5B0F18] font-black">•</span>
                        <span>{course}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Quick Contact Card */}
              <div className="bg-[#EFE4D2] rounded-3xl border border-stone-300 p-6">
                <h3 className="text-sm font-bold text-[#5B0F18] mb-2">สนใจติดต่ออาจารย์ที่ปรึกษา?</h3>
                <p className="text-xs text-stone-700 mb-4 leading-relaxed font-medium">
                  คุณสามารถใช้ระบบช่วยร่างอีเมลแนะนำตัวพร้อมโครงร่างหัวข้อวิจัยที่เหมาะสมเพื่อติดต่ออาจารย์ได้
                </p>
                <button
                  onClick={() => router.push("/")}
                  className="w-full bg-[#5B0F18] hover:bg-[#4a0c13] text-white text-xs font-bold py-2.5 rounded-xl shadow-sm transition flex justify-center items-center gap-1.5 cursor-pointer"
                >
                  <span>กลับสู่หน้าหลักเพื่อร่างอีเมล</span>
                </button>
              </div>

            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

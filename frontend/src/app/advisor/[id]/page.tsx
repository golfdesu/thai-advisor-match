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
      <div className="min-h-screen bg-[var(--theme-bg)] flex flex-col items-center justify-center">
        <Loader2 size={48} className="text-[var(--theme-primary)] animate-spin mb-4" />
        <p className="text-[var(--theme-text-muted)] font-medium">กำลังโหลดข้อมูล...</p>
      </div>
    );
  }

  if (error || !advisor) {
    return (
      <div className="min-h-screen bg-[var(--theme-bg)] p-8 flex flex-col items-center justify-center text-center">
        <div className="bg-[var(--theme-card)] p-8 rounded-3xl border border-[var(--theme-border)] shadow-sm max-w-md w-full">
          <AlertCircle size={48} className="text-[var(--theme-accent)] mx-auto mb-4" />
          <h2 className="text-xl font-bold text-[var(--theme-text-title)] mb-2">ไม่พบข้อมูล</h2>
          <p className="text-[var(--theme-text-muted)] mb-6">{error || "อาจารย์ที่ปรึกษาไม่มีอยู่ในระบบ"}</p>
          <button
            onClick={() => router.push("/")}
            className="bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] font-bold px-6 py-2.5 rounded-xl transition w-full shadow-sm cursor-pointer"
          >
            กลับสู่หน้าหลัก
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--theme-bg)] text-[var(--theme-text-body)] pb-20 selection:bg-[var(--theme-primary)] selection:text-[var(--theme-primary-contrast)] font-sans antialiased">
      {/* Top Banner */}
      <div className="bg-[var(--theme-primary)] h-48 md:h-64 w-full relative border-b border-[var(--theme-border)]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 pt-6">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-white bg-black/20 hover:bg-black/30 backdrop-blur-md px-4 py-2 rounded-xl transition text-sm font-bold shadow-sm cursor-pointer"
          >
            <ArrowLeft size={16} /> กลับ
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 -mt-24 md:-mt-32 relative z-10">
        <div className="bg-[var(--theme-card)] rounded-3xl shadow-sm border border-[var(--theme-border)] overflow-hidden">

          {/* Header Section */}
          <div className="p-6 md:p-10 flex flex-col md:flex-row gap-6 md:gap-8 items-start border-b border-[var(--theme-border)]">
            <img
              src={advisor.image_url || getAdvisorAvatarUrl(advisor.full_name_th)}
              alt={advisor.full_name_th}
              loading="lazy"
              decoding="async"
              onError={(e) => {
                (e.target as HTMLImageElement).src = getAdvisorAvatarUrl(advisor.full_name_th);
              }}
              className="w-32 h-32 md:w-40 md:h-40 rounded-3xl object-cover border-4 border-[var(--theme-card)] shadow-lg flex-shrink-0 bg-[var(--theme-card-subtle)]"
            />
            <div className="flex-1 w-full">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div>
                  <h1 className="text-3xl md:text-4xl font-extrabold text-[var(--theme-text-title)] mb-2 leading-tight">
                    {advisor.full_name_th}
                  </h1>
                  {advisor.full_name && (
                    <p className="text-[var(--theme-text-muted)] font-medium mb-3 text-lg">{advisor.full_name}</p>
                  )}

                  <div className="flex flex-wrap items-center gap-2 mb-4">
                    <span className="bg-[var(--theme-accent-subtle)] text-[var(--theme-accent)] border border-[var(--theme-accent-border)] text-sm font-bold px-3 py-1 rounded-lg flex items-center gap-1.5">
                      <Award size={16} /> {advisor.role || "อาจารย์ประจำ"}
                    </span>
                    <span className="bg-[var(--theme-card-subtle)] text-[var(--theme-text-body)] border border-[var(--theme-border)] text-sm font-semibold px-3 py-1 rounded-lg flex items-center gap-1.5">
                      <Building2 size={16} className="text-[var(--theme-text-muted)]" />
                      {advisor.department_th}
                    </span>
                  </div>

                  <p className="text-[var(--theme-text-muted)] font-medium text-sm">
                    {advisor.faculty_th} • {advisor.university_th}
                  </p>
                </div>

                <div className="flex flex-col gap-2 w-full md:w-auto">
                  {advisor.email && (
                    <a
                      href={`mailto:${advisor.email}`}
                      className="bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] font-bold px-5 py-2.5 rounded-xl transition shadow-md flex items-center justify-center gap-2 whitespace-nowrap cursor-pointer"
                    >
                      <Mail size={18} /> ติดต่อผ่านอีเมล
                    </a>
                  )}
                  {advisor.profile_url && (
                    <a
                      href={advisor.profile_url}
                      target="_blank"
                      rel="noreferrer"
                      className="bg-[var(--theme-card-subtle)] hover:bg-[var(--theme-card)] text-[var(--theme-text-title)] font-bold px-5 py-2.5 rounded-xl transition flex items-center justify-center gap-2 whitespace-nowrap border border-[var(--theme-border)] cursor-pointer"
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
                  <h2 className="text-lg font-bold text-[var(--theme-text-title)] mb-4 flex items-center gap-2">
                    <BookOpen className="text-[var(--theme-primary)]" size={20} />
                    สาขาวิจัยและความเชี่ยวชาญ (Research Interests)
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {advisor.research_interests.map((interest, i) => (
                      <span key={i} className="bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] font-medium px-3.5 py-1.5 rounded-xl text-sm">
                        {interest}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Education */}
              {advisor.education && advisor.education.length > 0 && (
                <section>
                  <h2 className="text-lg font-bold text-[var(--theme-text-title)] mb-4 flex items-center gap-2">
                    <GraduationCap className="text-[var(--theme-primary)]" size={20} />
                    ประวัติการศึกษา (Education)
                  </h2>
                  <div className="space-y-3">
                    {advisor.education.map((edu, i) => (
                      <div key={i} className="flex gap-3 bg-[var(--theme-card-subtle)] p-4 rounded-2xl border border-[var(--theme-border)]">
                        <div className="w-8 h-8 rounded-full bg-[var(--theme-primary-subtle)] text-[var(--theme-primary)] flex items-center justify-center flex-shrink-0 mt-0.5">
                          <GraduationCap size={16} />
                        </div>
                        <p className="text-sm text-[var(--theme-text-body)] font-medium leading-relaxed">{edu}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Publications */}
              {advisor.featured_publications && advisor.featured_publications.length > 0 && (
                <section>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-bold text-[var(--theme-text-title)] flex items-center gap-2">
                      <FileText className="text-[var(--theme-primary)]" size={20} />
                      ผลงานวิชาการและงานวิจัยเด่น (Publications)
                    </h2>
                    {advisor.scholar_url && (
                      <a href={advisor.scholar_url} target="_blank" rel="noreferrer" className="text-xs font-bold text-[var(--theme-primary)] hover:underline flex items-center gap-1 bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] px-3 py-1.5 rounded-lg transition">
                        Google Scholar <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                  <div className="space-y-3">
                    {advisor.featured_publications.map((pub, i) => (
                      <div key={i} className="bg-[var(--theme-card)] p-4 rounded-2xl border border-[var(--theme-border)] shadow-xs hover:border-[var(--theme-primary)] transition">
                        <h4 className="font-bold text-sm text-[var(--theme-text-title)] leading-snug mb-2">{pub.title}</h4>
                        <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--theme-text-muted)] font-medium">
                          {pub.year && <span className="bg-[var(--theme-card-subtle)] px-2 py-0.5 rounded-md text-[var(--theme-text-body)] font-semibold border border-[var(--theme-border)]">{pub.year}</span>}
                          {pub.venue && <span>{pub.venue}</span>}
                          {pub.citation_count !== undefined && pub.citation_count > 0 && (
                            <span className="text-[var(--theme-text-body)] bg-[var(--theme-card-subtle)] px-2 py-0.5 rounded-md border border-[var(--theme-border)] font-medium">
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
                <div className="bg-[var(--theme-card)] rounded-3xl border border-[var(--theme-border)] p-6 shadow-sm">
                  <h3 className="text-base font-bold text-[var(--theme-text-title)] mb-4 flex items-center gap-2">
                    <BookOpen className="text-[var(--theme-primary)]" size={20} />
                    รายวิชาที่รับผิดชอบ
                  </h3>
                  <ul className="space-y-2">
                    {advisor.taught_courses.map((course, i) => (
                      <li key={i} className="flex gap-2 text-sm text-[var(--theme-text-body)] font-medium">
                        <span className="text-[var(--theme-primary)] font-black">•</span>
                        <span>{course}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Quick Contact Card */}
              <div className="bg-[var(--theme-card-subtle)] rounded-3xl border border-[var(--theme-border)] p-6">
                <h3 className="text-sm font-bold text-[var(--theme-primary)] mb-2">สนใจติดต่ออาจารย์ที่ปรึกษา?</h3>
                <p className="text-xs text-[var(--theme-text-body)] mb-4 leading-relaxed font-medium">
                  คุณสามารถใช้ระบบช่วยร่างอีเมลแนะนำตัวพร้อมโครงร่างหัวข้อวิจัยที่เหมาะสมเพื่อติดต่ออาจารย์ได้
                </p>
                <button
                  onClick={() => router.push("/")}
                  className="w-full bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold py-2.5 rounded-xl shadow-sm transition flex justify-center items-center gap-1.5 cursor-pointer"
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

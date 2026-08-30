"use client";

import React, { useState } from "react";
import { FacultyMember } from "@/types";
import { API_BASE_URL } from "@/lib/config";
import { Mail, X, Loader2, Copy, Check, Send } from "lucide-react";

interface ColdEmailModalProps {
  advisor: FacultyMember | null;
  onClose: () => void;
}

export const ColdEmailModal: React.FC<ColdEmailModalProps> = ({ advisor, onClose }) => {
  const [studentName, setStudentName] = useState("");
  const [studentBackground, setStudentBackground] = useState("");
  const [researchTopic, setResearchTopic] = useState("");
  const [intendedDegree, setIntendedDegree] = useState("Master's Degree");
  const [emailLanguage, setEmailLanguage] = useState<"th" | "en">("th");
  const [generatedEmail, setGeneratedEmail] = useState<{
    subject: string;
    body: string;
    tips: string[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!advisor) return null;

  const handleGenerate = async () => {
    setLoading(true);
    setGeneratedEmail(null);

    try {
      const res = await fetch(`${API_BASE_URL}/search/cold-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          faculty_id: advisor.id,
          student_name: studentName.trim() || "นักศึกษาผู้สนใจ",
          student_background:
            studentBackground.trim() || "นักศึกษาที่มีความสนใจศึกษาต่อและทำวิจัย",
          research_topic:
            researchTopic.trim() ||
            advisor.research_interests?.[0] ||
            "หัวข้อวิจัยที่สอดคล้องกับความเชี่ยวชาญ",
          intended_degree: intendedDegree,
          language: emailLanguage,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setGeneratedEmail(data);
      } else {
        alert("ไม่สามารถสร้างร่างอีเมลได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง");
      }
    } catch (e) {
      alert("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!generatedEmail) return;
    const fullText = `หัวข้อ: ${generatedEmail.subject}\n\n${generatedEmail.body}`;
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-[var(--theme-card)] border border-[var(--theme-border)] rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[var(--theme-border)] flex items-center justify-between bg-[var(--theme-card-subtle)]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center shadow-2xs">
              <Mail className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[var(--theme-text-title)]">ผู้ช่วยร่างอีเมลติดต่ออาจารย์</h2>
              <p className="text-[11px] text-[var(--theme-text-muted)]">
                ร่างอีเมลติดต่อ {advisor.full_name_th} ({advisor.university_th})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] border border-[var(--theme-border)] cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Form & Output */}
        <div className="flex-1 overflow-auto p-6 space-y-4">
          {!generatedEmail ? (
            <div className="space-y-3.5 text-xs">
              <div>
                <label className="block font-bold text-[var(--theme-text-title)] mb-1">
                  ชื่อ-นามสกุลของคุณ (Student Name):
                </label>
                <input
                  type="text"
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  placeholder="เช่น นายสมชาย ใจดี หรือ Somchai Jaidee"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div>
                <label className="block font-bold text-[var(--theme-text-title)] mb-1">
                  ระดับการศึกษาที่ต้องการสมัคร (Target Degree):
                </label>
                <select
                  value={intendedDegree}
                  onChange={(e) => setIntendedDegree(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] focus:outline-none focus:ring-1 focus:ring-[var(--theme-primary)] cursor-pointer"
                >
                  <option value="Master's Degree">ปริญญาโท (Master&apos;s Degree)</option>
                  <option value="Ph.D. / Doctoral Degree">ปริญญาเอก (Ph.D. / Doctoral Degree)</option>
                  <option value="Research Intern / Assistant">ผู้ช่วยวิจัย / นักศึกษาฝึกงานวิจัย</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-[var(--theme-text-title)] mb-1">
                  ประวัติการศึกษา / ทักษะสำคัญของคุณ (Background & Skills):
                </label>
                <textarea
                  rows={2}
                  value={studentBackground}
                  onChange={(e) => setStudentBackground(e.target.value)}
                  placeholder="เช่น จบ ป.ตรี วิศวกรรมศาสตร์ GPA 3.65 มีพื้นฐาน Python, Machine Learning และเคยทำโปรเจกต์ IoT..."
                  className="w-full px-3.5 py-2 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div>
                <label className="block font-bold text-[var(--theme-text-title)] mb-1">
                  หัวข้อวิจัยหรือความสนใจที่ต้องการทำ (Proposed Research Topic):
                </label>
                <textarea
                  rows={2}
                  value={researchTopic}
                  onChange={(e) => setResearchTopic(e.target.value)}
                  placeholder={
                    advisor.research_interests?.[0]
                      ? `เช่น สนใจศึกษาต่อยอดด้าน ${advisor.research_interests[0]}...`
                      : "ระบุหัวข้องานวิจัยที่สนใจทำร่วมกับอาจารย์..."
                  }
                  className="w-full px-3.5 py-2 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--theme-primary)]"
                />
              </div>

              <div>
                <label className="block font-bold text-[var(--theme-text-title)] mb-1">ภาษาที่ใช้เขียน (Language):</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEmailLanguage("th")}
                    className={`flex-1 py-2 rounded-xl font-bold border transition-all cursor-pointer ${
                      emailLanguage === "th"
                        ? "bg-[var(--theme-primary)] border-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-2xs"
                        : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)]"
                    }`}
                  >
                    ภาษาไทย
                  </button>
                  <button
                    type="button"
                    onClick={() => setEmailLanguage("en")}
                    className={`flex-1 py-2 rounded-xl font-bold border transition-all cursor-pointer ${
                      emailLanguage === "en"
                        ? "bg-[var(--theme-primary)] border-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-2xs"
                        : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)]"
                    }`}
                  >
                    English
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] space-y-3">
                <div>
                  <span className="text-[var(--theme-text-muted)] text-[10px] uppercase font-bold block mb-1">
                    หัวข้ออีเมล (Subject):
                  </span>
                  <p className="font-bold text-[var(--theme-text-title)] select-all">{generatedEmail.subject}</p>
                </div>

                <div className="pt-3 border-t border-[var(--theme-border)]">
                  <span className="text-[var(--theme-text-muted)] text-[10px] uppercase font-bold block mb-1">
                    เนื้อความ (Body):
                  </span>
                  <pre className="font-sans text-[var(--theme-text-body)] whitespace-pre-wrap select-all leading-relaxed bg-[var(--theme-card)] p-3.5 rounded-xl border border-[var(--theme-border)]">
                    {generatedEmail.body}
                  </pre>
                </div>
              </div>

              {generatedEmail.tips && generatedEmail.tips.length > 0 && (
                <div className="p-3.5 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-body)] space-y-1">
                  <span className="font-bold block text-[var(--theme-text-title)]">คำแนะนำในการติดต่อ:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-[11px] text-[var(--theme-text-muted)]">
                    {generatedEmail.tips.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="px-6 py-4 border-t border-[var(--theme-border)] bg-[var(--theme-card-subtle)] flex items-center justify-between">
          {!generatedEmail ? (
            <>
              <button
                type="button"
                onClick={onClose}
                className="text-xs font-semibold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] cursor-pointer"
              >
                ยกเลิก
              </button>
              <button
                type="button"
                onClick={handleGenerate}
                disabled={loading}
                className="px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                <span>สร้างร่างอีเมล</span>
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setGeneratedEmail(null)}
                className="text-xs font-semibold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] cursor-pointer"
              >
                แก้ไขข้อมูลใหม่
              </button>
              <button
                type="button"
                onClick={copyToClipboard}
                className="px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:bg-[var(--theme-primary-hover)] text-[var(--theme-primary-contrast)] text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? "คัดลอกเรียบร้อย" : "คัดลอกข้อความ"}</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

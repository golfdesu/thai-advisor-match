"use client";

import React, { useState } from "react";
import { ResearchLab, LabInquiryResponse } from "@/types";
import { API_BASE_URL } from "@/lib/config";
import { Building2, X, Loader2, Copy, Check, Send, Sparkles } from "lucide-react";

interface LabInquiryModalProps {
  lab: ResearchLab | null;
  onClose: () => void;
}

export const LabInquiryModal: React.FC<LabInquiryModalProps> = ({ lab, onClose }) => {
  const [studentName, setStudentName] = useState("");
  const [studentBackground, setStudentBackground] = useState("");
  const [researchProposal, setResearchProposal] = useState("");
  const [intendedDegree, setIntendedDegree] = useState("Master's Degree");
  const [inquiryType, setInquiryType] = useState("ra_assistantship");
  const [emailLanguage, setEmailLanguage] = useState<"th" | "en">("th");
  const [generatedLetter, setGeneratedLetter] = useState<LabInquiryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!lab) return null;

  const handleGenerate = async () => {
    setLoading(true);
    setGeneratedLetter(null);

    try {
      const res = await fetch(`${API_BASE_URL}/labs/inquiry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lab_id: lab.id,
          student_name: studentName.trim() || "นักศึกษาผู้สนใจ",
          student_background:
            studentBackground.trim() || "นักศึกษาที่มีความสนใจศึกษาต่อและทำวิจัยในห้องปฏิบัติการ",
          research_proposal:
            researchProposal.trim() ||
            lab.research_domains?.[0] ||
            "หัวข้อวิจัยที่สอดคล้องกับความเชี่ยวชาญของห้องปฏิบัติการ",
          intended_degree: intendedDegree,
          inquiry_type: inquiryType,
          language: emailLanguage,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setGeneratedLetter(data);
      } else {
        alert("ไม่สามารถสร้างร่างข้อความติดต่อแล็บได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง");
      }
    } catch {
      alert("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!generatedLetter) return;
    const fullText = `หัวข้อ: ${generatedLetter.subject}\n\n${generatedLetter.body}`;
    navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="bg-[var(--theme-card)] border-2 border-[var(--theme-border)] rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden shadow-black/30">
        {/* Modal Header */}
        <div className="px-6 sm:px-8 py-5 border-b border-[var(--theme-border)] flex items-center justify-between bg-[var(--theme-card-subtle)]/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] flex items-center justify-center shadow-md">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black text-[var(--theme-text-title)]">
                ผู้ช่วยร่างจดหมายติดต่อสมัครเข้าร่วมแล็บวิจัย (AI)
              </h2>
              <p className="text-xs sm:text-sm text-[var(--theme-text-muted)] font-semibold mt-0.5 line-clamp-1">
                {lab.name_th} ({lab.university_th})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-[var(--theme-card)] hover:bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] border border-[var(--theme-border)] cursor-pointer transition shadow-2xs"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form & Output */}
        <div className="flex-1 overflow-auto p-6 sm:p-8 space-y-5">
          {!generatedLetter ? (
            <div className="space-y-4 text-xs sm:text-sm">
              <div>
                <label className="block font-black text-[var(--theme-text-title)] mb-1.5">
                  ชื่อ-นามสกุลของคุณ (Student Name):
                </label>
                <input
                  type="text"
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  placeholder="เช่น นายสมชาย ใจดี หรือ Somchai Jaidee"
                  className="w-full px-4 py-3 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] text-xs sm:text-sm"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-black text-[var(--theme-text-title)] mb-1.5">
                    ระดับการศึกษาที่มุ่งหมาย (Target Degree):
                  </label>
                  <select
                    value={intendedDegree}
                    onChange={(e) => setIntendedDegree(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] cursor-pointer text-xs sm:text-sm font-semibold"
                  >
                    <option value="Master's Degree">ปริญญาโท (Master&apos;s Degree)</option>
                    <option value="Ph.D. / Doctoral Degree">ปริญญาเอก (Ph.D. / Doctoral Degree)</option>
                    <option value="Research Assistant / Postdoc">ผู้ช่วยวิจัย (RA) / นักวิจัยหลังปริญญาเอก</option>
                  </select>
                </div>

                <div>
                  <label className="block font-black text-[var(--theme-text-title)] mb-1.5">
                    วัตถุประสงค์การติดต่อ (Inquiry Objective):
                  </label>
                  <select
                    value={inquiryType}
                    onChange={(e) => setInquiryType(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] cursor-pointer text-xs sm:text-sm font-semibold"
                  >
                    <option value="ra_assistantship">สมัครรับทุนผู้ช่วยวิจัย (RA Application)</option>
                    <option value="lab_visit">ขอเข้าพบเยี่ยมชมแล็บและปรึกษาวิจัย (Lab Visit)</option>
                    <option value="joint_project">เสนอโครงการร่วมวิจัย (Research Proposal)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-black text-[var(--theme-text-title)] mb-1.5">
                  ประวัติการศึกษา / ผลงาน / ทักษะสำคัญของคุณ (Background & Skills):
                </label>
                <textarea
                  rows={3}
                  value={studentBackground}
                  onChange={(e) => setStudentBackground(e.target.value)}
                  placeholder="เช่น จบ ป.ตรี วิศวกรรมศาสตร์ GPA 3.70 มีความชำนาญด้าน PyTorch, Robot Operating System (ROS) และเคยทำโปรเจกต์..."
                  className="w-full px-4 py-3 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] text-xs sm:text-sm"
                />
              </div>

              <div>
                <label className="block font-black text-[var(--theme-text-title)] mb-1.5">
                  แนวคิดงานวิจัยที่ต้องการทำในห้องปฏิบัติการ (Proposed Research Focus):
                </label>
                <textarea
                  rows={3}
                  value={researchProposal}
                  onChange={(e) => setResearchProposal(e.target.value)}
                  placeholder={
                    lab.research_domains?.[0]
                      ? `เช่น สนใจศึกษาต่อยอดด้าน ${lab.research_domains[0]} และการประยุกต์ใช้ในอุตสาหกรรม...`
                      : "ระบุข้อเสนอหัวข้องานวิจัยที่สนใจทำในห้องปฏิบัติการ..."
                  }
                  className="w-full px-4 py-3 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-title)] placeholder-[var(--theme-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] text-xs sm:text-sm"
                />
              </div>

              <div>
                <label className="block font-black text-[var(--theme-text-title)] mb-1.5">
                  ภาษาที่ใช้เขียน (Language):
                </label>
                <div className="flex gap-2.5">
                  <button
                    type="button"
                    onClick={() => setEmailLanguage("th")}
                    className={`flex-1 py-2.5 rounded-xl font-black border transition-all cursor-pointer text-xs sm:text-sm ${
                      emailLanguage === "th"
                        ? "bg-[var(--theme-primary)] border-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-md"
                        : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)]"
                    }`}
                  >
                    ภาษาไทย
                  </button>
                  <button
                    type="button"
                    onClick={() => setEmailLanguage("en")}
                    className={`flex-1 py-2.5 rounded-xl font-black border transition-all cursor-pointer text-xs sm:text-sm ${
                      emailLanguage === "en"
                        ? "bg-[var(--theme-primary)] border-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-md"
                        : "bg-[var(--theme-card-subtle)] border-[var(--theme-border)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)]"
                    }`}
                  >
                    English
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-5 text-xs sm:text-sm">
              <div className="p-5 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] space-y-4 shadow-sm">
                <div>
                  <span className="text-[var(--theme-text-muted)] text-xs uppercase font-black block mb-1.5">
                    หัวข้ออีเมล (Subject):
                  </span>
                  <p className="font-black text-sm sm:text-base text-[var(--theme-text-title)] select-all leading-snug">
                    {generatedLetter.subject}
                  </p>
                </div>

                <div className="pt-4 border-t border-[var(--theme-border)]">
                  <span className="text-[var(--theme-text-muted)] text-xs uppercase font-black block mb-1.5">
                    เนื้อความ (Body):
                  </span>
                  <pre className="font-sans text-xs sm:text-sm text-[var(--theme-text-body)] whitespace-pre-wrap select-all leading-relaxed bg-[var(--theme-card)] p-5 rounded-2xl border border-[var(--theme-border)] shadow-inner">
                    {generatedLetter.body}
                  </pre>
                </div>
              </div>

              {generatedLetter.tips && generatedLetter.tips.length > 0 && (
                <div className="p-5 rounded-2xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-[var(--theme-text-body)] space-y-2">
                  <span className="font-black block text-xs sm:text-sm text-[var(--theme-text-title)] flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-[var(--theme-accent)]" />
                    <span>คำแนะนำเพื่อเพิ่มโอกาสการตอบรับเข้าแล็บ:</span>
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-xs sm:text-sm text-[var(--theme-text-muted)] font-medium">
                    {generatedLetter.tips.map((tip, idx) => (
                      <li key={idx} className="leading-relaxed">
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="px-6 sm:px-8 py-4 border-t border-[var(--theme-border)] bg-[var(--theme-card-subtle)] flex items-center justify-between gap-3">
          {!generatedLetter ? (
            <>
              <button
                type="button"
                onClick={onClose}
                className="text-xs sm:text-sm font-bold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] cursor-pointer"
              >
                ยกเลิก
              </button>
              <button
                type="button"
                onClick={handleGenerate}
                disabled={loading}
                className="px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:opacity-90 text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-bold transition flex items-center gap-2 disabled:opacity-50 cursor-pointer shadow-sm"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                <span>สร้างร่างจดหมาย AI</span>
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setGeneratedLetter(null)}
                className="text-xs sm:text-sm font-bold text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] cursor-pointer"
              >
                แก้ไขข้อมูลใหม่
              </button>
              <button
                type="button"
                onClick={copyToClipboard}
                className="px-5 py-2.5 rounded-xl bg-[var(--theme-primary)] hover:opacity-90 text-[var(--theme-primary-contrast)] text-xs sm:text-sm font-bold transition flex items-center gap-2 cursor-pointer shadow-sm"
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

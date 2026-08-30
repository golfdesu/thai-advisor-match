"use client";

import React from "react";
import { SlidersHorizontal } from "lucide-react";

interface FilterBarProps {
  activeTab: "courses" | "advisors";
  selectedUni: string;
  selectedDegree: string;
  onSelectUni: (uni: string) => void;
  onSelectDegree: (deg: string) => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  activeTab,
  selectedUni,
  selectedDegree,
  onSelectUni,
  onSelectDegree,
}) => {
  return (
    <div className="p-4 sm:p-5 rounded-2xl bg-[var(--theme-card)] border border-[var(--theme-border)] shadow-xs flex flex-wrap items-center justify-between gap-4">
      <div className="flex flex-wrap items-center gap-3.5 w-full sm:w-auto">
        <div className="flex items-center gap-2 text-xs sm:text-sm font-black text-[var(--theme-text-title)]">
          <SlidersHorizontal className="w-4 h-4 text-[var(--theme-primary)]" />
          <span>คัดกรอง:</span>
        </div>

        {/* University Dropdown */}
        <select
          value={selectedUni}
          onChange={(e) => onSelectUni(e.target.value)}
          className="px-4 py-2 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-xs sm:text-sm text-[var(--theme-text-title)] font-bold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] cursor-pointer"
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

        {/* Degree Level Filter Tabs */}
        {activeTab === "courses" && (
          <div className="flex items-center gap-1 p-1 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)]">
            {[
              { id: "all", label: "ทุกระดับ" },
              { id: "ปริญญาตรี", label: "ปริญญาตรี" },
              { id: "ปริญญาโท", label: "ปริญญาโท" },
              { id: "ปริญญาเอก", label: "ปริญญาเอก" },
            ].map((deg) => (
              <button
                key={deg.id}
                onClick={() => onSelectDegree(deg.id)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  selectedDegree === deg.id
                    ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-2xs font-black"
                    : "text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)]"
                }`}
              >
                {deg.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

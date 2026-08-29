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
    <div className="p-4 rounded-2xl bg-white border border-stone-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
      <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
        <div className="flex items-center gap-2 text-xs font-bold text-stone-700">
          <SlidersHorizontal className="w-4 h-4 text-[#5B0F18]" />
          <span>คัดกรอง:</span>
        </div>

        {/* University Dropdown */}
        <select
          value={selectedUni}
          onChange={(e) => onSelectUni(e.target.value)}
          className="px-3 py-1.5 rounded-xl bg-stone-50 border border-stone-200 text-xs text-stone-800 font-medium focus:outline-none focus:ring-1 focus:ring-[#5B0F18] cursor-pointer"
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
          <div className="flex items-center gap-1 p-0.5 rounded-xl bg-stone-100 border border-stone-200">
            {[
              { id: "all", label: "ทุกระดับ" },
              { id: "ปริญญาตรี", label: "ปริญญาตรี" },
              { id: "ปริญญาโท", label: "ปริญญาโท" },
              { id: "ปริญญาเอก", label: "ปริญญาเอก" },
            ].map((deg) => (
              <button
                key={deg.id}
                onClick={() => onSelectDegree(deg.id)}
                className={`px-3 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                  selectedDegree === deg.id
                    ? "bg-[#5B0F18] text-white shadow-2xs"
                    : "text-stone-600 hover:text-stone-900"
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

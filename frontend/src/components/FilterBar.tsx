"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  SlidersHorizontal,
  MapPin,
  Building2,
  GraduationCap,
  BookOpen,
  RotateCcw,
  ChevronDown,
} from "lucide-react";
import type { RegionInfo, UniversityOption, FacultyOption, DepartmentOption } from "@/types";
import { API_BASE_URL } from "@/lib/config";
import { taxonomyCache } from "@/lib/dsa";

const DEFAULT_REGIONS: RegionInfo[] = [
  { id: "all", label_th: "ทุกภูมิภาค", label_en: "All", icon: "🇹🇭", university_count: 37, advisor_count: 5685, course_count: 4162 },
  { id: "central", label_th: "กทม. และภาคกลาง", label_en: "Central", icon: "🏙️", university_count: 22, advisor_count: 3575, course_count: 2834 },
  { id: "north", label_th: "ภาคเหนือ", label_en: "North", icon: "⛰️", university_count: 6, advisor_count: 807, course_count: 577 },
  { id: "northeast", label_th: "ภาคอีสาน", label_en: "Northeast", icon: "🌾", university_count: 5, advisor_count: 702, course_count: 570 },
  { id: "south", label_th: "ภาคใต้", label_en: "South", icon: "🌊", university_count: 3, advisor_count: 587, course_count: 140 },
  { id: "east", label_th: "ภาคตะวันออก", label_en: "East", icon: "🌅", university_count: 1, advisor_count: 14, course_count: 41 },
];

interface FilterBarProps {
  activeTab: "courses" | "advisors" | "labs";
  selectedRegion: string;
  selectedUni: string;
  selectedFaculty: string;
  selectedDepartment: string;
  selectedDegree: string;
  selectedResearchTier?: string;
  onSelectRegion: (region: string) => void;
  onSelectUni: (uni: string) => void;
  onSelectFaculty: (faculty: string) => void;
  onSelectDepartment: (dept: string) => void;
  onSelectDegree: (deg: string) => void;
  onSelectResearchTier?: (tier: string) => void;
  onResetFilters: () => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  activeTab,
  selectedRegion,
  selectedUni,
  selectedFaculty,
  selectedDepartment,
  selectedDegree,
  selectedResearchTier = "all",
  onSelectRegion,
  onSelectUni,
  onSelectFaculty,
  onSelectDepartment,
  onSelectDegree,
  onSelectResearchTier,
  onResetFilters,
}) => {
  const [regions, setRegions] = useState<RegionInfo[]>(DEFAULT_REGIONS);
  const [universities, setUniversities] = useState<UniversityOption[]>([]);
  const [faculties, setFaculties] = useState<FacultyOption[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [loadingUnis, setLoadingUnis] = useState(false);
  const [loadingFacs, setLoadingFacs] = useState(false);
  const [loadingDepts, setLoadingDepts] = useState(false);

  const uniAbortRef = useRef<AbortController | null>(null);
  const facAbortRef = useRef<AbortController | null>(null);
  const deptAbortRef = useRef<AbortController | null>(null);

  // 1. Fetch Regions metadata on mount
  useEffect(() => {
    const cached = taxonomyCache.get("taxonomy:regions") as RegionInfo[] | undefined;
    if (cached) {
      queueMicrotask(() => setRegions(cached));
      return;
    }

    const controller = new AbortController();
    fetch(`${API_BASE_URL}/taxonomy/regions`, { signal: controller.signal })
      .then((res) => (res.ok ? res.json() : null))
      .then((data: RegionInfo[] | null) => {
        if (data && Array.isArray(data)) {
          taxonomyCache.put("taxonomy:regions", data);
          setRegions(data);
        }
      })
      .catch(() => {
        // Fallback to DEFAULT_REGIONS
      });

    return () => controller.abort();
  }, []);

  // 2. Fetch Universities whenever selectedRegion changes
  useEffect(() => {
    const cacheKey = `taxonomy:unis:${selectedRegion}`;
    const cached = taxonomyCache.get(cacheKey) as UniversityOption[] | undefined;
    if (cached) {
      queueMicrotask(() => setUniversities(cached));
      return;
    }

    uniAbortRef.current?.abort();
    const controller = new AbortController();
    uniAbortRef.current = controller;
    queueMicrotask(() => setLoadingUnis(true));

    const regionParam = selectedRegion && selectedRegion !== "all" ? `?region=${encodeURIComponent(selectedRegion)}` : "";
    fetch(`${API_BASE_URL}/taxonomy/universities${regionParam}`, { signal: controller.signal })
      .then((res) => (res.ok ? res.json() : null))
      .then((data: UniversityOption[] | null) => {
        if (data && Array.isArray(data)) {
          taxonomyCache.put(cacheKey, data);
          setUniversities(data);
        }
      })
      .catch((err) => {
        if (err instanceof Error && err.name === "AbortError") return;
      })
      .finally(() => {
        setLoadingUnis(false);
      });

    return () => controller.abort();
  }, [selectedRegion]);

  // 3. Fetch Faculties whenever selectedUni or selectedRegion changes
  useEffect(() => {
    if (selectedUni === "all" && selectedRegion === "all") {
      queueMicrotask(() => setFaculties([]));
      return;
    }

    const cacheKey = `taxonomy:faculties:${selectedUni}:${selectedRegion}`;
    const cached = taxonomyCache.get(cacheKey) as FacultyOption[] | undefined;
    if (cached) {
      queueMicrotask(() => setFaculties(cached));
      return;
    }

    facAbortRef.current?.abort();
    const controller = new AbortController();
    facAbortRef.current = controller;
    queueMicrotask(() => setLoadingFacs(true));

    const params = new URLSearchParams();
    if (selectedUni && selectedUni !== "all") params.append("university", selectedUni);
    if (selectedRegion && selectedRegion !== "all") params.append("region", selectedRegion);

    fetch(`${API_BASE_URL}/taxonomy/faculties?${params.toString()}`, { signal: controller.signal })
      .then((res) => (res.ok ? res.json() : null))
      .then((data: FacultyOption[] | null) => {
        if (data && Array.isArray(data)) {
          taxonomyCache.put(cacheKey, data);
          setFaculties(data);
        }
      })
      .catch((err) => {
        if (err instanceof Error && err.name === "AbortError") return;
      })
      .finally(() => {
        setLoadingFacs(false);
      });

    return () => controller.abort();
  }, [selectedUni, selectedRegion]);

  // 4. Fetch Departments whenever selectedUni or selectedFaculty changes
  useEffect(() => {
    if (!selectedUni || selectedUni === "all" || !selectedFaculty || selectedFaculty === "all") {
      queueMicrotask(() => setDepartments([]));
      return;
    }

    const cacheKey = `taxonomy:departments:${selectedUni}:${selectedFaculty}`;
    const cached = taxonomyCache.get(cacheKey) as DepartmentOption[] | undefined;
    if (cached) {
      queueMicrotask(() => setDepartments(cached));
      return;
    }

    deptAbortRef.current?.abort();
    const controller = new AbortController();
    deptAbortRef.current = controller;
    queueMicrotask(() => setLoadingDepts(true));

    const params = new URLSearchParams({
      university: selectedUni,
      faculty: selectedFaculty,
    });

    fetch(`${API_BASE_URL}/taxonomy/departments?${params.toString()}`, { signal: controller.signal })
      .then((res) => (res.ok ? res.json() : null))
      .then((data: DepartmentOption[] | null) => {
        if (data && Array.isArray(data)) {
          taxonomyCache.put(cacheKey, data);
          setDepartments(data);
        }
      })
      .catch((err) => {
        if (err instanceof Error && err.name === "AbortError") return;
      })
      .finally(() => {
        setLoadingDepts(false);
      });

    return () => controller.abort();
  }, [selectedUni, selectedFaculty]);

  const hasActiveFilter =
    selectedRegion !== "all" ||
    selectedUni !== "all" ||
    selectedFaculty !== "all" ||
    selectedDepartment !== "all" ||
    selectedDegree !== "all" ||
    (selectedResearchTier !== "all" && activeTab === "advisors");

  return (
    <div className="flex flex-col gap-4">
      {/* Top Bar: Label & Region Pills */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-[var(--theme-border)]">
        <div className="flex items-center gap-2 text-xs sm:text-sm font-black text-[var(--theme-text-title)]">
          <MapPin className="w-4 h-4 text-[var(--theme-primary)]" />
          <span>ภูมิภาคที่ต้องการศึกษา:</span>
        </div>

        {/* Region Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {regions.map((reg) => {
            const isActive = selectedRegion === reg.id;
            return (
              <button
                key={reg.id}
                type="button"
                onClick={() => {
                  onSelectRegion(reg.id);
                  onSelectUni("all");
                  onSelectFaculty("all");
                  onSelectDepartment("all");
                }}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  isActive
                    ? "bg-[var(--theme-primary)] text-[var(--theme-primary-contrast)] shadow-xs font-black"
                    : "bg-[var(--theme-card-subtle)] text-[var(--theme-text-muted)] hover:text-[var(--theme-text-title)] border border-[var(--theme-border)]"
                }`}
              >
                <span>{reg.icon}</span>
                <span>{reg.label_th}</span>
                {reg.university_count > 0 && reg.id !== "all" && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      isActive
                        ? "bg-[var(--theme-primary-contrast)]/20 text-[var(--theme-primary-contrast)]"
                        : "bg-[var(--theme-card)] text-[var(--theme-text-muted)]"
                    }`}
                  >
                    {reg.university_count}
                  </span>
                )}
              </button>
            );
          })}

          {/* Reset Filters button */}
          {hasActiveFilter && (
            <button
              type="button"
              onClick={onResetFilters}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold text-red-500 hover:bg-red-500/10 transition-colors cursor-pointer ml-auto sm:ml-2"
              title="ล้างตัวกรองทั้งหมด"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>ล้างตัวกรอง</span>
            </button>
          )}
        </div>
      </div>

      {/* Cascading Dropdowns Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Dropdown 1: University */}
        <div className="relative">
          <label className="block text-[11px] font-bold text-[var(--theme-text-muted)] mb-1 flex items-center gap-1">
            <Building2 className="w-3 h-3 text-[var(--theme-primary)]" />
            <span>มหาวิทยาลัย ({universities.length || 37})</span>
          </label>
          <div className="relative">
            <select
              value={selectedUni}
              onChange={(e) => {
                const newUni = e.target.value;
                onSelectUni(newUni);
                onSelectFaculty("all");
                onSelectDepartment("all");
              }}
              disabled={loadingUnis}
              className="ui-field w-full appearance-none px-3.5 py-2.5 pr-8 text-xs sm:text-sm font-bold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] cursor-pointer disabled:opacity-60 truncate"
            >
              <option value="all">ทุกมหาวิทยาลัย (All Universities)</option>
              {universities.map((u) => (
                <option key={u.name_th} value={u.name_th}>
                  {u.name_th} {u.abbr ? `(${u.abbr})` : ""}
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[var(--theme-text-muted)] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* Dropdown 2: Faculty */}
        <div className="relative">
          <label className="block text-[11px] font-bold text-[var(--theme-text-muted)] mb-1 flex items-center gap-1">
            <GraduationCap className="w-3 h-3 text-[var(--theme-primary)]" />
            <span>คณะ / สำนักวิชา {faculties.length > 0 ? `(${faculties.length})` : ""}</span>
          </label>
          <div className="relative">
            <select
              value={selectedFaculty}
              onChange={(e) => {
                const newFac = e.target.value;
                onSelectFaculty(newFac);
                onSelectDepartment("all");
              }}
              disabled={loadingFacs || faculties.length === 0}
              className="ui-field w-full appearance-none px-3.5 py-2.5 pr-8 text-xs sm:text-sm font-bold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed truncate"
            >
              <option value="all">
                {selectedUni === "all" && selectedRegion === "all"
                  ? "ทุกคณะ (เลือกมหาวิทยาลัยเพื่อเจาะจง)"
                  : "ทุกคณะ / สำนักวิชา (All Faculties)"}
              </option>
              {faculties.map((f) => (
                <option key={f.faculty_th} value={f.faculty_th}>
                  {f.faculty_th} {f.advisor_count > 0 ? `(${f.advisor_count} อ.)` : ""}
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[var(--theme-text-muted)] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* Dropdown 3: Department / Discipline */}
        <div className="relative">
          <label className="block text-[11px] font-bold text-[var(--theme-text-muted)] mb-1 flex items-center gap-1">
            <BookOpen className="w-3 h-3 text-[var(--theme-primary)]" />
            <span>ภาควิชา / สาขา {departments.length > 0 ? `(${departments.length})` : ""}</span>
          </label>
          <div className="relative">
            <select
              value={selectedDepartment}
              onChange={(e) => onSelectDepartment(e.target.value)}
              disabled={loadingDepts || selectedFaculty === "all" || departments.length === 0}
              className="ui-field w-full appearance-none px-3.5 py-2.5 pr-8 text-xs sm:text-sm font-bold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed truncate"
            >
              <option value="all">
                {selectedFaculty === "all"
                  ? "เลือกคณะเพื่อดูสาขาวิชา"
                  : "ทุกภาควิชา / สาขาวิชา (All Departments)"}
              </option>
              {departments.map((d) => (
                <option key={d.department_th} value={d.department_th}>
                  {d.department_th} {d.advisor_count > 0 ? `(${d.advisor_count} อ.)` : ""}
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[var(--theme-text-muted)] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* Dropdown 4: Degree Level (Courses) or Research Tier (Advisors) or Filter Status (Labs) */}
        <div className="relative">
          <label className="block text-[11px] font-bold text-[var(--theme-text-muted)] mb-1 flex items-center gap-1">
            <SlidersHorizontal className="w-3 h-3 text-[var(--theme-primary)]" />
            <span>
              {activeTab === "courses"
                ? "ระดับการศึกษา"
                : activeTab === "advisors"
                ? "ระดับผลงานวิจัย (Research Tier)"
                : "ตัวช่วยคัดกรอง"}
            </span>
          </label>
          {activeTab === "courses" ? (
            <div className="relative">
              <select
                value={selectedDegree}
                onChange={(e) => onSelectDegree(e.target.value)}
                className="ui-field w-full appearance-none px-3.5 py-2.5 pr-8 text-xs sm:text-sm font-bold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] cursor-pointer"
              >
                <option value="all">ทุกระดับการศึกษา (All Levels)</option>
                <option value="ปริญญาตรี">ปริญญาตรี (Bachelor)</option>
                <option value="ปริญญาโท">ปริญญาโท (Master)</option>
                <option value="ปริญญาเอก">ปริญญาเอก (Doctorate)</option>
              </select>
              <ChevronDown className="w-4 h-4 text-[var(--theme-text-muted)] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          ) : activeTab === "advisors" ? (
            <div className="relative">
              <select
                value={selectedResearchTier}
                onChange={(e) => onSelectResearchTier && onSelectResearchTier(e.target.value)}
                className="ui-field w-full appearance-none px-3.5 py-2.5 pr-8 text-xs sm:text-sm font-bold focus:outline-none focus:ring-2 focus:ring-[var(--theme-primary)] cursor-pointer truncate"
              >
                <option value="all">ทุกระดับผลงาน (All Advisors)</option>
                <option value="indexed">มีประวัติวิจัย (h-index &gt; 0)</option>
                <option value="elite">🏆 นักวิจัยแนวหน้า (h ≥ 20)</option>
              </select>
              <ChevronDown className="w-4 h-4 text-[var(--theme-text-muted)] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          ) : (
            <div className="flex items-center h-[42px] px-3.5 rounded-xl bg-[var(--theme-card-subtle)] border border-[var(--theme-border)] text-xs font-semibold text-[var(--theme-text-muted)]">
              {hasActiveFilter ? (
                <span className="text-[var(--theme-primary)] font-bold truncate">
                  {selectedDepartment !== "all"
                    ? `สาขา: ${selectedDepartment}`
                    : selectedFaculty !== "all"
                    ? `คณะ: ${selectedFaculty}`
                    : selectedUni !== "all"
                    ? `ม.: ${selectedUni}`
                    : "กำลังกรองตามภูมิภาค"}
                </span>
              ) : (
                <span>แสดงข้อมูลทั้งหมด</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

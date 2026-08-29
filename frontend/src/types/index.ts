export interface Publication {
  title: string;
  year?: number;
  venue?: string;
  url?: string;
  citation_count?: number;
}

export interface FacultyMember {
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
  featured_publications?: Publication[];
  scholar_url?: string;
}

export interface SearchMatchResult {
  faculty: FacultyMember;
  match_score: number;
  ai_explanation?: string;
  matched_keywords?: string[];
}

export interface Course {
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

export interface RiasecScore {
  realistic: number;
  investigative: number;
  artistic: number;
  social: number;
  enterprising: number;
  conventional: number;
}

export interface CareerItem {
  title: string;
  description: string;
  match_percentage: number;
  skills: string[];
  growth_outlook: string;
}

export interface CareerProfileResponse {
  tier: string;
  archetype_title: string;
  archetype_code: string;
  archetype_description: string;
  riasec_scores: RiasecScore;
  personality_summary: string;
  strengths: string[];
  ideal_work_environment: string;
  campus_vibe_match?: string;
  learning_style_match?: string;
  lifestyle_highlights: string[];
  growth_advice: string;
  share_quote: string;
  top_careers: CareerItem[];
  recommended_courses: Course[];
}

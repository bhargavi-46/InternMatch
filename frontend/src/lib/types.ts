export type Level = "internship" | "entry_level" | "other";

export interface Job {
  id: number;
  company: string;
  title: string;
  location: string;
  is_remote: boolean;
  experience_level: Level;
  min_years_experience: number | null;
  url: string;
  posted_at: string | null;
  source: string;
}

export interface Profile {
  summary: string;
  skills: string[];
  target_roles: string[];
  education: string | null;
  graduation_year: number | null;
  years_experience: number;
  preferred_locations: string[];
}

export interface Filters {
  levels: Level[];
  remote_only: boolean;
  location: string | null;
  max_years_experience: number | null;
}

export interface Match {
  job: Job;
  score: number;
  semantic: number;
  skill_coverage: number;
  matched_skills: string[];
  missing_skills: string[];
}

export interface SearchHit {
  job: Job;
  score: number;
}

export interface Explanation {
  fit_score: number;
  summary: string;
  matching_skills: string[];
  missing_skills: string[];
  how_to_prepare: string[];
}

export interface Stats {
  active_jobs: number;
  internships: number;
  entry_level: number;
  companies: number;
  last_refreshed: string | null;
}

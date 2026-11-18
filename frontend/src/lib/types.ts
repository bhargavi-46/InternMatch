export type Level = "internship" | "entry_level" | "other";

export type RoleFamily = "swe" | "ml_ai" | "data" | "devops_cloud" | "security" | "qa" | "other" | "non_tech";

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
  role_family: RoleFamily | null;
  duration_months: number | null;
  start_month: string | null;
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
  role_families: RoleFamily[];
  min_duration_months: number | null;
  posted_within_days: number | null;
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

export type AppStatus = "saved" | "applied" | "oa" | "interview" | "offer" | "rejected";

export interface Application {
  job: Job;
  status: AppStatus;
  history: { status: AppStatus; at: string }[];
  notes: string;
}

export interface Resource {
  title: string;
  url: string;
}

export interface PrepTopic {
  name: string;
  category: string;
  why: string;
  priority: "high" | "medium" | "low";
  student_knows: boolean;
  resources: Resource[];
}

export interface InterviewQuestion {
  question: string;
  kind: "technical" | "coding" | "system_design" | "behavioral" | "resume";
  hint: string;
}

export interface PrepPlan {
  summary: string;
  topics: PrepTopic[];
  interview_questions: InterviewQuestion[];
  week_plan: string[];
}

export interface QuizQuestion {
  topic: string;
  question: string;
  options: string[];
  answer_index: number;
  explanation: string;
}

export interface InterviewTurn {
  role: "interviewer" | "candidate";
  content: string;
}

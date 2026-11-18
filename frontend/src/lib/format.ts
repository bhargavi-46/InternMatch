import type { Level, RoleFamily } from "./types";

export const LEVEL_LABEL: Record<Level, string> = {
  internship: "Internship",
  entry_level: "Entry level",
  other: "Experienced",
};

export function timeAgo(iso: string | null): string | null {
  if (!iso) return null;
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days} days ago`;
  const months = Math.floor(days / 30);
  return months === 1 ? "1 month ago" : `${months} months ago`;
}

export function hoursAgo(iso: string | null): string | null {
  if (!iso) return null;
  const hours = Math.floor((Date.now() - new Date(iso).getTime()) / 3_600_000);
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  return timeAgo(iso);
}

export const ROLE_LABEL: Record<RoleFamily, string> = {
  swe: "Software",
  ml_ai: "AI / ML",
  data: "Data",
  devops_cloud: "DevOps / Cloud",
  security: "Security",
  qa: "QA / Testing",
  other: "Other tech",
  non_tech: "Non-tech",
};

export const TECH_FAMILIES: RoleFamily[] = ["swe", "ml_ai", "data", "devops_cloud", "security", "qa", "other"];

export function daysAgo(iso: string | null): number | null {
  if (!iso) return null;
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
}

import { LEVEL_LABEL, daysAgo, timeAgo } from "@/lib/format";
import type { Job } from "@/lib/types";

const LEVEL_STYLE = {
  internship: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  entry_level: "bg-sky-50 text-sky-800 ring-sky-200",
  other: "bg-slate-100 text-slate-700 ring-slate-200",
} as const;

const BADGE = "rounded-full px-2 py-0.5 text-xs font-medium ring-1";
const OLD_AFTER_DAYS = 90;

export function JobHeader({ job }: { job: Job }) {
  const posted = timeAgo(job.posted_at);
  const age = daysAgo(job.posted_at);
  return (
    <div className="min-w-0">
      <div className="flex flex-wrap items-center gap-2">
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-slate-900 hover:text-blue-700 hover:underline"
        >
          {job.title}
        </a>
        <span className={`${BADGE} ${LEVEL_STYLE[job.experience_level]}`}>{LEVEL_LABEL[job.experience_level]}</span>
        {job.duration_months && (
          <span className={`${BADGE} bg-violet-50 text-violet-800 ring-violet-200`}>
            {job.duration_months} month{job.duration_months === 1 ? "" : "s"}
          </span>
        )}
        {job.start_month && (
          <span className={`${BADGE} bg-indigo-50 text-indigo-800 ring-indigo-200`}>Starts {job.start_month}</span>
        )}
        {age !== null && age <= 7 && <span className={`${BADGE} bg-amber-50 text-amber-800 ring-amber-200`}>New</span>}
        {job.role_family === "non_tech" && (
          <span className={`${BADGE} bg-slate-100 text-slate-600 ring-slate-200`}>Non-tech</span>
        )}
      </div>
      <p className="mt-0.5 text-sm text-slate-600">
        {job.company} · {job.location || "Location not listed"}
        {job.is_remote && " · Remote"}
        {posted && <span className="text-slate-400"> · {posted}</span>}
      </p>
      {age !== null && age > OLD_AFTER_DAYS && (
        <p className="mt-1 text-xs text-amber-700">
          Posted over 3 months ago. It is still listed, but check that it is open before you spend time on it.
        </p>
      )}
    </div>
  );
}

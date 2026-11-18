import { LEVEL_LABEL, timeAgo } from "@/lib/format";
import type { Job } from "@/lib/types";

const LEVEL_STYLE = {
  internship: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  entry_level: "bg-sky-50 text-sky-800 ring-sky-200",
  other: "bg-slate-100 text-slate-700 ring-slate-200",
} as const;

export function JobHeader({ job }: { job: Job }) {
  const posted = timeAgo(job.posted_at);
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
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${LEVEL_STYLE[job.experience_level]}`}>
          {LEVEL_LABEL[job.experience_level]}
        </span>
      </div>
      <p className="mt-0.5 text-sm text-slate-600">
        {job.company} · {job.location || "Location not listed"}
        {job.is_remote && " · Remote"}
        {posted && <span className="text-slate-400"> · {posted}</span>}
      </p>
    </div>
  );
}

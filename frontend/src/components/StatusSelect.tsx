"use client";

import { STATUSES, STATUS_LABEL, STATUS_STYLE } from "@/lib/tracker";
import type { AppStatus } from "@/lib/types";

interface Props {
  status: AppStatus | null;
  onChange: (status: AppStatus | null) => void;
}

/** Track a job: Saved → Applied → Online test → Interview → Offer / Rejected. */
export function StatusSelect({ status, onChange }: Props) {
  if (status === null) {
    return (
      <span className="inline-flex gap-2">
        <button
          type="button"
          onClick={() => onChange("saved")}
          className="rounded-md px-3 py-1.5 font-medium text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50"
        >
          Save
        </button>
        <button
          type="button"
          onClick={() => onChange("applied")}
          className="rounded-md px-3 py-1.5 font-medium text-blue-700 ring-1 ring-blue-200 hover:bg-blue-50"
          title="Click after you have applied on the company's site"
        >
          I applied
        </button>
      </span>
    );
  }
  return (
    <select
      aria-label="Application status"
      value={status}
      onChange={(e) => onChange(e.target.value === "remove" ? null : (e.target.value as AppStatus))}
      className={`rounded-md px-2 py-1.5 text-sm font-medium ring-1 outline-none ${STATUS_STYLE[status]}`}
    >
      {STATUSES.map((s) => (
        <option key={s} value={s}>
          {STATUS_LABEL[s]}
        </option>
      ))}
      <option value="remove">Stop tracking</option>
    </select>
  );
}

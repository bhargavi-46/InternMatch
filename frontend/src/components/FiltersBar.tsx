"use client";

import type { Filters, Level } from "@/lib/types";
import { LEVEL_LABEL } from "@/lib/format";

const LEVELS: Level[] = ["internship", "entry_level", "other"];

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export function FiltersBar({ filters, onChange }: Props) {
  function toggleLevel(level: Level) {
    const levels = filters.levels.includes(level)
      ? filters.levels.filter((l) => l !== level)
      : [...filters.levels, level];
    onChange({ ...filters, levels });
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      {LEVELS.map((level) => {
        const on = filters.levels.includes(level);
        return (
          <button
            key={level}
            type="button"
            aria-pressed={on}
            onClick={() => toggleLevel(level)}
            className={`rounded-full px-3 py-1 ring-1 transition ${
              on ? "bg-slate-900 text-white ring-slate-900" : "bg-white text-slate-700 ring-slate-300 hover:ring-slate-400"
            }`}
          >
            {LEVEL_LABEL[level]}
          </button>
        );
      })}
      <label className="ml-1 inline-flex items-center gap-1.5 text-slate-700">
        <input
          type="checkbox"
          checked={filters.remote_only}
          onChange={(e) => onChange({ ...filters, remote_only: e.target.checked })}
          className="size-4 accent-blue-600"
        />
        Remote only
      </label>
      <label className="inline-flex items-center gap-1.5 text-slate-700">
        <input
          type="checkbox"
          checked={filters.max_years_experience !== null}
          onChange={(e) => onChange({ ...filters, max_years_experience: e.target.checked ? 1 : null })}
          className="size-4 accent-blue-600"
        />
        Hide roles needing 2+ years
      </label>
      <input
        value={filters.location ?? ""}
        onChange={(e) => onChange({ ...filters, location: e.target.value || null })}
        placeholder="City (e.g. Bengaluru)"
        className="w-40 rounded-full border border-slate-300 bg-white px-3 py-1 outline-none focus:border-blue-500"
      />
    </div>
  );
}

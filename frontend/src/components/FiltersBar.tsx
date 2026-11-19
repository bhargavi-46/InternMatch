"use client";

import { LEVEL_LABEL, ROLE_LABEL } from "@/lib/format";
import type { Filters, Level, RoleFamily } from "@/lib/types";

const LEVELS: Level[] = ["internship", "entry_level", "other"];
const ROLES: RoleFamily[] = ["swe", "ml_ai", "data", "devops_cloud", "security", "qa", "other", "non_tech"];

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((x) => x !== item) : [...list, item];
}

function Chip({
  on,
  onClick,
  children,
  small,
}: {
  on: boolean;
  onClick: () => void;
  children: React.ReactNode;
  small?: boolean;
}) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className={`rounded-full ring-1 transition ${small ? "px-2.5 py-0.5 text-xs" : "px-3 py-1"} ${
        on ? "bg-slate-900 text-white ring-slate-900" : "bg-white text-slate-700 ring-slate-300 hover:ring-slate-400"
      }`}
    >
      {children}
    </button>
  );
}

export function FiltersBar({ filters, onChange }: Props) {
  return (
    <div className="space-y-2 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        {LEVELS.map((level) => (
          <Chip
            key={level}
            on={filters.levels.includes(level)}
            onClick={() => onChange({ ...filters, levels: toggle(filters.levels, level) })}
          >
            {LEVEL_LABEL[level]}
          </Chip>
        ))}
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
          Experience
          <select
            value={filters.max_years_experience ?? "any"}
            onChange={(e) =>
              onChange({
                ...filters,
                max_years_experience: e.target.value === "any" ? null : Number(e.target.value),
              })
            }
            className="rounded-full border border-slate-300 bg-white px-2 py-1 outline-none focus:border-blue-500"
          >
            <option value="0">Fresher (0 years)</option>
            <option value="1">Up to 1 year</option>
            <option value="any">Any</option>
          </select>
        </label>
        <input
          value={filters.location ?? ""}
          onChange={(e) => onChange({ ...filters, location: e.target.value || null })}
          placeholder="City (e.g. Bengaluru)"
          className="w-40 rounded-full border border-slate-300 bg-white px-3 py-1 outline-none focus:border-blue-500"
        />
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-xs font-medium text-slate-500">Roles</span>
        {ROLES.map((role) => (
          <Chip
            key={role}
            small
            on={filters.role_families.includes(role)}
            onClick={() =>
              onChange({
                ...filters,
                role_families: toggle(filters.role_families, role),
              })
            }
          >
            {ROLE_LABEL[role]}
          </Chip>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label
          className="inline-flex items-center gap-1.5 text-slate-700"
          title="Only internships whose posting states a length of 6 months or more"
        >
          <input
            type="checkbox"
            checked={filters.min_duration_months !== null}
            onChange={(e) =>
              onChange({
                ...filters,
                min_duration_months: e.target.checked ? 6 : null,
              })
            }
            className="size-4 accent-blue-600"
          />
          6+ month internships
        </label>
        <label className="inline-flex items-center gap-1.5 text-slate-700">
          Posted
          <select
            value={filters.posted_within_days ?? ""}
            onChange={(e) =>
              onChange({
                ...filters,
                posted_within_days: e.target.value ? Number(e.target.value) : null,
              })
            }
            className="rounded-full border border-slate-300 bg-white px-2 py-0.5 outline-none focus:border-blue-500"
          >
            <option value="">any time</option>
            <option value="7">this week</option>
            <option value="30">this month</option>
            <option value="90">last 3 months</option>
          </select>
        </label>
      </div>
    </div>
  );
}

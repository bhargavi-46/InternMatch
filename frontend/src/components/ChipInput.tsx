"use client";

import { useState } from "react";

interface Props {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder: string;
  tone?: "blue" | "slate";
}

export function ChipInput({ label, values, onChange, placeholder, tone = "slate" }: Props) {
  const [draft, setDraft] = useState("");
  const chip = tone === "blue" ? "bg-blue-50 text-blue-800 ring-blue-200" : "bg-slate-100 text-slate-800 ring-slate-200";

  function add() {
    const items = draft
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s && !values.some((v) => v.toLowerCase() === s.toLowerCase()));
    if (items.length) onChange([...values, ...items]);
    setDraft("");
  }

  return (
    <div>
      <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {values.map((value) => (
          <span key={value} className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-sm ring-1 ${chip}`}>
            {value}
            <button
              type="button"
              aria-label={`Remove ${value}`}
              onClick={() => onChange(values.filter((v) => v !== value))}
              className="text-slate-400 hover:text-slate-700"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            add();
          }
        }}
        onBlur={add}
        placeholder={placeholder}
        className="mt-2 w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </div>
  );
}

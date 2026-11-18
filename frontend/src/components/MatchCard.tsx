"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { Explanation, Match, Profile } from "@/lib/types";

import { JobHeader } from "./JobHeader";

interface Props {
  match: Match;
  profile: Profile;
  saved: boolean;
  onToggleSave: () => void;
  onHide: () => void;
}

export function MatchCard({ match, profile, saved, onToggleSave, onHide }: Props) {
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const percent = Math.round(match.score * 100);

  async function explain() {
    setLoading(true);
    setError(null);
    try {
      setExplanation(await api.explain(match.job.id, profile));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not explain this match.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-4">
        <JobHeader job={match.job} />
        <div className="shrink-0 text-right" title="Overall match score">
          <p className="text-lg font-semibold text-slate-900">{percent}%</p>
          <div className="mt-1 h-1.5 w-16 rounded-full bg-slate-100">
            <div className="h-1.5 rounded-full bg-blue-600" style={{ width: `${Math.min(percent, 100)}%` }} />
          </div>
        </div>
      </div>

      {(match.matched_skills.length > 0 || match.missing_skills.length > 0) && (
        <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
          {match.matched_skills.map((s) => (
            <span key={s} className="rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-800 ring-1 ring-emerald-200">
              ✓ {s}
            </span>
          ))}
          {match.missing_skills.slice(0, 6).map((s) => (
            <span key={s} className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-800 ring-1 ring-amber-200">
              + {s}
            </span>
          ))}
        </div>
      )}

      {explanation && (
        <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">
          <p className="font-medium text-slate-900">Fit: {explanation.fit_score}/10</p>
          <p className="mt-1 text-slate-700">{explanation.summary}</p>
          {explanation.how_to_prepare.length > 0 && (
            <>
              <p className="mt-2 font-medium text-slate-900">How to prepare</p>
              <ul className="mt-1 list-disc space-y-0.5 pl-5 text-slate-700">
                {explanation.how_to_prepare.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
      {error && <p className="mt-3 rounded-md bg-red-50 p-2.5 text-sm text-red-700">{error}</p>}

      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
        <a
          href={match.job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md bg-slate-900 px-3 py-1.5 font-medium text-white hover:bg-slate-700"
        >
          Apply
        </a>
        {!explanation && (
          <button
            type="button"
            onClick={explain}
            disabled={loading}
            className="rounded-md px-3 py-1.5 font-medium text-blue-700 ring-1 ring-blue-200 hover:bg-blue-50 disabled:opacity-60"
          >
            {loading ? "Thinking…" : "Explain my fit"}
          </button>
        )}
        <button
          type="button"
          onClick={onToggleSave}
          aria-pressed={saved}
          className={`rounded-md px-3 py-1.5 font-medium ring-1 ${
            saved ? "bg-emerald-50 text-emerald-800 ring-emerald-300" : "text-slate-700 ring-slate-300 hover:bg-slate-50"
          }`}
        >
          {saved ? "Saved" : "Save"}
        </button>
        <button type="button" onClick={onHide} className="ml-auto text-slate-500 hover:text-slate-800">
          Not for me
        </button>
      </div>
    </article>
  );
}

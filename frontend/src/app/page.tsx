"use client";

import { useEffect, useState } from "react";

import { ChatPanel } from "@/components/ChatPanel";
import { FiltersBar } from "@/components/FiltersBar";
import { MatchCard } from "@/components/MatchCard";
import { ProfilePanel } from "@/components/ProfilePanel";
import { SearchPanel } from "@/components/SearchPanel";
import { api } from "@/lib/api";
import { hoursAgo } from "@/lib/format";
import { useStoredState } from "@/lib/storage";
import type { Filters, Match, Profile, Stats } from "@/lib/types";

const DEFAULT_FILTERS: Filters = {
  levels: ["internship", "entry_level"],
  remote_only: false,
  location: null,
  max_years_experience: 1,
};

type Tab = "matches" | "search";

export default function Home() {
  const [profile, setProfile] = useStoredState<Profile | null>("im.profile", null);
  const [filters, setFilters] = useStoredState<Filters>("im.filters", DEFAULT_FILTERS);
  const [savedIds, setSavedIds] = useStoredState<number[]>("im.saved", []);
  const [hiddenIds, setHiddenIds] = useStoredState<number[]>("im.hidden", []);
  const [tab, setTab] = useState<Tab>("matches");
  const [chatOpen, setChatOpen] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch(() => setStats(null));
  }, []);

  const hasProfileInput = !!profile && (profile.skills.length > 0 || profile.target_roles.length > 0 || !!profile.summary);

  useEffect(() => {
    if (!profile || !hasProfileInput) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.match({ profile, filters, liked_ids: savedIds, hidden_ids: hiddenIds });
        if (!cancelled) setMatches(result);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load matches.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 400);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [profile, hasProfileInput, filters, savedIds, hiddenIds]);

  function toggleSave(id: number) {
    setSavedIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]));
  }

  function hide(id: number) {
    setHiddenIds((ids) => [...ids, id]);
    setMatches((m) => m?.filter((x) => x.job.id !== id) ?? null);
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Intern<span className="text-blue-600">Match</span>
          </h1>
          <p className="mt-1 text-slate-600">Internships ranked by how well they fit you, with the skills you&apos;re missing.</p>
        </div>
        {stats && (
          <p className="text-sm text-slate-500">
            <span className="font-medium text-slate-800">{stats.active_jobs.toLocaleString()}</span> live roles ·{" "}
            <span className="font-medium text-slate-800">{stats.internships + stats.entry_level}</span> for students ·{" "}
            {stats.companies} companies
            {stats.last_refreshed && <> · updated {hoursAgo(stats.last_refreshed)}</>}
          </p>
        )}
      </header>

      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        <div className="lg:sticky lg:top-6 lg:self-start">
          <ProfilePanel
            profile={profile}
            onChange={(p) => {
              setProfile(p);
              if (!p) setMatches(null);
            }}
          />
        </div>

        <section className="min-w-0 space-y-4">
          <div className="flex gap-1 rounded-lg bg-slate-200/60 p-1 text-sm font-medium sm:w-fit">
            {(["matches", "search"] as Tab[]).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`flex-1 rounded-md px-4 py-1.5 sm:flex-none ${
                  tab === t ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {t === "matches" ? "Your matches" : "Search"}
              </button>
            ))}
          </div>

          <FiltersBar filters={filters} onChange={setFilters} />

          {tab === "search" ? (
            <SearchPanel filters={filters} />
          ) : !hasProfileInput ? (
            <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-slate-600">
              Add your resume or a few skills on the left to see your ranked matches.
            </div>
          ) : (
            <div className="space-y-3">
              {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
              {loading && !matches && <p className="text-sm text-slate-500">Finding your matches…</p>}
              {matches?.length === 0 && (
                <p className="rounded-xl bg-white p-6 text-sm text-slate-600 ring-1 ring-slate-200">
                  No roles match these filters right now. Try including entry-level or experienced roles, or clear the city.
                </p>
              )}
              {matches && matches.length > 0 && (
                <p className="text-sm text-slate-500">
                  {matches.length} roles, best fit first. Saving and hiding roles tunes the ranking to you.
                  {loading && " Updating…"}
                </p>
              )}
              {matches?.map((match) => (
                <MatchCard
                  key={match.job.id}
                  match={match}
                  profile={profile!}
                  saved={savedIds.includes(match.job.id)}
                  onToggleSave={() => toggleSave(match.job.id)}
                  onHide={() => hide(match.job.id)}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      {chatOpen ? (
        <ChatPanel profile={hasProfileInput ? profile : null} onClose={() => setChatOpen(false)} />
      ) : (
        <button
          type="button"
          onClick={() => setChatOpen(true)}
          className="fixed right-4 bottom-4 z-20 rounded-full bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-lg hover:bg-blue-700"
        >
          Ask InternMatch
        </button>
      )}
    </main>
  );
}

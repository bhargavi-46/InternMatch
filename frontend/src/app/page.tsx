"use client";

import { useEffect, useMemo, useState } from "react";

import { ApplicationsPanel } from "@/components/ApplicationsPanel";
import { ChatPanel } from "@/components/ChatPanel";
import { FiltersBar } from "@/components/FiltersBar";
import { MatchCard } from "@/components/MatchCard";
import { MockInterview } from "@/components/MockInterview";
import { ProfilePanel } from "@/components/ProfilePanel";
import { QuizPanel } from "@/components/QuizPanel";
import { SearchPanel } from "@/components/SearchPanel";
import { api } from "@/lib/api";
import { TECH_FAMILIES, hoursAgo } from "@/lib/format";
import { useStoredState } from "@/lib/storage";
import { useApplications, usePrepPlans } from "@/lib/tracker";
import type { Filters, Job, Match, Profile, Stats } from "@/lib/types";

const DEFAULT_FILTERS: Filters = {
  levels: ["internship", "entry_level"],
  remote_only: false,
  location: null,
  max_years_experience: 1,
  role_families: TECH_FAMILIES,
  min_duration_months: null,
  posted_within_days: null,
};

type Tab = "matches" | "search" | "applications" | "practice";

const TAB_LABEL: Record<Tab, string> = {
  matches: "Your matches",
  search: "Search",
  applications: "Applications",
  practice: "Daily practice",
};

export default function Home() {
  const [profile, setProfile] = useStoredState<Profile | null>("im.profile", null);
  const [storedFilters, setFilters] = useStoredState<Filters>("im.filters", DEFAULT_FILTERS);
  // Filters saved by an older version lack the newer fields.
  const filters = useMemo(() => ({ ...DEFAULT_FILTERS, ...storedFilters }), [storedFilters]);
  const { apps, setStatus, setNotes } = useApplications();
  const { plans, savePlan } = usePrepPlans();
  const [interviewJob, setInterviewJob] = useState<Job | null>(null);
  // Tracked jobs (except rejections) steer the ranking like likes. A string key keeps edits to notes from refetching.
  const likedKey = Object.values(apps)
    .filter((a) => a.status !== "rejected")
    .map((a) => a.job.id)
    .sort((a, b) => a - b)
    .join(",");
  const trackedCount = Object.keys(apps).length;
  const likedIds = useMemo(() => (likedKey ? likedKey.split(",").map(Number) : []), [likedKey]);
  const [hiddenIds, setHiddenIds] = useStoredState<number[]>("im.hidden", []);
  const [tab, setTab] = useState<Tab>("matches");
  const [chatOpen, setChatOpen] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .stats()
      .then(setStats)
      .catch(() => setStats(null));
  }, []);

  const hasProfileInput =
    !!profile && (profile.skills.length > 0 || profile.target_roles.length > 0 || !!profile.summary);

  useEffect(() => {
    if (!profile || !hasProfileInput) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.match({
          profile,
          filters,
          liked_ids: likedIds,
          hidden_ids: hiddenIds,
        });
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
  }, [profile, hasProfileInput, filters, likedIds, hiddenIds]);

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
          <p className="mt-1 text-slate-600">
            Internships ranked by how well they fit you, with the skills you&apos;re missing.
          </p>
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
          <div className="grid grid-cols-2 gap-1 rounded-lg bg-slate-200/60 p-1 text-sm font-medium sm:flex sm:w-fit">
            {(["matches", "search", "applications", "practice"] as Tab[]).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`rounded-md px-4 py-1.5 ${
                  tab === t ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {TAB_LABEL[t]}
                {t === "applications" && trackedCount > 0 && (
                  <span className="ml-1.5 rounded-full bg-blue-600 px-1.5 text-xs text-white">{trackedCount}</span>
                )}
              </button>
            ))}
          </div>

          {(tab === "matches" || tab === "search") && <FiltersBar filters={filters} onChange={setFilters} />}

          {tab === "applications" ? (
            <ApplicationsPanel
              apps={apps}
              plans={plans}
              profile={hasProfileInput ? profile : null}
              onStatus={setStatus}
              onNotes={setNotes}
              onPlan={savePlan}
              onInterview={setInterviewJob}
            />
          ) : tab === "practice" ? (
            <QuizPanel apps={apps} plans={plans} profile={hasProfileInput ? profile : null} />
          ) : tab === "search" ? (
            <SearchPanel filters={filters} apps={apps} onStatus={setStatus} />
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
                  No roles match these filters right now. Try including entry-level or experienced roles, or clear the
                  city.
                </p>
              )}
              {matches && matches.length > 0 && (
                <p className="text-sm text-slate-500">
                  {matches.length} roles, best fit first. Saving, tracking and hiding roles tunes the ranking to you.
                  {loading && " Updating…"}
                </p>
              )}
              {matches?.map((match) => (
                <MatchCard
                  key={match.job.id}
                  match={match}
                  profile={profile!}
                  status={apps[match.job.id]?.status ?? null}
                  onStatus={(s) => setStatus(match.job, s)}
                  onHide={() => hide(match.job.id)}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      {interviewJob && (
        <MockInterview
          job={interviewJob}
          profile={hasProfileInput ? profile : null}
          onClose={() => setInterviewJob(null)}
        />
      )}

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

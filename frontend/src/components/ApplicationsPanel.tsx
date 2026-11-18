"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import { type Applications, STATUSES, STATUS_LABEL, STATUS_STYLE, daysSince, hasApplied, since } from "@/lib/tracker";
import type { Application, AppStatus, Job, PrepPlan, Profile } from "@/lib/types";

import { JobHeader } from "./JobHeader";
import { PrepPlanView } from "./PrepPlanView";
import { StatusSelect } from "./StatusSelect";

interface Props {
  apps: Applications;
  plans: Record<string, PrepPlan>;
  profile: Profile | null;
  onStatus: (job: Job, status: AppStatus | null) => void;
  onNotes: (jobId: number, notes: string) => void;
  onPlan: (jobId: number, plan: PrepPlan) => void;
  onInterview: (job: Job) => void;
}

interface Reminder {
  app: Application;
  text: string;
}

function reminders(apps: Application[]): Reminder[] {
  const out: Reminder[] = [];
  for (const app of apps) {
    const days = daysSince(since(app));
    if (app.status === "saved" && days >= 3) {
      out.push({
        app,
        text: `Saved ${days} days ago. Apply soon: internship openings fill up fast.`,
      });
    } else if (app.status === "applied" && days >= 10) {
      out.push({
        app,
        text: `Applied ${days} days ago with no update. Follow up with a recruiter on LinkedIn, and keep applying elsewhere.`,
      });
    } else if (app.status === "oa" || app.status === "interview") {
      out.push({
        app,
        text: `${STATUS_LABEL[app.status]} stage: open the prep plan, do today's quiz and take a mock interview.`,
      });
    }
  }
  return out;
}

function Stat({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <div className="rounded-xl bg-white p-3 ring-1 ring-slate-200" title={hint}>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}

function ApplicationRow({
  app,
  plan,
  profile,
  onStatus,
  onNotes,
  onPlan,
  onInterview,
}: {
  app: Application;
  plan: PrepPlan | undefined;
  profile: Profile | null;
} & Omit<Props, "apps" | "plans" | "profile">) {
  const [open, setOpen] = useState<"prep" | "notes" | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const appliedOn = since(app, "applied");

  async function makePlan() {
    setOpen("prep");
    if (plan) return;
    setLoading(true);
    setError(null);
    try {
      onPlan(app.job.id, await api.prep(app.job.id, profile));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not make a prep plan.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <JobHeader job={app.job} />
        <StatusSelect status={app.status} onChange={(s) => onStatus(app.job, s)} />
      </div>
      <p className="mt-1 text-xs text-slate-500">
        {appliedOn ? `Applied ${appliedOn.toLocaleDateString()}` : "Not applied yet"}
        {app.status !== "saved" &&
          app.status !== "applied" &&
          ` · ${STATUS_LABEL[app.status]} since ${since(app)?.toLocaleDateString()}`}
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
        <a
          href={app.job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md bg-slate-900 px-3 py-1.5 font-medium text-white hover:bg-slate-700"
        >
          {app.status === "saved" ? "Apply" : "Open posting"}
        </a>
        <button
          type="button"
          onClick={() => (open === "prep" ? setOpen(null) : makePlan())}
          className="rounded-md px-3 py-1.5 font-medium text-blue-700 ring-1 ring-blue-200 hover:bg-blue-50"
        >
          {open === "prep" ? "Hide prep plan" : plan ? "Prep plan" : "Make prep plan"}
        </button>
        <button
          type="button"
          onClick={() => onInterview(app.job)}
          className="rounded-md px-3 py-1.5 font-medium text-violet-700 ring-1 ring-violet-200 hover:bg-violet-50"
        >
          Mock interview
        </button>
        <button
          type="button"
          onClick={() => setOpen(open === "notes" ? null : "notes")}
          className="text-slate-600 hover:text-slate-900"
        >
          {app.notes ? "Notes ✎" : "Add notes"}
        </button>
      </div>

      {open === "notes" && (
        <textarea
          value={app.notes}
          onChange={(e) => onNotes(app.job.id, e.target.value)}
          rows={3}
          placeholder="Referral, recruiter name, test date, questions they asked…"
          className="mt-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
        />
      )}
      {open === "prep" && (
        <div className="mt-3 rounded-lg bg-slate-50 p-3">
          {loading && (
            <p className="text-sm text-slate-500">Reading the job description and your profile… (about 20 seconds)</p>
          )}
          {error && <p className="text-sm text-red-700">{error}</p>}
          {plan && <PrepPlanView plan={plan} />}
        </div>
      )}
    </article>
  );
}

export function ApplicationsPanel({ apps, plans, profile, onStatus, onNotes, onPlan, onInterview }: Props) {
  const [filter, setFilter] = useState<AppStatus | "all">("all");
  const list = Object.values(apps).sort((a, b) => (since(b)?.getTime() ?? 0) - (since(a)?.getTime() ?? 0));

  if (list.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-slate-600">
        Nothing tracked yet. On a match, click <b>Save</b> or <b>I applied</b> after applying on the company&apos;s
        site.
        <br />
        Your applications, prep plans and notes stay in this browser.
      </div>
    );
  }

  const applied = list.filter(hasApplied);
  const thisWeek = applied.filter((a) => daysSince(since(a, "applied")) < 7 && since(a, "applied")).length;
  const active = list.filter((a) => a.status === "oa" || a.status === "interview").length;
  const offers = list.filter((a) => a.status === "offer").length;
  const todo = reminders(list);
  const shown = filter === "all" ? list : list.filter((a) => a.status === filter);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Applied" value={applied.length} />
        <Stat label="Applied this week" value={thisWeek} hint="Aim for 10-15 a week during internship season" />
        <Stat label="Tests and interviews" value={active} />
        <Stat label="Offers" value={offers} />
      </div>

      {todo.length > 0 && (
        <section className="rounded-xl bg-amber-50 p-4 ring-1 ring-amber-200">
          <h3 className="text-sm font-semibold text-amber-900">To do</h3>
          <ul className="mt-2 space-y-1.5 text-sm text-amber-900">
            {todo.slice(0, 6).map(({ app, text }) => (
              <li key={app.job.id}>
                <b>
                  {app.job.title} · {app.job.company}
                </b>
                : {text}
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="flex flex-wrap gap-1.5 text-xs">
        {(["all", ...STATUSES] as const).map((s) => {
          const count = s === "all" ? list.length : list.filter((a) => a.status === s).length;
          if (s !== "all" && count === 0) return null;
          const on = filter === s;
          return (
            <button
              key={s}
              type="button"
              aria-pressed={on}
              onClick={() => setFilter(s)}
              className={`rounded-full px-2.5 py-1 ring-1 ${
                on
                  ? "bg-slate-900 text-white ring-slate-900"
                  : s === "all"
                    ? "bg-white ring-slate-300"
                    : STATUS_STYLE[s]
              }`}
            >
              {s === "all" ? "All" : STATUS_LABEL[s]} ({count})
            </button>
          );
        })}
      </div>

      <div className="space-y-3">
        {shown.map((app) => (
          <ApplicationRow
            key={app.job.id}
            app={app}
            plan={plans[app.job.id]}
            profile={profile}
            onStatus={onStatus}
            onNotes={onNotes}
            onPlan={onPlan}
            onInterview={onInterview}
          />
        ))}
      </div>
    </div>
  );
}

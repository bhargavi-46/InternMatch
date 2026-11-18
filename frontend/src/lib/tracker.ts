"use client";

import { useCallback } from "react";

import { useStoredState } from "./storage";
import type { Application, AppStatus, Job, PrepPlan } from "./types";

// Everything here lives in this browser only (localStorage): no account, nothing sent to the server.

export const STATUSES: AppStatus[] = ["saved", "applied", "oa", "interview", "offer", "rejected"];

export const STATUS_LABEL: Record<AppStatus, string> = {
  saved: "Saved",
  applied: "Applied",
  oa: "Online test",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
};

export const STATUS_STYLE: Record<AppStatus, string> = {
  saved: "bg-slate-100 text-slate-700 ring-slate-300",
  applied: "bg-blue-50 text-blue-800 ring-blue-200",
  oa: "bg-violet-50 text-violet-800 ring-violet-200",
  interview: "bg-amber-50 text-amber-800 ring-amber-200",
  offer: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  rejected: "bg-red-50 text-red-700 ring-red-200",
};

export type Applications = Record<string, Application>;

export function useApplications() {
  const [apps, setApps, loaded] = useStoredState<Applications>("im.applications", {});

  const setStatus = useCallback(
    (job: Job, status: AppStatus | null) =>
      setApps((prev) => {
        const next = { ...prev };
        if (status === null) {
          delete next[job.id];
          return next;
        }
        const current = prev[job.id];
        if (current?.status === status) return prev;
        const history = [...(current?.history ?? []), { status, at: new Date().toISOString() }];
        next[job.id] = { job, status, history, notes: current?.notes ?? "" };
        return next;
      }),
    [setApps],
  );

  const setNotes = useCallback(
    (jobId: number, notes: string) =>
      setApps((prev) => (prev[jobId] ? { ...prev, [jobId]: { ...prev[jobId], notes } } : prev)),
    [setApps],
  );

  return { apps, setStatus, setNotes, loaded };
}

export function usePrepPlans() {
  const [plans, setPlans] = useStoredState<Record<string, PrepPlan>>("im.prep", {});
  const savePlan = useCallback(
    (jobId: number, plan: PrepPlan) => setPlans((prev) => ({ ...prev, [jobId]: plan })),
    [setPlans],
  );
  return { plans, savePlan };
}

/** When the application entered `status` most recently, or null. */
export function since(app: Application, status: AppStatus = app.status): Date | null {
  for (let i = app.history.length - 1; i >= 0; i--) {
    if (app.history[i].status === status) return new Date(app.history[i].at);
  }
  return null;
}

export function daysSince(date: Date | null): number {
  return date ? Math.floor((Date.now() - date.getTime()) / 86_400_000) : 0;
}

/** Applied at any point (moving on to a test, interview, offer or rejection counts). */
export function hasApplied(app: Application): boolean {
  return app.status !== "saved";
}

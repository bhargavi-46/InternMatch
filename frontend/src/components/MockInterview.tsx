"use client";

import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import type { InterviewTurn, Job, Profile } from "@/lib/types";

import { Markdown } from "./Markdown";

interface Props {
  job: Job;
  profile: Profile | null;
  onClose: () => void;
}

/** A 6-question practice interview for one job, with feedback after every answer. Nothing is saved. */
export function MockInterview({ job, profile, onClose }: Props) {
  const [turns, setTurns] = useState<InterviewTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);
  const bottom = useRef<HTMLDivElement>(null);

  async function next(history: InterviewTurn[]) {
    setWaiting(true);
    setError(null);
    try {
      const { reply, done: finished } = await api.interview(job.id, profile, history);
      setTurns([...history, { role: "interviewer", content: reply }]);
      setDone(finished);
    } catch (e) {
      setError(e instanceof Error ? e.message : "The interviewer could not reply.");
    } finally {
      setWaiting(false);
    }
  }

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void next([]);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- start once when opened
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, waiting]);

  function answer() {
    const text = draft.trim();
    if (!text || waiting || done) return;
    setDraft("");
    const history: InterviewTurn[] = [...turns, { role: "candidate", content: text }];
    setTurns(history);
    void next(history);
  }

  const answered = turns.filter((t) => t.role === "candidate").length;

  return (
    <div className="fixed inset-0 z-30 flex items-end justify-center bg-slate-900/40 p-2 sm:items-center sm:p-6">
      <div className="flex h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl">
        <header className="flex items-start justify-between gap-3 border-b border-slate-200 px-4 py-3">
          <div className="min-w-0">
            <p className="font-semibold">Mock interview</p>
            <p className="truncate text-xs text-slate-500">
              {job.title} · {job.company} · question {Math.min(answered + 1, 6)} of 6
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close interview"
            className="text-xl text-slate-400 hover:text-slate-700"
          >
            ×
          </button>
        </header>

        <div className="flex-1 space-y-3 overflow-y-auto p-4 text-sm">
          <p className="rounded-md bg-blue-50 p-2.5 text-xs text-blue-900">
            Answer as you would out loud in a real interview. You get feedback and a score after each answer, and a
            summary at the end. Take your time.
          </p>
          {turns.map((t, i) => (
            <div key={i} className={t.role === "candidate" ? "flex justify-end" : ""}>
              <div
                className={
                  t.role === "candidate"
                    ? "max-w-[85%] rounded-lg bg-blue-600 px-3 py-2 whitespace-pre-wrap text-white"
                    : "max-w-[95%] rounded-lg bg-slate-50 px-3 py-2 text-slate-800 ring-1 ring-slate-200"
                }
              >
                {t.role === "candidate" ? t.content : <Markdown>{t.content}</Markdown>}
              </div>
            </div>
          ))}
          {waiting && (
            <p className="text-slate-500">The interviewer is thinking… (this can take up to half a minute)</p>
          )}
          {error && (
            <div className="rounded-md bg-red-50 p-2.5 text-red-700">
              {error}{" "}
              <button type="button" onClick={() => next(turns)} className="font-medium underline">
                Try again
              </button>
            </div>
          )}
          {done && !waiting && (
            <p className="rounded-md bg-emerald-50 p-2.5 text-emerald-800">
              Interview finished. Practise the weak spots in Daily practice, then try another round.
            </p>
          )}
          <div ref={bottom} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            answer();
          }}
          className="flex gap-2 border-t border-slate-200 p-3"
        >
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                answer();
              }
            }}
            rows={3}
            maxLength={4000}
            disabled={done}
            placeholder={done ? "Interview finished" : "Your answer (Enter to send, Shift+Enter for a new line)"}
            className="flex-1 resize-none rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 disabled:bg-slate-50"
          />
          <button
            type="submit"
            disabled={waiting || done || !draft.trim()}
            className="self-end rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

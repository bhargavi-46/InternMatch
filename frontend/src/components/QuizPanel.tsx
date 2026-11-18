"use client";

import { useMemo, useState } from "react";

import { api } from "@/lib/api";
import {
  EMPTY_STATS,
  type QuizStats,
  type TodayQuiz,
  accuracy,
  currentStreak,
  finishDay,
  recordAnswer,
  today,
  weakTopics,
} from "@/lib/quiz";
import { useStoredState } from "@/lib/storage";
import type { Applications } from "@/lib/tracker";
import type { PrepPlan, Profile } from "@/lib/types";

import { ChipInput } from "./ChipInput";
import { InlineMarkdown } from "./Markdown";

const CORE_TOPICS = ["Data structures & algorithms", "OOP", "DBMS & SQL", "Operating systems", "Computer networks"];
const ML_TOPICS = ["Machine learning fundamentals", "Deep learning", "LLMs & NLP"];

interface Props {
  apps: Applications;
  plans: Record<string, PrepPlan>;
  profile: Profile | null;
}

/** Topics from the prep plans of jobs still in play (high priority first), else sensible defaults. */
function planTopics(apps: Applications, plans: Record<string, PrepPlan>, profile: Profile | null): string[] {
  const rank = { high: 0, medium: 1, low: 2 };
  const topics = Object.values(apps)
    .filter((a) => a.status !== "rejected" && plans[a.job.id])
    .flatMap((a) => plans[a.job.id].topics)
    .filter((t) => t.category !== "behavioral")
    .sort((a, b) => rank[a.priority] - rank[b.priority])
    .map((t) => t.name);
  if (topics.length > 0) return [...new Set(topics)];
  const wantsMl = profile?.target_roles.some((r) => /\b(ml|ai|machine learning|data scien)/i.test(r));
  return [...CORE_TOPICS, ...(wantsMl ? ML_TOPICS : []), ...(profile?.skills.slice(0, 4) ?? [])];
}

export function QuizPanel({ apps, plans, profile }: Props) {
  const [stats, setStats] = useStoredState<QuizStats>("im.quiz.stats", EMPTY_STATS);
  const [quiz, setQuiz] = useStoredState<TodayQuiz | null>("im.quiz.today", null);
  const [extra, setExtra] = useStoredState<string[]>("im.quiz.topics", []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const suggested = useMemo(() => planTopics(apps, plans, profile), [apps, plans, profile]);
  const topics = [...new Set([...extra, ...suggested])].slice(0, 20);
  const weak = weakTopics(stats);
  const todays = quiz?.date === today() ? quiz : null;
  const answeredCount = todays?.answers.filter((a) => a !== null).length ?? 0;
  const finished = !!todays && answeredCount === todays.questions.length;
  const score = todays?.answers.filter((a, i) => a === todays.questions[i].answer_index).length ?? 0;
  const streak = currentStreak(stats);

  async function start() {
    setLoading(true);
    setError(null);
    try {
      const { questions } = await api.quiz({
        topics,
        weak_topics: weak,
        avoid: stats.recent,
        count: 10,
      });
      if (questions.length === 0) throw new Error("The quiz came back empty. Please try again.");
      setQuiz({ date: today(), questions, answers: questions.map(() => null) });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not make today's quiz.");
    } finally {
      setLoading(false);
    }
  }

  function choose(index: number, option: number) {
    if (!todays || todays.answers[index] !== null) return;
    const question = todays.questions[index];
    const answers = todays.answers.map((a, i) => (i === index ? option : a));
    setQuiz({ ...todays, answers });
    setStats((s) => {
      const next = recordAnswer(s, question.topic, option === question.answer_index);
      return answers.every((a) => a !== null) ? finishDay(next, todays.questions) : next;
    });
  }

  const tracked = Object.entries(stats.topics).sort(([, a], [, b]) => accuracy(a) - accuracy(b));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl bg-white p-3 ring-1 ring-slate-200">
          <p className="text-2xl font-semibold text-slate-900">{streak}</p>
          <p className="text-xs text-slate-500">day streak</p>
        </div>
        <div className="rounded-xl bg-white p-3 ring-1 ring-slate-200">
          <p className="text-2xl font-semibold text-slate-900">
            {todays ? `${answeredCount}/${todays.questions.length}` : "0/10"}
          </p>
          <p className="text-xs text-slate-500">answered today</p>
        </div>
        <div className="rounded-xl bg-white p-3 ring-1 ring-slate-200">
          <p className="text-2xl font-semibold text-slate-900">{weak.length}</p>
          <p className="text-xs text-slate-500">topics due for review</p>
        </div>
      </div>

      {!todays && (
        <section className="space-y-3 rounded-xl bg-white p-4 ring-1 ring-slate-200">
          <div>
            <h3 className="font-semibold text-slate-900">Today&apos;s 10 questions</h3>
            <p className="mt-0.5 text-sm text-slate-600">
              {Object.keys(plans).length > 0
                ? "Built from the prep plans of the jobs you're tracking, with extra questions on your weak topics."
                : "Make a prep plan for a tracked job to get questions from its job description. Until then, these are common interview topics."}
            </p>
          </div>
          <div>
            <p className="mb-1 text-xs font-medium text-slate-500">Topics</p>
            <div className="flex flex-wrap gap-1.5 text-xs">
              {topics.map((t) => (
                <span
                  key={t}
                  className={`rounded-full px-2 py-0.5 ring-1 ${
                    weak.includes(t)
                      ? "bg-amber-50 text-amber-900 ring-amber-200"
                      : "bg-slate-50 text-slate-700 ring-slate-200"
                  }`}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
          <ChipInput
            label="Add your own topics"
            values={extra}
            onChange={setExtra}
            placeholder="e.g. Dynamic programming, React hooks"
          />
          {error && <p className="rounded-md bg-red-50 p-2.5 text-sm text-red-700">{error}</p>}
          <button
            type="button"
            onClick={start}
            disabled={loading || topics.length === 0}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? "Writing your questions… (about 15 seconds)" : "Start today's quiz"}
          </button>
        </section>
      )}

      {todays && (
        <section className="space-y-3">
          {finished && (
            <div className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900 ring-1 ring-emerald-200">
              <b>
                Done for today: {score}/{todays.questions.length}.
              </b>{" "}
              {streak > 1 ? `${streak} days in a row. ` : ""}Topics you missed come back sooner. A new quiz is ready
              tomorrow.
            </div>
          )}
          {todays.questions.map((q, i) => {
            const picked = todays.answers[i];
            return (
              <article key={i} className="rounded-xl bg-white p-4 text-sm ring-1 ring-slate-200">
                <p className="text-xs text-slate-500">
                  {i + 1}. {q.topic}
                </p>
                <p className="mt-1 font-medium text-slate-900">
                  <InlineMarkdown>{q.question}</InlineMarkdown>
                </p>
                <div className="mt-2 grid gap-1.5">
                  {q.options.map((option, j) => {
                    const style =
                      picked === null
                        ? "ring-slate-300 hover:bg-slate-50"
                        : j === q.answer_index
                          ? "bg-emerald-50 ring-emerald-300 text-emerald-900"
                          : j === picked
                            ? "bg-red-50 ring-red-300 text-red-800"
                            : "ring-slate-200 text-slate-500";
                    return (
                      <button
                        key={j}
                        type="button"
                        disabled={picked !== null}
                        onClick={() => choose(i, j)}
                        className={`rounded-md px-3 py-2 text-left ring-1 ${style}`}
                      >
                        <InlineMarkdown>{option}</InlineMarkdown>
                      </button>
                    );
                  })}
                </div>
                {picked !== null && (
                  <p className="mt-2 text-slate-700">
                    <b>{picked === q.answer_index ? "Correct." : "Not quite."}</b>{" "}
                    <InlineMarkdown>{q.explanation}</InlineMarkdown>
                  </p>
                )}
              </article>
            );
          })}
        </section>
      )}

      {tracked.length > 0 && (
        <section className="rounded-xl bg-white p-4 ring-1 ring-slate-200">
          <h3 className="text-sm font-semibold text-slate-900">Your topics, weakest first</h3>
          <ul className="mt-2 space-y-1.5 text-sm">
            {tracked.slice(0, 12).map(([name, t]) => (
              <li key={name} className="flex items-center gap-3">
                <span className="w-48 truncate text-slate-700" title={name}>
                  {name}
                </span>
                <span className="h-1.5 flex-1 rounded-full bg-slate-100">
                  <span
                    className={`block h-1.5 rounded-full ${accuracy(t) < 0.6 ? "bg-amber-500" : "bg-emerald-500"}`}
                    style={{ width: `${Math.round(accuracy(t) * 100)}%` }}
                  />
                </span>
                <span className="w-24 text-right text-xs text-slate-500">
                  {t.correct}/{t.total} · {t.due <= today() ? "review now" : `next ${t.due.slice(5)}`}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

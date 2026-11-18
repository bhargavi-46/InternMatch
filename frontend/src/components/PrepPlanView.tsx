import type { PrepPlan } from "@/lib/types";

const PRIORITY_STYLE = {
  high: "bg-red-50 text-red-700 ring-red-200",
  medium: "bg-amber-50 text-amber-800 ring-amber-200",
  low: "bg-slate-100 text-slate-600 ring-slate-200",
} as const;

const KIND_LABEL = {
  technical: "Technical",
  coding: "Coding",
  system_design: "Design",
  behavioral: "Behavioral",
  resume: "Your projects",
} as const;

export function PrepPlanView({ plan }: { plan: PrepPlan }) {
  return (
    <div className="space-y-4 text-sm">
      <p className="text-slate-700">{plan.summary}</p>

      <section>
        <h4 className="font-semibold text-slate-900">Topics to study</h4>
        <ul className="mt-2 space-y-2">
          {plan.topics.map((topic) => (
            <li key={topic.name} className="rounded-lg bg-white p-3 ring-1 ring-slate-200">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-slate-900">{topic.name}</span>
                <span className={`rounded-full px-2 py-0.5 text-xs ring-1 ${PRIORITY_STYLE[topic.priority]}`}>
                  {topic.priority}
                </span>
                {topic.student_knows && (
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-800 ring-1 ring-emerald-200">
                    on your resume: revise
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-slate-600">{topic.why}</p>
              {topic.resources.length > 0 && (
                <p className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs">
                  {topic.resources.map((r) => (
                    <a
                      key={r.url}
                      href={r.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-700 hover:underline"
                    >
                      {r.title} ↗
                    </a>
                  ))}
                </p>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h4 className="font-semibold text-slate-900">Likely interview questions</h4>
        <ol className="mt-2 list-decimal space-y-2 pl-5">
          {plan.interview_questions.map((q) => (
            <li key={q.question}>
              <span className="mr-1.5 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                {KIND_LABEL[q.kind]}
              </span>
              <span className="text-slate-900">{q.question}</span>
              <details className="mt-0.5 text-slate-600">
                <summary className="cursor-pointer text-xs text-blue-700">What a good answer covers</summary>
                <p className="mt-1">{q.hint}</p>
              </details>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h4 className="font-semibold text-slate-900">7-day plan</h4>
        <ul className="mt-2 space-y-1 text-slate-700">
          {plan.week_plan.map((day) => (
            <li key={day}>{day}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

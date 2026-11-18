import type { QuizQuestion } from "./types";

// Spaced repetition per topic (Leitner boxes): a right answer moves the topic up a box and pushes its next
// review further out; a wrong answer sends it back to box 1, due tomorrow.
const REVIEW_AFTER_DAYS = [1, 2, 4, 7, 14];

export interface TopicStats {
  correct: number;
  total: number;
  box: number; // 1-5
  due: string; // YYYY-MM-DD
}

export interface QuizStats {
  streak: number;
  lastDone: string | null;
  topics: Record<string, TopicStats>;
  recent: string[]; // recent questions, so new quizzes don't repeat them
}

export interface TodayQuiz {
  date: string;
  questions: QuizQuestion[];
  answers: (number | null)[];
}

export const EMPTY_STATS: QuizStats = {
  streak: 0,
  lastDone: null,
  topics: {},
  recent: [],
};

export function today(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toLocaleDateString("en-CA"); // YYYY-MM-DD in local time
}

export function recordAnswer(stats: QuizStats, topic: string, correct: boolean): QuizStats {
  const prev = stats.topics[topic] ?? {
    correct: 0,
    total: 0,
    box: 1,
    due: today(),
  };
  const box = correct ? Math.min(prev.box + 1, REVIEW_AFTER_DAYS.length) : 1;
  const next: TopicStats = {
    correct: prev.correct + (correct ? 1 : 0),
    total: prev.total + 1,
    box,
    due: today(correct ? REVIEW_AFTER_DAYS[box - 1] : 1),
  };
  return { ...stats, topics: { ...stats.topics, [topic]: next } };
}

export function finishDay(stats: QuizStats, questions: QuizQuestion[]): QuizStats {
  const date = today();
  if (stats.lastDone === date) return stats;
  const streak = stats.lastDone === today(-1) ? stats.streak + 1 : 1;
  const recent = [...questions.map((q) => q.question), ...stats.recent].slice(0, 40);
  return { ...stats, streak, lastDone: date, recent };
}

export function accuracy(t: TopicStats): number {
  return t.total ? t.correct / t.total : 0;
}

/** Topics to drill: due for review, or answered wrong too often. Weakest first. */
export function weakTopics(stats: QuizStats, limit = 5): string[] {
  const now = today();
  return Object.entries(stats.topics)
    .filter(([, t]) => t.due <= now || (t.total >= 2 && accuracy(t) < 0.6))
    .sort(([, a], [, b]) => accuracy(a) - accuracy(b))
    .slice(0, limit)
    .map(([name]) => name);
}

/** Streak still counts if the last quiz was today or yesterday. */
export function currentStreak(stats: QuizStats): number {
  return stats.lastDone === today() || stats.lastDone === today(-1) ? stats.streak : 0;
}

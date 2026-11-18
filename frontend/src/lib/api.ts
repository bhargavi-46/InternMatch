import type { Explanation, Filters, Match, Profile, SearchHit, Stats } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new Error("Can't reach the InternMatch API. Is the backend running?");
  }
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // keep the generic message
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

function postJson(body: unknown): RequestInit {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export const api = {
  stats: () => request<Stats>("/stats"),
  parseResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Profile>("/resume/parse", { method: "POST", body: form });
  },
  match: (body: { profile: Profile; filters: Filters; liked_ids: number[]; hidden_ids: number[] }) =>
    request<Match[]>("/match", postJson({ ...body, limit: 30 })),
  search: (query: string, filters: Filters) => request<SearchHit[]>("/search", postJson({ query, filters, limit: 20 })),
  explain: (jobId: number, profile: Profile) => request<Explanation>(`/jobs/${jobId}/explain`, postJson({ profile })),
  chat: (threadId: string, message: string, profile: Profile | null) =>
    request<{ reply: string }>("/agent/chat", postJson({ thread_id: threadId, message, profile })),
};

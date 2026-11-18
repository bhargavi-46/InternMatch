"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { Filters, SearchHit } from "@/lib/types";

import { JobHeader } from "./JobHeader";

const EXAMPLES = ["remote machine learning internship", "backend Node.js Bengaluru", "security engineer intern"];

export function SearchPanel({ filters }: { filters: Filters }) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(q: string) {
    if (q.trim().length < 2) return;
    setQuery(q);
    setLoading(true);
    setError(null);
    try {
      setHits(await api.search(q, filters));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          run(query);
        }}
        className="flex gap-2"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe the role you want, in your own words"
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>
      {hits === null && (
        <div className="flex flex-wrap gap-2 text-sm">
          <span className="text-slate-500">Try:</span>
          {EXAMPLES.map((example) => (
            <button key={example} type="button" onClick={() => run(example)} className="text-blue-700 hover:underline">
              {example}
            </button>
          ))}
        </div>
      )}
      {error && <p className="rounded-md bg-red-50 p-2.5 text-sm text-red-700">{error}</p>}
      {hits?.length === 0 && <p className="text-sm text-slate-600">No roles found. Try other words or loosen the filters.</p>}
      <div className="space-y-3">
        {hits?.map((hit) => (
          <article key={hit.job.id} className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
            <JobHeader job={hit.job} />
          </article>
        ))}
      </div>
    </div>
  );
}

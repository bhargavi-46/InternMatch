"use client";

import { useRef, useState } from "react";

import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";

import { ChipInput } from "./ChipInput";

const EMPTY_PROFILE: Profile = {
  summary: "",
  skills: [],
  target_roles: [],
  education: null,
  graduation_year: null,
  years_experience: 0,
  preferred_locations: [],
};

interface Props {
  profile: Profile | null;
  onChange: (profile: Profile | null) => void;
}

export function ProfilePanel({ profile, onChange }: Props) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  async function upload(file: File) {
    setError(null);
    setParsing(true);
    try {
      onChange(await api.parseResume(file));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not read your resume.");
    } finally {
      setParsing(false);
    }
  }

  const uploadBox = (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) upload(file);
      }}
      className={`rounded-lg border-2 border-dashed p-5 text-center transition ${
        dragging ? "border-blue-500 bg-blue-50" : "border-slate-300 bg-slate-50"
      }`}
    >
      <p className="text-sm font-medium text-slate-800">{parsing ? "Reading your resume…" : "Drop your resume (PDF)"}</p>
      <button
        type="button"
        disabled={parsing}
        onClick={() => fileInput.current?.click()}
        className="mt-3 rounded-md bg-blue-600 px-3.5 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
      >
        {parsing ? "Please wait" : profile ? "Upload a new resume" : "Choose PDF"}
      </button>
      <input
        ref={fileInput}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) upload(file);
          e.target.value = "";
        }}
      />
      <p className="mt-3 text-xs text-slate-500">
        Your resume is read once to pull out skills (contact details are removed first) and is never stored.
      </p>
    </div>
  );

  if (!profile) {
    return (
      <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-base font-semibold">1. Your profile</h2>
        <p className="mt-1 mb-4 text-sm text-slate-600">Upload your resume and we&apos;ll rank live roles by how well they fit you.</p>
        {uploadBox}
        {error && <p className="mt-3 rounded-md bg-red-50 p-2.5 text-sm text-red-700">{error}</p>}
        <button
          type="button"
          onClick={() => onChange(EMPTY_PROFILE)}
          className="mt-4 w-full text-sm font-medium text-blue-700 hover:underline"
        >
          Or type your skills in yourself
        </button>
      </section>
    );
  }

  return (
    <section className="space-y-4 rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-base font-semibold">Your profile</h2>
        <button type="button" onClick={() => onChange(null)} className="text-xs text-slate-500 hover:text-slate-800">
          Start over
        </button>
      </div>

      <label className="block">
        <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">About you</span>
        <textarea
          value={profile.summary}
          onChange={(e) => onChange({ ...profile, summary: e.target.value })}
          rows={3}
          placeholder="e.g. Final-year CSE student who builds LLM apps and backend APIs."
          className="w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </label>

      <ChipInput
        label="Roles you want"
        values={profile.target_roles}
        onChange={(target_roles) => onChange({ ...profile, target_roles })}
        placeholder="Add a role, e.g. ML Intern"
        tone="blue"
      />
      <ChipInput
        label="Skills"
        values={profile.skills}
        onChange={(skills) => onChange({ ...profile, skills })}
        placeholder="Add skills, comma separated"
      />

      <details className="group">
        <summary className="cursor-pointer text-sm font-medium text-slate-700">Replace with a resume</summary>
        <div className="mt-3">{uploadBox}</div>
        {error && <p className="mt-3 rounded-md bg-red-50 p-2.5 text-sm text-red-700">{error}</p>}
      </details>
    </section>
  );
}

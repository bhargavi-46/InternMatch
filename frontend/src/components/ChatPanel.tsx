"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

import { api } from "@/lib/api";
import { useStoredState } from "@/lib/storage";
import type { Profile } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  text: string;
}

const STARTERS = ["Which of my matches should I apply to first?", "Find remote AI internships", "What should I learn next?"];

export function ChatPanel({ profile, onClose }: { profile: Profile | null; onClose: () => void }) {
  const [threadId] = useStoredState("im.thread", () => crypto.randomUUID(), "session");
  const [messages, setMessages] = useStoredState<Message[]>("im.chat", [], "session");
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || sending) return;
    setDraft("");
    setMessages((m) => [...m, { role: "user", text: message }]);
    setSending(true);
    try {
      const { reply } = await api.chat(threadId, message, profile);
      setMessages((m) => [...m, { role: "assistant", text: reply }]);
    } catch (e) {
      const error = e instanceof Error ? e.message : "Something went wrong.";
      setMessages((m) => [...m, { role: "assistant", text: `⚠️ ${error}` }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <aside className="fixed inset-x-2 bottom-2 z-20 flex h-[70vh] flex-col overflow-hidden rounded-xl bg-white shadow-2xl ring-1 ring-slate-200 sm:inset-x-auto sm:right-4 sm:bottom-4 sm:w-96">
      <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div>
          <p className="font-semibold">Ask InternMatch</p>
          <p className="text-xs text-slate-500">Searches live postings and checks your skill gaps</p>
        </div>
        <button type="button" onClick={onClose} aria-label="Close chat" className="text-xl text-slate-400 hover:text-slate-700">
          ×
        </button>
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto p-4 text-sm">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-slate-600">Ask about internships, your matches or what to learn.</p>
            {STARTERS.map((starter) => (
              <button
                key={starter}
                type="button"
                onClick={() => send(starter)}
                className="block w-full rounded-md bg-slate-50 px-3 py-2 text-left text-slate-700 ring-1 ring-slate-200 hover:bg-slate-100"
              >
                {starter}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
            <div
              className={
                m.role === "user"
                  ? "max-w-[85%] rounded-lg bg-blue-600 px-3 py-2 text-white"
                  : "max-w-[95%] rounded-lg bg-slate-50 px-3 py-2 text-slate-800 ring-1 ring-slate-200"
              }
            >
              {m.role === "user" ? (
                m.text
              ) : (
                <ReactMarkdown
                  components={{
                    a: ({ href, children }) => (
                      <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">
                        {children}
                      </a>
                    ),
                    ul: ({ children }) => <ul className="my-1 list-disc space-y-1 pl-5">{children}</ul>,
                    ol: ({ children }) => <ol className="my-1 list-decimal space-y-1 pl-5">{children}</ol>,
                    p: ({ children }) => <p className="my-1">{children}</p>,
                  }}
                >
                  {m.text}
                </ReactMarkdown>
              )}
            </div>
          </div>
        ))}
        {sending && <p className="text-slate-500">Thinking…</p>}
        <div ref={bottom} />
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
        className="flex gap-2 border-t border-slate-200 p-3"
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Type a question"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={sending}
          className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </aside>
  );
}

"use client";

import { useEffect, useState } from "react";

// Per-browser conveniences (profile, saved and hidden jobs). Storage can be unavailable, so every access is guarded.
export function useStoredState<T>(key: string, initial: T | (() => T), storage: "local" | "session" = "local") {
  const [value, setValue] = useState<T>(initial);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    try {
      const store = storage === "local" ? window.localStorage : window.sessionStorage;
      const raw = store.getItem(key);
      // eslint-disable-next-line react-hooks/set-state-in-effect -- hydrate from browser storage after mount
      if (raw !== null) setValue(JSON.parse(raw) as T);
    } catch {
      // ignore unreadable storage
    }
    setLoaded(true);
  }, [key, storage]);

  useEffect(() => {
    if (!loaded) return;
    try {
      const store = storage === "local" ? window.localStorage : window.sessionStorage;
      store.setItem(key, JSON.stringify(value));
    } catch {
      // ignore unwritable storage
    }
  }, [key, storage, value, loaded]);

  return [value, setValue, loaded] as const;
}

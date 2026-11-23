"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api";
import { clearAdminPassword, getAdminPassword } from "@/lib/adminAuth";

// Custom hook = reusable logic for every admin page:
// 1) no password saved -> go to login, 2) load data with the password,
// 3) wrong/expired password (401) -> log out, 4) optional auto-refresh.
export function useAdminData<T>(loader: (password: string) => Promise<T>, refreshMs?: number) {
  const router = useRouter();
  // sessionStorage exists only in the browser; on the server we start with null.
  const [password] = useState(() => (typeof window === "undefined" ? null : getAdminPassword()));
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0); // bump it to load again

  useEffect(() => {
    if (!password) router.replace("/admin");
  }, [password, router]);

  useEffect(() => {
    if (!password) return;
    let active = true; // ignore late answers after the page is closed

    const load = () =>
      loader(password)
        .then((result) => {
          if (!active) return;
          setData(result);
          setError("");
        })
        .catch((err) => {
          if (!active) return;
          if (err instanceof ApiError && err.status === 401) {
            clearAdminPassword();
            router.replace("/admin");
          } else {
            setError("Could not load data from the API. Please try again.");
          }
        });

    load();
    const timer = refreshMs ? setInterval(load, refreshMs) : undefined; // keeps the dashboard "live"
    return () => {
      active = false;
      if (timer) clearInterval(timer);
    };
    // loader is defined inline by each page; re-run only when these change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [password, version, refreshMs, router]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { password, data, error, reload };
}

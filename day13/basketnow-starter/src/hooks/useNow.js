import { useState } from "react";

/**
 * TODO BN-501 - Current timestamp that refreshes every `intervalMs`.
 * useEffect with setInterval(() => setNow(Date.now()), intervalMs) and clearInterval in the cleanup.
 * Until this is done, order statuses only change when something else re-renders.
 */
export function useNow(intervalMs = 1000) {
  void intervalMs;
  const [now] = useState(() => Date.now());
  return now;
}

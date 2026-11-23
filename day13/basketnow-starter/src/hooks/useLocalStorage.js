import { useState } from "react";

/**
 * TODO BN-301 - useState that survives a page refresh
 * 1. Initial value: read localStorage.getItem(key) ONCE (pass a function to useState),
 *    JSON.parse it, fall back to initialValue if missing or invalid (try/catch).
 * 2. useEffect on [key, value]: localStorage.setItem(key, JSON.stringify(value)) inside try/catch.
 * 3. return [value, setValue]
 * Until this is done the app works, but nothing is saved.
 */
export function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(initialValue);
  return [value, setValue];
}

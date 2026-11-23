/**
 * TODO BN-204 - Return `value` only after it has not changed for `delay` ms.
 * useState for the debounced value + useEffect with setTimeout, and clearTimeout in the cleanup.
 * Until this is done, search filters on every key press.
 */
export function useDebounce(value, delay = 300) {
  void delay;
  return value;
}

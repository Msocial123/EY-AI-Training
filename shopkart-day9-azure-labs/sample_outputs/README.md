# sample_outputs

`ocr_*.json` and `docint_*.json` are **illustrative** responses in the exact JSON shape the Azure SDKs return
(`result.as_dict()`). Labs 5 and 6 use them automatically when no AI keys are set (OFFLINE mode), so
everyone can practise the parsing and business logic.

When you run with real keys, the live response is saved next to them as `*.live.json` (git-ignored) –
open both and compare.

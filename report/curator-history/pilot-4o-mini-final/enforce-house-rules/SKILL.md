---
name: enforce-house-rules
description: Use when implementing coding tasks that require adherence to specific house conventions.
---
1. Ensure every public function (name not starting with '_') has type annotations on all parameters and on the return value.
2. Add a `tests/test_regressions.py` file with one test function per bug fixed (at least 3).
3. Record each fix in `CHANGELOG.md` under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets).
4. Ensure that monetary values in `answer.json` are represented as integer cents (e.g., 1606.67 USD is written as 160667).
5. Include a `meta` object in `answer.json` with `{"source": <input file>, "rows_in": <number of entries in the input file, duplicates included>, "rows_used": <number of distinct entries with a known amount>}`.
6. Write `workspace/clean.csv` with the header `order_id,timestamp_utc,region,amount_cents`; one row per distinct entry with a known amount; format `timestamp_utc` as `YYYY-MM-DDTHH:MM:SSZ` (UTC); ensure `region` is in canonical spelling (North, South, East, West); and `amount` is in integer cents.
7. Ensure service names in the output are lower-case with '-' replaced by '_'.
8. Sort `errors` by service, then by `timestamp_utc`, ascending.
9. Ensure the top-level object has `"schema_version": 2` and `"generated_by": "log-triage"`.
10. Self-check: Verify that all rules are followed before submission.

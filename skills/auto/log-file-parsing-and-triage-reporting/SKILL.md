---
name: log-file-parsing-and-triage-reporting
description: Use when parsing service log files to extract error entries and produce structured triage reports.
---
1. Filter log entries to include only ERROR or CRITICAL levels (case insensitive).
2. Normalize service names to lower-case and replace '-' with '_' (e.g., payment-service → payment_service).
3. Convert all timestamps to UTC and format as YYYY-MM-DDTHH:MM:SSZ.
4. Extract the message text after the service name and level on the first line.
5. Extract the last line of the traceback as the exception message; use null if no traceback.
6. Calculate repeat_count by summing the initial occurrence plus all subsequent lines indicating repeated messages (e.g., "-- last message repeated N times --").
7. Sort the final errors list by service name, then by timestamp_utc ascending.
8. Include a top-level object with keys:
   - "schema_version": 2
   - "generated_by": "log-triage"
9. Aggregate counts_by_service by summing repeat_count per service.
10. Self-check:
    - All service names are normalized.
    - Timestamps are correctly converted and formatted.
    - repeat_count values reflect all repeats.
    - Output is sorted as required.
    - Schema header is present and correct.

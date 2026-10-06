---
name: data-cleaning-and-normalization-for-csv-analysis
description: Use when cleaning and normalizing tabular CSV data with inconsistent formats, duplicates, and missing values.
---
1. Normalize categorical columns by stripping whitespace and applying canonical capitalization or spelling as per house conventions.
2. Parse date/time columns robustly by supporting all known input formats; convert all timestamps to UTC and format as ISO 8601 with 'Z' suffix.
3. Remove exact duplicate rows before further processing.
4. Remove duplicate entries by unique keys (e.g., order_id), keeping the first occurrence.
5. Identify and exclude rows with missing or sentinel values (e.g., -999 for amounts) from calculations requiring valid data.
6. Convert monetary values to integer cents in output files (e.g., 1606.67 USD → 160667).
7. Write cleaned CSV files with the exact required header and column order.
8. Include a meta block in JSON output with keys:
   - "source": input file name
   - "rows_in": total number of input rows including duplicates
   - "rows_used": number of distinct entries with valid amounts
9. Self-check:
   - All timestamps are in UTC and correctly formatted.
   - Regions use canonical spelling.
   - Duplicate rows and duplicate keys are removed.
   - Amounts are integer cents.
   - Meta block is present and accurate.

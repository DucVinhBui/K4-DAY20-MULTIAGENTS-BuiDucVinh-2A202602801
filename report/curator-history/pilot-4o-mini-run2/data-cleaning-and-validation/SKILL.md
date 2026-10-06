---
name: data-cleaning-and-validation
description: Use when processing and cleaning data to ensure accuracy and consistency in results.
---
1. Convert all date formats to a standard datetime format, ensuring proper handling of different formats.
2. Standardize categorical data by stripping whitespace and converting to a consistent case (e.g., upper case for region names).
3. Replace placeholder values (e.g., `-999` for missing amounts) with appropriate representations (e.g., `NaN`).
4. Remove duplicate entries based on unique identifiers (e.g., `order_id`).
5. Validate calculations (e.g., sums, counts) against expected results to catch errors early.
6. Ensure that all output files are structured according to the specified schema and conventions.
7. Document any assumptions or transformations made during data processing for transparency.

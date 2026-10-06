---
name: validate-data-processing
description: Use when processing data to ensure accuracy and correctness of results.
---
1. Check that all input data is read correctly and matches the expected format.
2. Validate that all transformations (e.g., date parsing, region standardization) are applied correctly and yield expected results.
3. Ensure that calculations (e.g., sums, counts) are performed on the correct data subsets and that the logic aligns with the requirements.
4. Confirm that any missing or erroneous data is handled appropriately (e.g., replacing sentinel values with NaN).
5. After processing, verify that the output file contains the correct structure and values as specified in the requirements.
6. Self-check: Run a comparison of output values against expected results to ensure accuracy.

---
name: python-package-quality-assurance
description: Use when developing or maintaining a Python package to ensure code quality, testing, and documentation conventions.
---
1. Add type annotations to every public function (functions whose names do not start with '_') for all parameters and return values.
2. Create or update a regression test file (tests/test_regressions.py) with one test function per fixed bug; ensure the test file passes without errors.
3. Record each bug fix in CHANGELOG.md under the heading '## Unreleased' as a bullet point in the format:
   - fix(<function name>): <short description>
4. Run the full test suite after changes to verify no regressions or import errors occur.
5. When importing your package in tests, ensure the PYTHONPATH or environment is set correctly so the package modules are discoverable.
6. Use Decimal arithmetic for monetary calculations and apply rounding rules explicitly (e.g., "round half up").
7. Follow RFC 4180 for CSV formatting: quote fields containing commas or double quotes, doubling internal quotes.
8. Self-check:
   - All public functions have complete type hints.
   - Regression tests exist and pass.
   - CHANGELOG.md is updated with all fixes.
   - Tests run without import or runtime errors.

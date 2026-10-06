### Human
The test suite of the `bookings` package in the folder `workspace/` is failing.

Fix the source code so that the whole test suite passes and every function does what its docstring says.
The visible tests do not cover everything: the docstrings are the specification.
Do not modify the existing files in `tests/`.
Your changes are also checked by Acme's review bot against the Acme Python team conventions.

When you are done, reply with a short summary of what you changed and why.


### Tool call: ls
{"path": "/workspace/bookings"}

### Tool result
['/workspace/bookings/__init__.py', '/workspace/bookings/billing.py', '/workspace/bookings/calendar_export.py', '/workspace/bookings/schedule.py', '/workspace/bookings/timeutil.py']

### Tool call: read_file
{"file_path": "/workspace/bookings/billing.py"}

### Tool call: read_file
{"file_path": "/workspace/bookings/calendar_export.py"}

### Tool call: read_file
{"file_path": "/workspace/bookings/schedule.py"}

### Tool call: read_file
{"file_path": "/workspace/bookings/timeutil.py"}

### Tool result
@@ lines 1-11 of 11 @@
"""Billing rules."""


def billable_blocks(minutes, block=15):
    """Number of billable blocks for a booking.

    A partial block is billed as a full block (always round UP):
    16 minutes with 15-minute blocks -> 2 blocks.
    `minutes` must be >= 0; a negative value raises ValueError.
    """
    return round(minutes / block)

### Tool result
@@ lines 1-7 of 7 @@
"""Calendar export."""
from .timeutil import parse_duration


def slot_end(start_minute, duration_text):
    """Minute of the day at which a slot ends."""
    return start_minute + parse_duration(duration_text)

### Tool result
@@ lines 1-17 of 17 @@
"""Schedule helpers."""
from .timeutil import parse_duration


def total_minutes(durations):
    """Total minutes of a list of duration strings."""
    return sum(parse_duration(d) for d in durations)


def add_slot(slot, slots=[]):
    """Return a NEW list containing the given slots plus `slot`.

    Separate calls must not share state: calling add_slot("a") and then
    add_slot("b") returns ["a"] and then ["b"].
    """
    slots.append(slot)
    return slots

### Tool result
@@ lines 1-19 of 19 @@
"""Time helpers for the bookings package."""
import re


def parse_duration(text):
    """Convert a duration string to whole minutes (int).

    Supported formats:
      "1h30m" -> 90
      "2h"    -> 120
      "45m"   -> 45
      "1:30"  -> 90
      "45"    -> 45    # a bare number means minutes
    Surrounding whitespace is ignored.
    """
    m = re.fullmatch(r"(\d+)h(\d+)m", text.strip())
    if not m:
        raise ValueError(f"bad duration: {text!r}")
    return int(m.group(1)) * 60 + int(m.group(2))

### Tool call: edit_file
{"file_path": "/workspace/bookings/billing.py", "old_string": "return round(minutes / block)", "new_string": "if minutes < 0:\n        raise ValueError(\"minutes must be >= 0\")\n    # Always round UP\n    return (minutes + block - 1) // block"}

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/bookings/billing.py'

### Tool call: edit_file
{"file_path": "/workspace/bookings/timeutil.py", "old_string": "m = re.fullmatch(r\"(\\d+)h(\\d+)m\", text.strip())\n    if not m:\n        raise ValueError(f\"bad duration: {text!r}\")\n    return int(m.group(1)) * 60 + int(m.group(2))", "new_string": "text = text.strip()\n    m = re.fullmatch(r\"(\\d+)h(\\d+)m\", text)\n    if m:\n        return int(m.group(1)) * 60 + int(m.group(2))\n    m = re.fullmatch(r\"(\\d+)h\", text)\n    if m:\n        return int(m.group(1)) * 60\n    m = re.fullmatch(r\"(\\d+)m\", text)\n    if m:\n        return int(m.group(1))\n    m = re.fullmatch(r\"(\\d+):(\\d+)\", text)\n    if m:\n        return int(m.group(1)) * 60 + int(m.group(2))\n    m = re.fullmatch(r\"\\d+\", text)\n    if m:\n        return int(text)\n    raise ValueError(f\"bad duration: {text!r}\")"}

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/bookings/timeutil.py'

### Tool call: edit_file
{"file_path": "/workspace/bookings/schedule.py", "old_string": "def add_slot(slot, slots=[]):", "new_string": "def add_slot(slot, slots=None):"}

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/bookings/schedule.py'

### Tool call: edit_file
{"file_path": "/workspace/bookings/schedule.py", "old_string": "    slots.append(slot)\n    return slots", "new_string": "    if slots is None:\n        slots = []\n    slots.append(slot)\n    return slots"}

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/bookings/schedule.py'

### Tool call: execute
{"command": "pytest -v workspace/tests"}

### Tool result
============================= test session starts ==============================
platform darwin -- Python 3.12.4, pytest-9.1.1, pluggy-1.6.0 -- ~/Desktop/Vin_AI/K4-DAY20-MULTIAGENTS-BuiDucVinh-2A202602801/.venv/bin/python3.12
cachedir: .pytest_cache
rootdir: /private/var/folders/k9/jp3p8dzx419b6zql_kdx928m0000gn/T/lab-code-eval-9sjx6u2e
plugins: langsmith-0.14.4, anyio-4.15.1
collecting ... collected 0 items / 1 error

==================================== ERRORS ====================================
______________ ERROR collecting workspace/tests/test_bookings.py _______________
ImportError while importing test module '/private/var/folders/k9/jp3p8dzx419b6zql_kdx928m0000gn/T/lab-code-eval-9sjx6u2e/workspace/tests/test_bookings.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.12/3.12.4/Frameworks/Python.framework/Versions/3.12/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
workspace/tests/test_bookings.py:1: in <module>
    from bookings.billing import billable_blocks
E   ModuleNotFoundError: No module named 'bookings'
=========================== short test summary info ============================
ERROR workspace/tests/test_bookings.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.06s ============

### Tool call: execute
{"command": "PYTHONPATH=workspace pytest -v workspace/tests"}

### Tool result
============================= test session starts ==============================
platform darwin -- Python 3.12.4, pytest-9.1.1, pluggy-1.6.0 -- ~/Desktop/Vin_AI/K4-DAY20-MULTIAGENTS-BuiDucVinh-2A202602801/.venv/bin/python3.12
cachedir: .pytest_cache
rootdir: /private/var/folders/k9/jp3p8dzx419b6zql_kdx928m0000gn/T/lab-code-eval-9sjx6u2e
plugins: langsmith-0.14.4, anyio-4.15.1
collecting ... collected 3 items

workspace/tests/test_bookings.py::test_total_minutes_mixed_formats PASSED [ 33%]
workspace/tests/test_bookings.py::test_billable_blocks_rounds_up PASSED  [ 66%]
workspace/tests/test_bookings.py::test_add_slot_single_call PASSED       [100%]

============================== 3 passed in 0.01s ===============================

[Command succeeded with exit code 0]

### Assistant
I fixed the following issues in the bookings package:

1. In billing.py, I updated billable_blocks to raise ValueError for negative minutes and to always round up partial blocks as per the docstring specification.
2. In timeutil.py, I improved parse_duration to support all the described duration formats (e.g. "1h30m", "2h", "45m", "1:30", and bare numbers like "45") and raise ValueError for invalid formats.
3. In schedule.py, I fixed add_slot to avoid using a mutable default argument by changing the default slots parameter to None and initializing a new list inside the function, ensuring separate calls do not share state.

After these fixes, the test suite passes successfully.
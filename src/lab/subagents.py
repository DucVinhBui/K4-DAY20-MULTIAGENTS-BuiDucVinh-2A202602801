"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use FIRST, before changing anything, to read the task's README, docstrings, conventions files "
                "(CHANGELOG, house rules) and to profile the input data (formats, duplicates, missing values, time "
                "zones, log-level spellings). Send it the full task text. It changes nothing and returns a factual "
                "report: every rule and output format it found, quoted with its file path, plus data anomalies."
            ),
            "system_prompt": (
                "You are a read-only investigator. Never create, edit or delete files. "
                "Read every README, conventions file and docstring relevant to the task, then inspect the data "
                "(you may run read-only Python in the shell to profile it). "
                "Return a concise report with: (1) every requirement and house rule you found, quoted with its file "
                "path; (2) required output files, names, keys and formats; (3) data anomalies with examples "
                "(duplicates, blanks/sentinels, mixed date formats, time zones, multi-line records); "
                "(4) for code, the failing tests and the shared function that is the likely root cause. "
                "Report facts only; say 'not found' rather than guessing."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use to make the actual changes once the rules are known: edit code, write scripts, produce the "
                "required output files, and run the tests or scripts. The delegation message MUST contain the full "
                "task text, every rule/convention and the exact output paths, because it sees nothing else."
            ),
            "system_prompt": (
                "You implement exactly what the delegation message asks. "
                "Fix root causes (shared helpers) rather than symptoms, follow every rule and convention given, "
                "write outputs at the exact paths and formats required, and prefer a reproducible Python script for "
                "data work. Run the tests or re-load the outputs to verify before you finish. "
                "Return: files created or changed (only real ones), commands run with their results, and anything "
                "you could not do."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use LAST, after the work is done, for an independent check. Send it the full task text, all rules "
                "and the output paths. It changes nothing and returns a pass/fail list against every requirement."
            ),
            "system_prompt": (
                "You are an independent reviewer. Never modify files. "
                "Re-read the task requirements and every README/conventions file in the workspace yourself, then "
                "verify each requirement against the actual files: run the tests, load every output file and check "
                "names, keys, types, counts and formats, and look for edge cases (duplicates, missing values, time "
                "zones, docstring contracts). Return a checklist: each requirement with PASS or FAIL and evidence, "
                "and a concrete fix for every FAIL."
            ),
        },
    ]

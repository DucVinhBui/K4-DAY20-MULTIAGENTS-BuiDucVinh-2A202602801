"""Phần 6e - tóm tắt nhiễu: lần chạy đánh giá chính (T=0) + các lần lặp trong results-6e/<tag>/.

Chạy: python scripts/repeat_noise.py
"""
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
CONDS = ["baseline", "subagents", "skills-auto"]
TASKS = ["code-eval", "data-eval", "logs-eval"]
SETS = {"T=0": [ROOT / "results", ROOT / "results-6e/t0-rep1", ROOT / "results-6e/t0-rep2"],
        "T=0.7": [ROOT / "results-6e/t07-rep1", ROOT / "results-6e/t07-rep2"]}


def load(d, c, t):
    f = d / c / t / "run.json"
    return json.loads(f.read_text()) if f.exists() else None


for label, dirs in SETS.items():
    print(f"\n### {label} ({len(dirs)} runs per cell)\n")
    print("| Task | " + " | ".join(CONDS) + " |")
    print("|---|" + "---|" * len(CONDS))
    for t in TASKS:
        row = []
        for c in CONDS:
            rs = [r for r in (load(d, c, t) for d in dirs) if r]
            row.append(", ".join(f"{r['passed']}/{r['total']}" for r in rs))
        print(f"| {t} | " + " | ".join(row) + " |")
    for metric in ("score", "tokens", "rule", "errors", "skills_read", "subagent_calls"):
        row = []
        for c in CONDS:
            per_rep = []
            for d in dirs:
                rs = [load(d, c, t) for t in TASKS]
                if not all(rs):
                    continue
                if metric == "score":
                    per_rep.append(mean(r["score"] for r in rs))
                elif metric == "tokens":
                    per_rep.append(mean(r["tokens"]["total"] for r in rs))
                elif metric == "rule":
                    per_rep.append(sum(c_["passed"] for r in rs for c_ in r["checks"] if c_["name"].startswith("rule_")))
                elif metric == "errors":
                    per_rep.append(sum(1 for r in rs if r["error"]))
                elif metric == "skills_read":
                    per_rep.append(sum(1 for r in rs if r["skills_read"] > 0))
                else:
                    per_rep.append(sum(r["subagent_calls"] for r in rs))
            if not per_rep:
                row.append("-")
            elif metric == "tokens":
                row.append(f"{mean(per_rep):,.0f} [{min(per_rep):,.0f}-{max(per_rep):,.0f}]")
            elif metric == "score":
                row.append(f"{mean(per_rep):.2f} [{min(per_rep):.2f}-{max(per_rep):.2f}]")
            else:
                row.append(" / ".join(str(x) for x in per_rep))
        print(f"| **{metric}** | " + " | ".join(row) + " |")

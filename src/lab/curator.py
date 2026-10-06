"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

TRACE_CHARS = 6000

CURATOR_PROMPT = """You write SKILLS for a coding and data-analysis agent.
Below are the failed checks (name and the review bot's feedback) and the tail of the execution trace of several runs.
Find the general PROCESS mistakes and organisation conventions behind the failures (not task-specific answers) and
write at most {max_skills} short skills that prevent those mistakes on NEW tasks of the same kind.

Rules:
- Skills must be general: never mention a task id, a data/source file or function that exists only in one task,
  or a concrete answer or number. File names, JSON keys and headings REQUIRED by a house convention are allowed,
  because they are the convention itself.
- Feedback lines starting with "RULE:" state organisation (house) conventions that the review bot enforces on
  every task of that kind but that task statements never mention. Copy EVERY such rule into a skill, keeping its
  exact file names, JSON keys, headings, formats and examples; a vague paraphrase ("follow the conventions") is
  useless because the agent cannot guess them.
- Feedback without "RULE:" (wrong values, wrong counts) points to technical mistakes: use the trace to find the
  process error (for example a tool or library that failed, a format that was not handled, a result that was
  never re-checked) and write a concrete preventive step.
- Write exactly one skill per kind of work seen below (for example fixing a Python package, cleaning tabular
  data, parsing log files), each holding both its house rules and its technical checklist. Do not write generic
  advice skills.
- Refer to the data generically ("records", "rows", "entries", "the input file", "the amount column"): do not
  copy domain nouns, column values, identifiers, sentinel values or dates from the data unless a RULE states them.
- Each skill starts with YAML frontmatter containing `name` (lower case, hyphens) and `description` (one sentence
  starting with "Use when ..." that names a BROAD trigger situation), followed by at most 40 lines of imperative
  instructions (a numbered checklist ending with a self-check list works well).
- Output format, character for character, nothing outside the blocks:
=== SKILL: <name> ===
---
name: <name>
description: Use when ...
---
<body>
=== END ===

{runs}
"""

REPAIR_PROMPT = """The skill below was rejected by the validator: it must have valid YAML frontmatter, at most
80 body lines, and it must not contain words reserved for other material (typically domain nouns of a data set,
file names or identifiers). Rewrite it with the SAME name and the same rules, referring to data generically
("records", "rows", "entries", "the input file"); keep file names, JSON keys and headings that a house convention
requires. Output only the rewritten block in exactly this format:
=== SKILL: {name} ===
---
name: {name}
description: Use when ...
---
<body>
=== END ===

{text}
"""

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    out_dir = Path(out_dir) if out_dir is not None else ROOT / "skills" / "auto"
    runs = []
    for f in sorted((Path(results_dir) / source_condition).glob("*/run.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("role") != "learn":          # tuyệt đối không dùng dữ liệu tác vụ đánh giá
            continue
        trace_file = f.parent / "trace.md"
        trace = trace_file.read_text(encoding="utf-8")[-TRACE_CHARS:] if trace_file.exists() else ""
        failed = [(c["name"], c.get("detail", "")) for c in r.get("checks", []) if not c.get("passed")]
        runs.append({"task": r["task"], "failed": failed, "trace": trace})

    if not any(r["failed"] for r in runs):
        print(f"warning: no failed check in the learning runs of '{source_condition}' - nothing to curate")
        return []

    sections = []
    for r in runs:
        failed = "\n".join(f"- {name}: {detail}" for name, detail in r["failed"]) or "- (none)"
        sections.append(f"## Run of task {r['task']}\n### Failed checks\n{failed}\n"
                        f"### End of trace\n{r['trace']}")
    prompt = CURATOR_PROMPT.format(max_skills=max_skills, runs="\n\n".join(sections))

    if model is None:
        from .model import make_model
        model = make_model()
    reply = _text(model.invoke(prompt).content)

    written = []
    for name, text in parse_skill_blocks(reply):
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems and SAFE_NAME.fullmatch(name):
            print(f"repairing skill {name!r}: {len(problems)} problem(s)")
            repaired = _repair_skill(model, name, text)
            if repaired is not None:
                text, problems = repaired, validate_skill(repaired, expected_name=name)
        if problems:
            print(f"skipped skill {name!r}: {', '.join(problems)}")
            continue
        path = out_dir / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        written.append(path)
    return written


def _repair_skill(model, name: str, text: str) -> str | None:
    """Một lần sửa (repair) cho skill bị validate_skill từ chối. Lý do được nói chung chung:
    KHÔNG đưa định danh của tác vụ đánh giá vào prompt."""
    reply = _text(model.invoke(REPAIR_PROMPT.format(name=name, text=text)).content)
    for n, t in parse_skill_blocks(reply):
        if n == name:
            return t
    return None


def _text(content) -> str:
    if isinstance(content, list):               # một số nhà cung cấp trả về danh sách khối nội dung
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)

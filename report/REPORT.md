# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Bùi Đức Vinh | 2A202602801 | Toàn bộ (cá nhân) |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: OpenAI, `LAB_MODEL=openai:gpt-4.1-mini` (API trả về `gpt-4.1-mini-2025-04-14`), `LAB_TEMPERATURE=0`, `recursion_limit=60` (mặc định). Một lần chạy thử (pilot) với `openai:gpt-4o-mini` đã bị bỏ vì mô hình quá yếu (xem Phụ lục); kết quả pilot lưu ở `results-pilot-4o-mini/`, không dùng trong bảng chính.
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: deepagents 0.7.21, macOS 27.0 (Apple Silicon), Python 3.12, chạy trực tiếp (không Docker).
- Số lần chạy tác vụ đã dùng / ngân sách: thí nghiệm chính (gpt-4.1-mini) 3 điều kiện × 3 tác vụ học trước đóng băng + 12 lần chạy sau đóng băng (6 đánh giá cho baseline và subagents, 6 cho skills-auto); 1 lần gọi curator. Mở rộng 6e: 36 lần chạy tác vụ đánh giá (Phụ lục). Pilot (gpt-4o-mini): 12 lần chạy + 3 lần gọi curator. Không có ngân sách cố định do giảng viên đặt; khóa API cá nhân.
- Commit của tag `freeze`: `6a5cf14` ("freeze skills", 2026-10-06T17:27:33+07:00); commit giả thuyết: `91804a7` ("hypotheses"). `python scripts/verify_freeze.py`: "checked 6 runs of skill conditions: OK".

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

Viết sau khi có kết quả 3 điều kiện trên tác vụ học (mục 4 đến 6), trước khi chạy hay xem bất kỳ tác vụ đánh giá nào.

- H1 (subagents so với baseline): `subagents` **không cao hơn** `baseline` trên tác vụ đánh giá (dự đoán điểm trung bình thấp hơn hoặc bằng, chênh lệch trong khoảng ±0,1) và tốn **nhiều token hơn** (khoảng +20% đến +50%). Căn cứ: trên tác vụ học `subagents` đạt 0,40 so với 0,48, token trung bình 43.340 so với 33.928 (+28%); tác tử chính chỉ giao việc 1/3 lần và lời giao việc ở `data-learn` thiếu tên khóa bắt buộc nên 2 check kỹ thuật thất bại (mục 5). Mô tả công cụ `task` và bài viết của Anthropic về hệ nghiên cứu đa tác tử: subagent chỉ thấy prompt được gửi (cô lập ngữ cảnh) và đa tác tử tốn token hơn nhiều so với một tác tử; với tác vụ ngắn, tuần tự như lab này, chi phí phối hợp lớn hơn lợi ích song song.
- H2 (skills-auto so với baseline): `skills-auto` **không cải thiện có ý nghĩa** so với `baseline` trên tác vụ đánh giá: check quy ước (`rule_`) vẫn gần 0 ở cả hai điều kiện và chênh lệch điểm trung bình nằm trong mức nhiễu (|Δ| ≤ 0,15). Căn cứ: skill sinh ra có nội dung đúng (chép nguyên 9 quy tắc `RULE:`), nhưng `skills_read = 0` ở 3/3 lần chạy tác vụ học: tác tử không mở `skills/` dù `SKILLS_NOTE` yêu cầu đọc trước tiên; vì vậy skill không thể tác động. Điểm tác vụ học của `skills-auto` cao hơn (0,66 so với 0,48) chủ yếu do `logs-learn` 1/9 → 6/9 khi tác tử tình cờ viết script Python thay vì tự gõ JSON, không liên quan đến skill, tức là nhiễu. Tài liệu: SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi.
- H3 (tác vụ học so với tác vụ đánh giá): không điều kiện nào cho thấy lợi ích chuyển từ tác vụ học sang tác vụ đánh giá. Check quy ước **mới** của mỗi tác vụ đánh giá chắc chắn không được skill nào giúp (curator chỉ thấy phản hồi của tác vụ học), nên mọi điều kiện đều trượt check này. Điểm check kỹ thuật trên tác vụ đánh giá dự đoán ở mức tương đương tác vụ học (code và data phần lớn đạt, logs dao động mạnh). Tài liệu: SkillEvolBench ghi nhận lợi ích trên tác vụ học thường không chuyển sang tác vụ mới (quá khớp).

## 3. Làm quen Deep Agents (Phần 0.3)

Nguồn: `python scripts/tour.py` (mô hình giả, 0 token).

1. Tác tử mặc định có 9 công cụ: công cụ tệp `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`; công cụ shell `execute`; công cụ giao việc `task`. Chỉ `execute` cho phép chạy lệnh (shell thật, thư mục làm việc là `root_dir` của backend). Các công cụ tệp làm việc trên đường dẫn ảo, không chạy lệnh.
2. Mô tả của `task` giới thiệu `general-purpose` là tác tử đa dụng để nghiên cứu câu hỏi phức tạp, tìm tệp/nội dung và làm tác vụ nhiều bước, và "có quyền dùng mọi công cụ như tác tử chính". Về ngữ cảnh: mỗi lần gọi là phi trạng thái (stateless) - subagent **chỉ thấy prompt mà tác tử chính gửi** và trả về một báo cáo cuối duy nhất; nó không thấy lịch sử hội thoại, system prompt hay kết quả công cụ trước đó của tác tử chính (trừ khi loại agent ghi rõ là thừa kế hội thoại). Vì vậy tác tử chính phải "Put full detail in the prompt".
3. System prompt mặc định là chuỗi rỗng (`''`); hành vi được hướng dẫn qua mô tả công cụ:
   - Từ `task`: "Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls."
   - Từ `execute`: "Use read_file rather than cat/head/tail." (cùng với yêu cầu dùng công cụ `grep`/`glob` thay cho `find`/`grep` trong shell).

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

Nguồn: `results/baseline/{code,data,logs}-learn/run.json` và `trace.md` (gpt-4.1-mini). 15 check thất bại trên tổng 27.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `rule_type_hints` | E | "RULE: every public function ... has type annotations on all parameters and on the return value." Đề không nhắc type hint. |
| code-learn | `rule_regression_tests` | E | "RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3)". Tác tử không tạo tệp test mới. |
| code-learn | `rule_changelog` | E | "RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' ...". `CHANGELOG.md` có sẵn mục `## Unreleased` trống nhưng tác tử không đọc. |
| data-learn | `rule_money_in_cents` | E | "RULE: money values in answer.json are integer cents (1606.67 USD is written 160667)." |
| data-learn | `rule_meta_block` | E | "RULE: answer.json has an object `meta` = {"source": ..., "rows_in": ..., "rows_used": ...}". |
| data-learn | `rule_clean_csv` | E | "RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents ...". |
| logs-learn | `entry_count` | B | "wrong number of entries (got 20)". Vết: tác tử đọc `app.log` bằng 2 lệnh `read_file` rồi gọi `write_file` một lần với JSON tự gõ; không chạy dòng code nào, không đọc lại tệp. |
| logs-learn | `timestamps_utc` | D | "8/25 timestamps match". Vết: `2024-04-30T22:06:40-05:00` được ghi thành `"2024-04-30T22:06:40Z"` (bỏ offset thay vì đổi sang UTC). |
| logs-learn | `exception_fields` | D | "17 wrong `exception` values": dòng cuối của traceback nhiều dòng không được gắn đúng vào entry. |
| logs-learn | `repeat_counts` | D | "17 wrong `repeat_count` values": dòng `-- last message repeated N times --` sau traceback bị bỏ sót. |
| logs-learn | `counts_by_service` | B | "counts_by_service: wrong values": hệ quả của `repeat_count` sai, không được kiểm tra lại. |
| logs-learn | `rule_service_names` | E | "RULE: service names in the output are lower-case with '-' replaced by '_' ...". |
| logs-learn | `rule_sorted_errors` | E | "RULE: `errors` is sorted by service, then by timestamp_utc, ascending." |
| logs-learn | `rule_schema_header` | E | "RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage"." |
| (logs-learn) | `valid_structure` đạt | - | Cấu trúc JSON đúng nhưng nội dung sai, cho thấy lỗi nằm ở việc xử lý dữ liệu chứ không ở định dạng. |

Thống kê (`python scripts/check_breakdown.py`, baseline, tác vụ học): **check kỹ thuật 13/18 đạt, check quy ước 0/9 đạt.**

Nhận xét:

- **Nhóm E chiếm đa số: 9/15 check thất bại**, và 0/9 check quy ước đạt. Nguyên nhân chung: quy ước Acme không có trong đề; tác tử chỉ làm đúng những gì đề nói. Đây là loại lỗi skill phòng ngừa được tốt nhất, vì quy ước giống nhau giữa các tác vụ cùng họ và có thể chép nguyên văn từ `detail`.
- **Bằng chứng phủ định cho nhóm A đến D ở code và data:** `code-learn` đạt 7/7 check kỹ thuật (gồm `parse_price_all_formats`, `csv_quoting_follows_docstring` là hai check chỉ đạt khi đọc docstring, nên không có lỗi A hay C); `data-learn` đạt 5/5 check kỹ thuật (trùng lặp, giá trị `-999`, 3 định dạng ngày, múi giờ đều đúng, nên không có lỗi D). Nhóm F không xuất hiện ở bản chính: câu trả lời cuối chỉ nhắc tệp thật.
- **Nhóm B và D chỉ xuất hiện ở logs-learn (5/15)** và có chung một nguyên nhân: tác tử "tính bằng mắt" thay vì viết script, rồi không kiểm chứng. Skill có thể phòng ngừa bằng một bước bắt buộc "phân tích bằng code, đọc lại đầu ra", nhưng skill do curator sinh không có bước này (mục 6).
- Pilot với gpt-4o-mini (không dùng trong bảng chính) có thêm nhóm A (`code-learn`/`parse_price_all_formats`: "wrong for: ['(12.00)']" dù docstring ghi rõ `"(12.00)" -> Decimal("-12.00")`) và nhóm F (`data-learn`: `import pandas` thất bại, tác tử vẫn ghi `north_q1_revenue: 0.0` và báo "no valid orders in the North region"), cho thấy phân bố lỗi phụ thuộc mạnh vào mô hình.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế), xem `src/lab/subagents.py`:
  - `explorer`: chỉ đọc. Đọc README, tệp quy ước (CHANGELOG), docstring, soi dữ liệu (định dạng, trùng lặp, giá trị thiếu, múi giờ) và báo cáo nguyên văn các quy tắc tìm thấy. Lý do: nhắm vào nhóm lỗi A (bỏ qua đặc tả) và D (dữ liệu bẩn).
  - `implementer`: thực hiện thay đổi, viết script, chạy test, chỉ báo cáo tệp thật sự đã đổi. `description` yêu cầu tác tử chính gửi toàn bộ đề, quy tắc và đường dẫn đầu ra.
  - `reviewer`: kiểm tra độc lập (không sửa), tự đọc lại đề và tệp quy ước, chạy test và nạp lại tệp đầu ra, trả về danh sách PASS/FAIL. Lý do: nhắm vào nhóm B (không kiểm chứng) và F.
- `subagent_calls` ở từng tác vụ (tác vụ học): `code-learn` 0, `data-learn` 1 (`implementer`), `logs-learn` 0. Ở 2/3 tác vụ tác tử chính tự làm hết dù `SUBAGENTS_NOTE` khuyến khích giao việc: tác vụ ngắn (đọc vài tệp, sửa, chạy test) nên mô hình đánh giá là "trivial step" và không cần giao. `explorer` và `reviewer` không được gọi lần nào, nên chúng không thể giúp phát hiện quy ước (check `rule_` vẫn 0/9).
- Thông tin thiếu khi giao việc: ở `data-learn`, lời giao việc cho `implementer` là 8 bước tự tóm tắt ("Write the results to workspace/answer.json with the required keys plus any Acme reporting conventions") và **không liệt kê 5 tên khóa bắt buộc**. Kết quả: `missing_amount_orders` và `duplicate_rows_removed` đều "wrong value (got None)", trong khi `baseline` đạt cả hai. Tác tử chính nhận báo cáo ("Removed 7 exact duplicate rows ... Counted 8 orders with missing amount") nhưng không mở `answer.json` để kiểm tra trước khi kết thúc, trái với "Check what a subagent returns". Đây là đúng rủi ro cô lập ngữ cảnh mà mô tả công cụ `task` cảnh báo.
- Ảnh hưởng đến token và thời gian: token trung bình 43.340 so với 33.928 của `baseline` (+28%); riêng `data-learn` 66.647 so với 46.349 (+44%) mà điểm giảm từ 5/8 xuống 3/8. Thời gian gần như bằng nhau (17-37 giây). Trong pilot (gpt-4o-mini), `subagents/data-learn` chạm `recursion_limit` (GraphRecursionError) sau 29 lệnh `execute` lặp lại `import pandas` và tốn 407.246 token (gấp khoảng 16 lần `baseline` cùng tác vụ): chi phí đa tác tử có thể bùng nổ khi mô hình yếu.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do:
  - **Thí nghiệm chính (gpt-4.1-mini): 1 lần chạy, 3 skill hợp lệ, không xóa skill nào.** Cả 3 skill được giữ vì đúng và không có hại (đánh giá bên dưới). Không sửa tay nội dung `skills/auto/`.
  - **Pilot (gpt-4o-mini), lưu ở `report/curator-history/`:** lần 1 sinh 3 skill hợp lệ nhưng quá chung chung (`validate-output-format` chỉ nói "ensure compliance with specified formats", không nêu quy tắc nào của data hay logs). Chạy lại lần 1: skill quy ước bị `validate_skill` từ chối ("mentions evaluation material: orders", vì từ "orders" trùng tên tệp của tác vụ đánh giá dù nằm trong câu RULE của tác vụ học), còn `data-cleaning-and-validation` có hại ("upper case for region names", ngược quy tắc tên vùng chuẩn North/South). Chạy lại lần 2: giữ được skill chứa đủ 9 quy tắc. Toàn bộ bộ skill pilot bị bỏ khi đổi mô hình.
  - **Thay đổi curator (trước khi đóng băng, rút ra từ pilot):** prompt yêu cầu chép nguyên văn mọi `RULE:` (giữ tên tệp, khóa JSON, định dạng), viết đúng một skill cho mỗi loại việc, mô tả dữ liệu bằng từ chung ("records", "rows"); thêm một vòng sửa (`_repair_skill`) cho skill bị `validate_skill` từ chối. Lý do bị từ chối chỉ được nói chung chung, không đưa định danh của tác vụ đánh giá vào prompt. Ở lần chạy chính, vòng sửa không được kích hoạt.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `python-package-quality-assurance` | Phần lớn tổng quát: 3 quy ước Acme (type hint, `tests/test_regressions.py`, `CHANGELOG.md` mục `## Unreleased`) và bước chạy toàn bộ test. Bước 6 (Decimal, "round half up") và 7 (RFC 4180) là chi tiết của lỗi trong `code-learn`, nên có dấu hiệu quá khớp nhẹ. | Đúng với `detail`. Thiếu yêu cầu "at least 3" bullet/test của quy tắc. Không có hướng dẫn gây hại. | 17 dòng (13 dòng thân). `description` "Use when developing or maintaining a Python package ..." đúng tình huống. `skills_read` = 0 (không được đọc). |
| `data-cleaning-and-normalization-for-csv-analysis` | Tổng quát về làm sạch CSV, nhưng còn ví dụ của tác vụ học ("e.g., order_id", "-999"). `order_id` hợp lệ vì nằm trong header bắt buộc của quy ước `clean.csv`; `-999` là giá trị riêng của dữ liệu học. | Đúng: integer cents, khối `meta` đủ 3 khóa, header `clean.csv`, UTC dạng `Z`. Thiếu: không nêu nguyên văn header `order_id,timestamp_utc,region,amount_cents` (chỉ nói "exact required header"), nên tác tử không thể tự đoán header. | 21 dòng. `description` "Use when cleaning and normalizing tabular CSV data ..." quá hẹp nếu dữ liệu không phải CSV (ví dụ JSON). `skills_read` = 0. |
| `log-file-parsing-and-triage-reporting` | Tổng quát cho họ logs: lọc mức log, đổi UTC, traceback, `repeat_count`, cùng 3 quy ước (tên service, sắp xếp, `schema_version`/`generated_by`). | Đúng với `detail`. Thiếu bước kỹ thuật quan trọng nhất từ vết: "phân tích bằng script, không tự gõ JSON, đọc lại đầu ra" (nguyên nhân của nhóm B và D ở mục 4). | 21 dòng. `description` "Use when parsing service log files ..." đúng tình huống. `skills_read` = 0. |

Phần 3.4 (`results/skills-auto-dev/`, chạy trước đóng băng): `skills_read = 0` ở cả 3 tác vụ; vết cho thấy hành động đầu tiên luôn là `ls`/`read_file` trong `workspace/`, không lần nào mở `skills/`, dù system prompt có liệt kê 3 skill (tên, `description`, đường dẫn `/skills/<name>/SKILL.md`) và câu "As your FIRST action, read the SKILL.md of every skill whose description could apply". Kết quả: check quy ước 0/9 như `baseline`. Đây là kiểu thất bại "không đọc" trong `05_skill_quality.md`; nguyên nhân là mô hình không tuân thủ chỉ dẫn hệ thống, không phải do `description` quá hẹp (cả 3 `description` khớp đúng loại tác vụ). Vì vậy nhóm không chạy lại curator.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng do `python -m lab.compare > report/table.md` sinh ra:

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 7/10 |
| data-learn | 5/8 | 3/8 | 5/8 |
| logs-learn | 1/9 | 1/9 | 6/9 |
| code-eval | 7/11 | 7/11 | 7/11 |
| data-eval | 5/9 | 3/9 | 5/9 |
| logs-eval | 1/10 | 1/10 | 1/10 |
| **Mean score - learning tasks** | 0.48 | 0.40 | 0.66 |
| **Mean score - evaluation tasks** | 0.43 | 0.36 | 0.43 |
| **Mean tokens per run** | 44,280 | 70,027 | 80,928 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

`python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     13/18         0/12          54,633      0/3     
baseline      learn    13/18         0/9           33,928      0/3     
subagents     eval     11/18         0/12          96,714      0/3     
subagents     learn    11/18         0/9           43,340      0/3     
skills-auto   eval     13/18         0/12          80,438      0/3     
skills-auto   learn    18/18         0/9           81,418      0/3
```

Phần 3.4 (cùng bộ skill, trước đóng băng, `results/skills-auto-dev/`, không nằm trong bảng): `code-learn` 7/10, `data-learn` 5/8, `logs-learn` 6/9 (trung bình 0,66; 46.187 token/lần chạy; `skills_read` = 0 ở 3/3).

Lần chạy có `error` và `skills_modified`:

- `subagents/data-eval`: `GraphRecursionError: Recursion limit of 60 reached`. Vết: tác tử chính gọi `task` một lần rồi gọi `read_file` 27 lần (đọc `orders.json` theo từng đoạn) và hết giới hạn bước; điểm 3/9 được chấm trên workspace tại thời điểm dừng. Đây là hành vi của tác tử (lặp), không phải lỗi hạ tầng, nên giữ nguyên và không chạy lại; giới hạn 60 giống mọi điều kiện.
- `skills_modified` = `false` ở mọi lần chạy (12/12 sau đóng băng).
- Sự cố môi trường (pilot, trước đóng băng): trong `skills-auto/data-learn` của pilot gpt-4o-mini, tác tử chạy `pip install pandas` và cài vào `.venv` của harness (vì `PATH` của shell trỏ tới venv). Đã gỡ pandas, numpy, python-dateutil, six; thêm `PIP_NO_INDEX=1` vào môi trường shell trong `make_backend` để chặn cài gói; các lần chạy bị ảnh hưởng lưu riêng ở `results-pilot-4o-mini/skills-auto-pandas-installed/`. Mọi lần chạy chính (gpt-4.1-mini) diễn ra sau sửa đổi này; `grep 'pip install' results/*/*/trace.md` không có kết quả.

## 8. Phân tích

1. **Tác vụ học:** chỉ `skills-auto` cao hơn `baseline` (0,66 so với 0,48), và toàn bộ chênh lệch đến từ một tác vụ: `logs-learn` 6/9 so với 1/9. `code-learn` và `data-learn` bằng nhau ở cả ba điều kiện. `subagents` thấp hơn (0,40) do `data-learn` 3/8. **Tác vụ đánh giá:** không điều kiện nào cải thiện: `baseline` 0,43, `skills-auto` 0,43 (giống hệt từng tác vụ: 7/11, 5/9, 1/10), `subagents` 0,36. Vậy `skills-auto` "cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá". Dạng này thường là dấu hiệu quá khớp, nhưng ở đây cơ chế khác: skill **không được đọc lần nào** (`skills_read` = 0 ở 12/12 lần chạy `skills-auto`, kể cả `skills-auto-dev`), nên chênh lệch ở `logs-learn` không thể do nội dung skill. Vết cho thấy ở `skills-auto/logs-learn` tác tử viết và chạy script Python (3 lệnh `execute`), còn ở `baseline` và `subagents` nó tự gõ toàn bộ JSON bằng một lệnh `write_file`. System prompt của `skills-auto` dài hơn (có danh sách skill và `SKILLS_NOTE`), và ở nhiệt độ 0 khác biệt prompt đủ để đổi quỹ đạo. Hiệu ứng này không lặp lại ở `logs-eval` (cả ba điều kiện đều tự gõ JSON, đều 1/10). Kết luận: chênh lệch tác vụ học là nhiễu do prompt, không phải "hiệu quả học". H1, H2, H3 đều được số liệu xác nhận.

2. **Check kỹ thuật:** `baseline` 13/18 (học) và 13/18 (đánh giá); `skills-auto` 18/18 và 13/18; `subagents` 11/18 và 11/18. **Check quy ước:** 0/9 (học) và 0/12 (đánh giá) ở **cả ba điều kiện**. Skill do curator sinh **không giúp nhóm check nào**, vì không được đọc. Riêng phần nội dung: skill có chép đúng 9 quy ước của tác vụ học, nên nếu được đọc thì có thể giúp các check `rule_type_hints`, `rule_regression_tests`, `rule_changelog`, `rule_money_in_cents`, `rule_meta_block`, `rule_clean_csv`, `rule_service_names`, `rule_sorted_errors`, `rule_schema_header` (9/12 check quy ước của tác vụ đánh giá có cùng tên). Check quy ước **mới** của tác vụ đánh giá (`rule_version_bump`, `rule_sorted_keys_format`, `rule_source_line`) không thể được skill giúp: curator chỉ thấy phản hồi `detail` của tác vụ học, và các quy ước này không xuất hiện ở đó. Muốn đạt chúng, tác tử phải tự phát hiện quy ước trong workspace (nhóm lỗi A).

3. - **Check mà skill (về nội dung) giúp được nhưng thực tế không giúp vì không được đọc:** `code-eval/rule_changelog`. Skill `python-package-quality-assurance` bước 3 ghi đúng "Record each bug fix in CHANGELOG.md under the heading '## Unreleased' ... - fix(<function name>): <short description>". Vết `skills-auto/code-eval`: không có lệnh `read_file` nào vào `skills/`, tác tử không mở `CHANGELOG.md` và check thất bại giống `baseline`. Tương tự `rule_meta_block`, `rule_money_in_cents` ở `data-eval`.
   - **Check skill không giúp vì skill thiếu:** `logs-eval/timestamps_utc` và `repeat_counts`. Ngay cả khi được đọc, skill `log-file-parsing-and-triage-reporting` chỉ nói "Convert all timestamps to UTC" mà không có bước "phân tích bằng script và đọc lại đầu ra". Vết cả ba điều kiện ở `logs-eval` đều là đọc `worker.log` rồi gọi `write_file` với JSON tự gõ: đây là nguyên nhân thật (nhóm B và D, mục 4) mà curator không rút ra được.
   - Không có check nào mà skill giúp đạt theo cơ chế "đọc skill rồi làm theo"; đây là kết quả âm của thí nghiệm.

4. **Chi phí** (token trung bình mỗi lần chạy, 6 tác vụ): `baseline` 44.281, `subagents` 70.027 (+58%), `skills-auto` 80.928 (+83%). Điểm trên 100.000 token: `baseline` 1,03; `skills-auto` 0,68; `subagents` 0,54. Trên tác vụ đánh giá: 0,79; 0,54; 0,37. **`baseline` hiệu quả nhất** ở mọi cách tính. Khoảng 97% token là token đầu vào (ví dụ `baseline` 42.791 trên 44.281), tức là chi phí do ngữ cảnh lớn dần theo số bước, không phải do sinh văn bản. `skills-auto` tốn hơn dù không đọc skill vì danh sách skill được nối vào system prompt của mọi lần gọi, và vì quỹ đạo dài hơn (`data-eval` 146.483 token, 16 tool call). Đa tác tử **không đáng chi phí** trong thí nghiệm này: điểm thấp hơn ở cả tác vụ học (0,40 so với 0,48) và đánh giá (0,36 so với 0,43) mà token đánh giá cao hơn 77% (96.714 so với 54.633). Nguyên nhân từ vết: lời giao việc thiếu thông tin (`data-learn` thiếu tên khóa, mục 5) và vòng lặp đọc tệp ở `subagents/data-eval` (hết `recursion_limit`). Ngay cả `baseline` cũng tự gọi `general-purpose` một lần ở `data-eval` (121.085 token, cao nhất của `baseline`).

5. **Rò rỉ:** không có. `validate_skill` (có sẵn) chặn mọi skill chứa định danh của tác vụ đánh giá; curator chỉ đọc `run.json`/`trace.md` có `role == "learn"` (test `test_04` xác nhận prompt không chứa `data-eval` hay tên check của tác vụ đánh giá); vòng sửa skill chỉ nói lý do chung chung, không đưa định danh đánh giá vào prompt; nhóm không mở `tasks/*-eval/` trước tag `freeze`. Trong pilot, `validate_skill` đã từ chối một skill vì chứa từ "orders" (trùng tên tệp đánh giá), cho thấy cơ chế hoạt động, nhưng cũng là dương tính giả vì từ này có trong câu RULE của tác vụ học. **Quá khớp:** có dấu hiệu nhẹ: skill code chứa "Decimal ... round half up" và "RFC 4180" (chi tiết lỗi của `code-learn`), skill data chứa ví dụ "-999" (giá trị riêng của dữ liệu học; dữ liệu đánh giá dùng giá trị thiếu khác, theo vết `baseline/data-eval` là "-1"). Các chi tiết này không gây hại nhưng không chuyển giao được. Phòng tránh: prompt curator yêu cầu không nêu giá trị, tên cột, định danh của dữ liệu trừ khi nằm trong RULE.

6. **Nhiễu:** cùng bộ skill, Phần 3.4 so với sau đóng băng: `code-learn` 7/10 và 7/10, `data-learn` 5/8 và 5/8, `logs-learn` 6/9 và 6/9, tức **chênh lệch điểm bằng 0** ở cả ba. Token thì dao động mạnh: 61.267 → 76.769 (+25%), 43.106 → 40.697 (-6%), 34.187 → 126.789 (×3,7). Pilot gpt-4o-mini cho thấy điều tương tự (`skills-auto/logs-learn` hai lần đều 0/9 và đúng 30.846 token). Ở nhiệt độ 0, **lặp lại cùng một cấu hình** thường cho cùng điểm, nhưng không luôn luôn: mở rộng 6e (Phụ lục) cho thấy `baseline/data-eval` ra 5/9, 3/9, 5/9 và `subagents/data-eval` ra 3/9, 4/9, 5/9 qua ba lần chạy ở T=0. Bằng chứng là `logs-learn` thay đổi 1/9 → 6/9 chỉ vì system prompt khác (không đọc skill). Vì vậy một chênh lệch ±5 check ở một tác vụ có thể sinh ra chỉ từ thay đổi nhỏ của prompt; các chênh lệch trong bảng mục 7 (0,48 so với 0,66 ở tác vụ học; 0,43 so với 0,36 ở tác vụ đánh giá) không đủ tin cậy để kết luận có ý nghĩa thống kê. Phép lặp 6e xác nhận điều này: qua 5 lần chạy đánh giá mỗi điều kiện, điểm trung bình là `baseline` 0,42 (độ lệch chuẩn 0,03), `subagents` 0,37 (0,07), `skills-auto` 0,46 (0,06), các khoảng dao động chồng lên nhau. Chỉ hai kết luận chắc chắn: check quy ước 0/60 ở mọi điều kiện và mọi lần lặp, và đa tác tử tốn nhiều token hơn `baseline`.

## 9. Hạn chế và tính hợp lệ

1. **Mẫu rất nhỏ:** 3 tác vụ học, 3 tác vụ đánh giá, 1 họ cho mỗi loại việc. Một tác vụ (`logs-learn`) quyết định toàn bộ chênh lệch tác vụ học; không thể tính khoảng tin cậy hay kiểm định. Mọi kết luận về "cải thiện" chỉ mang tính mô tả.
2. **Bảng chính chỉ có một lần chạy mỗi ô ở nhiệt độ 0:** mở rộng 6e lặp thêm 4 lần trên tác vụ đánh giá (2 ở T=0, 2 ở T=0,7), nhưng tác vụ học không được lặp, và 5 lần chạy vẫn quá ít để kiểm định. Thay đổi nhỏ của system prompt đã đổi `logs-learn` 1/9 → 6/9, và một lần chạy T=0,7 của `skills-auto/logs-eval` cho 6/10 bằng đúng cơ chế đó (viết script thay vì tự gõ JSON), nên độ nhạy với prompt và lấy mẫu là nguồn bất định lớn nhất.
3. **Một mô hình duy nhất (gpt-4.1-mini) và mô hình không tuân thủ chỉ dẫn đọc skill:** `skills_read` = 0 ở 12/12 lần chạy, nên thí nghiệm **không kiểm định được** giả thuyết "skill tự sinh giúp tác tử"; nó chỉ cho thấy "skill không được đọc thì không giúp". Pilot gpt-4o-mini cũng có `skills_read` = 0. Kết luận về skill không tổng quát hóa cho mô hình mạnh hơn, vốn có thể tuân thủ `SKILLS_NOTE`.
4. **Tác vụ và quy ước do giảng viên thiết kế:** 12/17 check thất bại của `baseline` trên tác vụ đánh giá là quy ước ẩn (`rule_`) mà đề không nhắc. Điểm vì vậy đo khả năng "đoán quy ước" nhiều hơn năng lực kỹ thuật, và thiên vị cho phương pháp chép quy ước từ phản hồi (như curator). Mỗi tác vụ đánh giá có thêm một quy ước mới mà không phương pháp nào ở đây có thể học được.
5. **Thay đổi harness trong lúc làm:** prompt curator được chỉnh sau pilot và `PIP_NO_INDEX=1` được thêm sau sự cố cài gói. Mọi lần chạy chính diễn ra sau các thay đổi này nên so sánh giữa các điều kiện vẫn công bằng, nhưng kết quả pilot không so sánh trực tiếp được với kết quả chính.
6. **Đếm `tool_calls` và `skills_read` chỉ ở luồng chính:** nếu subagent `general-purpose` đọc skill thì không được đếm. Tuy vậy, ở `skills-auto` không có lần gọi `task` nào (`subagent_calls` = 0), nên hạn chế này không ảnh hưởng kết luận về skill.

## 10. Kết luận

Trên gpt-4.1-mini, không điều kiện nào cải thiện tác vụ đánh giá so với `baseline` (0,43): `skills-auto` bằng (0,43) và `subagents` thấp hơn (0,36), trong khi `baseline` rẻ nhất (44.281 token/lần chạy so với 70.027 và 80.928). Curator đã rút ra skill đúng và đủ 9 quy ước từ phản hồi tác vụ học, nhưng tác tử không đọc skill lần nào (`skills_read` = 0 ở 12/12 lần chạy), nên check quy ước vẫn 0/21 ở mọi điều kiện. Đa tác tử làm mất thông tin khi giao việc và tăng token mà không tăng điểm. Mức tăng của `skills-auto` trên tác vụ học (0,48 → 0,66) là hiệu ứng của prompt chứ không phải học, vì nó không lặp lại trên tác vụ đánh giá. Đề xuất tiếp theo: bỏ phụ thuộc vào việc tác tử tự chọn đọc skill bằng cách nạp nội dung skill trực tiếp (ví dụ đưa vào system prompt, hoặc tự động đọc skill có `description` khớp), rồi lặp lại thí nghiệm với vài lần chạy ở nhiệt độ > 0 để tách hiệu quả skill khỏi nhiễu.

## Phụ lục

- Lệnh đã chạy (theo thứ tự, thí nghiệm chính với `LAB_MODEL=openai:gpt-4.1-mini`):

```bash
python3.12 -m venv .venv && source .venv/bin/activate && pip install -e .
pytest                                               # 32 passed (test_01 15, test_02 9, test_03 6, test_04 2)
python scripts/tour.py
python -m lab.runner --condition baseline --tasks learn
python -m lab.runner --condition subagents --tasks learn
python -m lab.curator                                # 1 lần, 3 skill
python -m lab.runner --condition skills-auto --tasks learn
mv results/skills-auto results/skills-auto-dev
git add -A && git commit -m "hypotheses"
git commit --allow-empty -m "freeze skills" && git tag freeze
python -m lab.runner --condition baseline --tasks eval
python -m lab.runner --condition subagents --tasks eval
python -m lab.runner --condition skills-auto --tasks all
python scripts/verify_freeze.py                      # OK
python -m lab.compare > report/table.md
python scripts/check_breakdown.py
```

- **Thử thách mở rộng: 6e. Lặp để đo nhiễu.**
  - **Thiết kế:** chạy lại cả ba điều kiện trên 3 tác vụ đánh giá thêm 4 lần, mỗi lần một thư mục `--results` riêng: 2 lần ở cấu hình chính (`LAB_TEMPERATURE=0`, `results-6e/t0-rep1`, `t0-rep2`) và 2 lần ở `LAB_TEMPERATURE=0.7` (`results-6e/t07-rep1`, `t07-rep2`) để thấy độ nhạy với lấy mẫu. Tổng 36 lần chạy, cùng mô hình, cùng `recursion_limit=60`, cùng bộ skill đóng băng (`skills_sha256` của mọi lần chạy `skills-auto` trong `results-6e/` trùng với `results/`, `skills_modified` = `false` ở 36/36; mọi lần chạy diễn ra sau tag `freeze`, từ 2026-10-06T10:44Z). Bảng chính (mục 7) giữ nguyên, không bị thay bằng kết quả lặp. Bảng đầy đủ: `report/table-6e.md` (sinh bằng `python scripts/repeat_noise.py`).
  - **Kết quả theo tác vụ** (lần chạy chính được tính là lần lặp thứ nhất ở T=0):

    | Tác vụ | baseline (T=0 ×3; T=0,7 ×2) | subagents | skills-auto |
    |---|---|---|---|
    | code-eval | 7, 7, 7; 7, 7 /11 | 7, 7, 7; 7, 7 /11 | 7, 7, 7; 6, 7 /11 |
    | data-eval | 5, 3, 5; 5, 5 /9 | 3, 4, 5; 0, 5 /9 | 5, 5, 5; 5, 5 /9 |
    | logs-eval | 1, 1, 1; 1, 1 /10 | 1, 0, 1; 1, 1 /10 | 1, 1, 1; 6, 1 /10 |

  - **Tổng hợp trên 5 lần chạy mỗi điều kiện** (điểm = trung bình 3 tác vụ đánh giá của một lần lặp):

    | | baseline | subagents | skills-auto |
    |---|---|---|---|
    | Điểm trung bình [min-max] | 0,42 [0,36-0,43] | 0,37 [0,25-0,43] | 0,46 [0,43-0,57] |
    | Độ lệch chuẩn của điểm | 0,03 | 0,07 | 0,06 |
    | Check kỹ thuật (trên 18) mỗi lần lặp | 13, 11, 13, 13, 13 | 11, 11, 13, 8, 13 | 13, 13, 13, 17, 13 |
    | Check quy ước | 0/60 | 0/60 | 0/60 |
    | Token trung bình mỗi lần chạy [min-max của từng lần lặp] | 34.924 [22.861-54.633] | 57.572 [38.770-96.714] | 60.238 [45.339-80.438] |
    | Lần chạy đọc skill | 0/15 | 0/15 | 0/15 |

  - **So với kết quả chính:**
    - Thứ tự điểm trung bình (`skills-auto` ≥ `baseline` > `subagents`) giống bảng chính, nhưng khoảng dao động của ba điều kiện chồng lên nhau và chênh lệch lớn nhất (0,46 so với 0,42) nhỏ hơn biên độ dao động của một điều kiện (`subagents` 0,25-0,43). Không có chênh lệch nào đủ tin cậy; kết luận "không điều kiện nào cải thiện tác vụ đánh giá" của mục 10 giữ nguyên.
    - Ở T=0 điểm **không** hoàn toàn tất định: 2/9 ô thay đổi giữa các lần lặp (`baseline/data-eval` 5 → 3 → 5, `subagents/data-eval` 3 → 4 → 5, `subagents/logs-eval` 1 → 0 → 1). Như vậy mục 8.6 (dựa trên tác vụ học) đánh giá thấp nhiễu. Token dao động mạnh hơn điểm: `baseline/data-eval` 121.085 → 39.894 → 24.081 token với cùng cấu hình.
    - Hai kết luận chắc chắn vẫn đứng vững qua 45 lần chạy đánh giá: check quy ước 0 ở mọi lần chạy, và skill không được đọc lần nào (`skills_read` = 0 ở 15/15 lần chạy `skills-auto`). `subagents` tốn hơn `baseline` khoảng 65% token mà không tăng điểm.
  - **Cơ chế (từ vết) của các lần chạy lệch:**
    - `skills-auto/logs-eval`, T=0,7 rep1, 6/10: tác tử viết và chạy một script Python (`execute`) để phân tích log, trong khi 14/15 lần chạy `logs-eval` còn lại (mọi điều kiện) không chạy lệnh `execute` nào mà tự gõ JSON. Đạt toàn bộ 5 check kỹ thuật, trượt cả 4 check quy ước. Không đọc skill. Đây đúng là cơ chế đã thấy ở `skills-auto/logs-learn` (mục 8.1): mức tăng đến từ việc tác tử chọn dùng script, không phải từ nội dung skill, và chỉ xuất hiện ở 1/5 lần chạy.
    - `subagents/data-eval`, T=0,7 rep1, 0/9: subagent `general-purpose` trả về một đoạn code chưa chạy cùng lời hứa "I will perform the analysis now"; tác tử chính không kiểm tra mà ghi ngay `answer.json` với các con số tự bịa (nhóm D, mục 4). Đây là dạng hỏng riêng của đa tác tử: chỉ dẫn "Check what a subagent returns" trong `SUBAGENTS_NOTE` không được làm theo.
    - `baseline/data-eval`, T=0 rep1, 3/9: script chạy được (có `datetime.fromisoformat`, phần còn lại của script bị cắt trong vết) nhưng ra sai `march_revenue_utc` và `march_orders_utc`, phù hợp với việc lấy tháng trước khi đổi sang UTC (nhóm B; không xác nhận được dòng lỗi vì vết bị cắt). Hai lần lặp khác ở T=0 làm đúng.
    - `subagents` có độ lệch chuẩn lớn nhất vì mỗi lần chạy thêm một bước giao việc mà chất lượng lời giao và việc kiểm tra kết quả thay đổi giữa các lần.
  - **Sự cố khi chạy:** lần thử đầu của `skills-auto/code-eval` ở T=0,7 rep2 bị treo hơn 10 phút trên một kết nối HTTPS tới API (không ghi `run.json`, không có `error`). Tôi dừng tiến trình, xóa thư mục `results-6e/t07-rep2/skills-auto` chưa hoàn tất và chạy lại 3 tác vụ của ô này một lần. Đây là lỗi hạ tầng, không phải hành vi của tác tử, và không có kết quả nào bị loại theo điểm số. Không có lần chạy nào trong `results-6e/` cài gói (`grep 'pip install'` không có kết quả).
  - **Hạn chế:** 5 lần chạy mỗi ô vẫn quá ít để tính khoảng tin cậy có ý nghĩa; trộn T=0 và T=0,7 trong tổng hợp làm khoảng dao động phản ánh cả hai nguồn nhiễu; tác vụ học không được lặp nên mức tăng `logs-learn` 1/9 → 6/9 chưa được đo lại trực tiếp. Bước tiếp theo hợp lý: ≥10 lần lặp ở T=0,7 cho từng điều kiện và kiểm định hoán vị trên điểm từng tác vụ.
  - **Lệnh tái lập:**

    ```bash
    for temp in 0 0.7; do for rep in rep1 rep2; do
      for c in baseline subagents skills-auto; do
        LAB_TEMPERATURE=$temp python -m lab.runner --condition $c --tasks eval --results "results-6e/t${temp//./}-$rep"
      done
    done; done
    python scripts/repeat_noise.py > report/table-6e.md
    ```
- Pilot gpt-4o-mini (`results-pilot-4o-mini/`, `report/curator-history/pilot-4o-mini-*`): `baseline` học 5/10, 1/8, 1/9; `subagents` 5/10, 0/8 (hết `recursion_limit`, 407.246 token), 0/9; `skills-auto` (sau khi khôi phục môi trường) 2/10 (hết `recursion_limit`), 1/8, 0/9 (tác tử viết JSON trong lời gọi `write_file` dài đến mức hết giới hạn token đầu ra, tệp không được tạo); `skills_read` = 0 ở mọi lần chạy. Bị bỏ vì mô hình thất bại phần lớn check kỹ thuật (không có pandas thì ghi số đoán) và không đọc skill, nên thí nghiệm gần như không cho thông tin; quyết định đổi mô hình được đưa ra **trước** khi viết giả thuyết và đóng băng.
- Thay đổi so với pseudo-code: `run_task` dùng `agent.stream(..., stream_mode="values")` (mở rộng tùy chọn ở `03_runner.md`) để giữ vết khi lỗi; `make_backend` thêm `PIP_NO_INDEX=1`; curator có prompt chặt hơn và một vòng sửa skill (mục 6).

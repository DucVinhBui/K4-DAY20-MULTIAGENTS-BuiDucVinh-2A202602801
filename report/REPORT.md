# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Bùi Đức Vinh | 2A202602801 | Toàn bộ (cá nhân) |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: OpenAI, `LAB_MODEL=openai:gpt-4.1-mini` (API trả về `gpt-4.1-mini-2025-04-14`), `LAB_TEMPERATURE=0`, `recursion_limit=60` (mặc định). Một lần chạy thử (pilot) với `openai:gpt-4o-mini` đã bị bỏ vì mô hình quá yếu (xem Phụ lục); kết quả pilot lưu ở `results-pilot-4o-mini/`, không dùng trong bảng chính.
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: deepagents 0.7.21, macOS 27.0 (Apple Silicon), Python 3.12, chạy trực tiếp (không Docker).
- Số lần chạy tác vụ đã dùng / ngân sách: thí nghiệm chính (gpt-4.1-mini) 3 điều kiện × 3 tác vụ học trước đóng băng + 12 lần chạy sau đóng băng (6 đánh giá cho baseline và subagents, 6 cho skills-auto); 1 lần gọi curator. Pilot (gpt-4o-mini): 12 lần chạy + 3 lần gọi curator. Không có ngân sách cố định do giảng viên đặt; khóa API cá nhân.
- Commit của tag `freeze`:

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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:

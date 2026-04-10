# Phân tích AI cho game XO/Caro (7x7, 9x9, 11x11)

Tài liệu này phân tích kỹ, sâu và có hệ thống các thuật toán AI có thể dùng cho game XO/Caro 1 người chơi với máy, luật thắng là 5 quân liên tiếp.

## 1) Mô hình bài toán

### 1.1. Bản chất game

Game XO/Caro thuộc nhóm:

- Đối kháng 2 người chơi (zero-sum).
- Thông tin hoàn hảo (không có thông tin ẩn).
- Luân phiên lượt đi.
- Không gian trạng thái hữu hạn.

Ta mô hình hóa bằng **cây trò chơi**:

- Mỗi node là một trạng thái bàn cờ.
- Mỗi cạnh là một nước đi hợp lệ.
- Node Max: lượt AI.
- Node Min: lượt người chơi.

Mục tiêu AI là tìm nước đi tối ưu để tối đa hóa xác suất thắng (hoặc tối đa hóa giá trị đánh giá).

### 1.2. Đặc thù của bàn cờ 7/9/11 với luật 5 liên tiếp

Khác với tic-tac-toe 3x3, bàn lớn có:

- Branching factor cao (nhiều nước đi hợp lệ).
- Không thể duyệt hết cây đến trạng thái kết thúc trong thời gian ngắn.

Vì vậy AI bắt buộc phải kết hợp:

1. Tìm kiếm có cắt tỉa.
2. Hàm đánh giá heuristic ở độ sâu hữu hạn.
3. Cơ chế ưu tiên các tình huống bắt buộc (thắng ngay/chặn thua ngay).

---

## 2) Các nhóm thuật toán AI

## 2.1. Random / Rule-based (mức nền)

### Random

AI chọn ngẫu nhiên một ô trống.

- Ưu điểm: cực nhanh, cài đặt đơn giản.
- Nhược điểm: rất yếu, không có chiến lược.

### Rule-based

Dùng các luật ưu tiên, ví dụ:

1. Có nước thắng ngay thì đi ngay.
2. Đối thủ có nước thắng ngay thì chặn ngay.
3. Tạo open-four nếu có.
4. Chặn open-three nguy hiểm.
5. Nếu chưa có gì đặc biệt thì đi gần trung tâm/cụm quân.

- Ưu điểm: phản ứng chiến thuật tốt ở các pattern rõ ràng.
- Nhược điểm: khó mở rộng, dễ “mù chiến thuật sâu”.

Kết luận: rule-based nên là lớp bổ trợ, không nên là lõi duy nhất.

---

## 2.2. Minimax

Minimax là nền tảng lý thuyết cho game zero-sum:

- Max (AI) cố gắng tối đa hóa điểm.
- Min (người chơi) cố gắng tối thiểu hóa điểm của AI.

Pseudo-code:

```text
minimax(state, depth, maximizing):
  if terminal(state) or depth == 0:
    return evaluate(state)

  if maximizing:
    best = -INF
    for move in legal_moves(state):
      best = max(best, minimax(next_state, depth-1, false))
    return best
  else:
    best = +INF
    for move in legal_moves(state):
      best = min(best, minimax(next_state, depth-1, true))
    return best
```

Độ phức tạp xấp xỉ `O(b^d)` (b: số nhánh, d: độ sâu).

Với caro bàn lớn, minimax thuần thường quá chậm.

---

## 2.3. Negamax

Negamax là biến thể gọn của minimax dựa trên tính đối xứng zero-sum.

Ý tưởng:

`max(a,b) = -min(-a,-b)`

Pseudo-code:

```text
negamax(state, depth, color):
  if terminal or depth == 0:
    return color * evaluate(state)

  best = -INF
  for move in legal_moves(state):
    score = -negamax(next_state, depth-1, -color)
    best = max(best, score)
  return best
```

- Ưu điểm: code ngắn, ít lặp logic Max/Min.
- Sức mạnh tương đương minimax khi cùng điều kiện.

---

## 2.4. Alpha-Beta Pruning

Đây là tối ưu bắt buộc khi dùng minimax/negamax.

- `alpha`: giá trị tốt nhất Max đã đảm bảo.
- `beta`: giá trị tốt nhất Min đã đảm bảo.
- Nếu `alpha >= beta` thì cắt nhánh (prune) vì nhánh đó không còn khả năng cải thiện kết quả.

Pseudo-code:

```text
alphabeta(state, depth, alpha, beta, maximizing):
  if terminal or depth == 0:
    return evaluate(state)

  if maximizing:
    value = -INF
    for move in ordered_moves(state):
      value = max(value, alphabeta(next, depth-1, alpha, beta, false))
      alpha = max(alpha, value)
      if alpha >= beta: break
    return value
  else:
    value = +INF
    for move in ordered_moves(state):
      value = min(value, alphabeta(next, depth-1, alpha, beta, true))
      beta = min(beta, value)
      if alpha >= beta: break
    return value
```

Hiệu quả:

- Tệ nhất: vẫn `O(b^d)`.
- Tốt (ordering tốt): gần `O(b^(d/2))`.

Nghĩa là cùng thời gian, AI đi sâu hơn đáng kể.

---

## 2.5. Iterative Deepening (IDS)

Thay vì tìm trực tiếp depth lớn, AI tìm theo lớp:

- depth 1, rồi depth 2, rồi depth 3...
- đến khi hết thời gian.

Ưu điểm:

1. Anytime algorithm: luôn có lời giải tạm thời tốt nhất hiện có.
2. Tận dụng kết quả depth trước để ordering tốt hơn ở depth sau.
3. Ổn định khi có time limit.

Đây là mảnh ghép rất quan trọng cho mức `hard`.

---

## 2.6. Heuristic Evaluation

Vì không đi đến lá kết thúc toàn bộ cây, cần hàm đánh giá trung gian.

Công thức tổng quát:

```text
score(board) = score_patterns(AI) - score_patterns(Human)
```

### 2.6.1. Pattern chiến thuật thường dùng

- five-in-a-row: thắng ngay.
- open-four: 4 liên tiếp, mở hai đầu (rất mạnh).
- closed-four: 4 liên tiếp, mở một đầu.
- open-three, closed-three.
- open-two...

### 2.6.2. Nguyên tắc đặt trọng số

Trọng số phải phản ánh đúng thứ tự ưu tiên chiến thuật:

1. Thắng ngay.
2. Chặn thua ngay.
3. Open-four.
4. Closed-four.
5. Open-three...

Nếu thứ tự này sai, AI dễ “ham tấn công” và bỏ phòng thủ.

---

## 2.7. Move Ordering

Alpha-beta mạnh hay yếu phụ thuộc rất nhiều vào thứ tự duyệt nước đi.

Ordering tốt thường ưu tiên:

- Nước thắng ngay.
- Nước chặn thua ngay.
- Nước tạo run dài/open-end tốt.
- Nước gần tâm hoặc gần cụm quân.

Ordering càng tốt, prune càng nhiều, depth thực tế càng sâu.

---

## 2.8. Candidate Move Generation

Không thể duyệt tất cả ô trống ở mọi node.

Chiến lược phổ biến:

- Chỉ lấy ô trống trong bán kính `r` quanh các quân đã có.
- Sắp xếp ưu tiên.
- Giới hạn top-K.

Ưu điểm:

- Giảm mạnh branching factor.

Rủi ro:

- Có thể bỏ sót nước quan trọng nằm ngoài vùng candidate.

Khắc phục:

- Luôn quét global cho nước thắng/chặn ngay.
- Ở mức hard, có thể merge candidate cục bộ với danh sách “safe move” toàn cục.

---

## 2.9. Transposition Table (TT)

Cùng một trạng thái bàn cờ có thể đạt được qua nhiều thứ tự nước đi khác nhau.

TT là bộ nhớ đệm:

- Key: hash trạng thái + depth + side-to-move.
- Value: điểm đã tính.

Lợi ích:

- Tránh tính lại.
- Tăng tốc search rõ rệt.

---

## 2.10. Zobrist Hashing

Để TT hiệu quả, hash phải cập nhật nhanh khi đi/hoàn tác một quân.

Nguyên lý:

- Mỗi ô và mỗi loại quân (X/O) có một số ngẫu nhiên 64-bit.
- Hash board là XOR của các khóa tương ứng.
- Khi thêm/bỏ quân tại ô `(r,c)`: chỉ XOR lại đúng khóa đó.

Ưu điểm:

- Cập nhật `O(1)`.
- Rất hợp với alpha-beta có nhiều thao tác apply/unapply move.

---

## 2.11. Threat-Space Search (TSS)

TSS tập trung vào chuỗi đe dọa cưỡng bức, ví dụ:

- “Nếu tôi đi A, đối thủ buộc phải chặn B.”
- Sau đó tôi lại tạo đe dọa mới mạnh hơn.

Ưu điểm:

- Rất mạnh cho game kiểu gomoku/caro.

Nhược điểm:

- Cài đặt phức tạp hơn alpha-beta chuẩn.

Thực tế thường kết hợp TSS với alpha-beta để nâng lực chiến thuật.

---

## 2.12. Quiescence Search

Mục tiêu là giảm **horizon effect** (đánh giá sai vì cắt depth ở trạng thái đang quá “nóng”).

Ý tưởng:

- Khi gặp node có đe dọa trực tiếp (sắp thắng/sắp thua), mở rộng thêm vài lớp chọn lọc.

Ưu điểm:

- Giảm sai số đánh giá ở biên độ sâu.

Đánh đổi:

- Tăng thời gian tính.

---

## 2.13. Monte Carlo Tree Search (MCTS)

MCTS gồm 4 bước lặp:

1. Selection
2. Expansion
3. Simulation
4. Backpropagation

UCT phổ biến:

```text
UCT = Q/N + c * sqrt(ln(N_parent) / N)
```

Ưu điểm:

- Mạnh ở không gian nhánh lớn.
- Không phụ thuộc hoàn toàn vào heuristic thủ công.

Nhược điểm trong caro thuần:

- Cần nhiều rollout để ổn định.
- Rollout ngẫu nhiên thường chất lượng thấp nếu không có policy tốt.

---

## 2.14. Reinforcement Learning / Deep Learning

Các hướng hiện đại:

- Policy network: gợi ý nước đi tốt.
- Value network: ước lượng xác suất thắng.
- Kết hợp self-play + MCTS + network (phong cách AlphaZero).

Ưu điểm:

- Có thể học chiến lược sâu mà rule thủ công khó đạt.

Nhược điểm:

- Huấn luyện tốn tài nguyên lớn.
- Khó triển khai cho đồ án nhỏ cần tính giải thích cao.

---

## 3) Đối chiếu với dự án hiện tại

AI hiện tại trong dự án đang đi đúng hướng “classical AI” mạnh và dễ thuyết trình:

- Alpha-beta pruning.
- Iterative deepening.
- Heuristic theo run/open-end.
- Candidate generation + move ordering.
- Transposition table + Zobrist hash.
- Lớp ưu tiên chiến thuật bắt buộc (thắng ngay/chặn thua ngay).

Đây là lựa chọn cân bằng tốt giữa:

- Sức mạnh thực chiến.
- Tốc độ phản hồi.
- Tính giải thích cho giảng viên.

---

## 4) Vì sao hard chưa thể “hoàn hảo tuyệt đối” mọi tình huống?

Muốn tuyệt đối theo nghĩa lý tưởng cần gần như giải toàn cục rất sâu, trong khi thực tế bị ràng buộc:

- Time budget mỗi lượt.
- Độ sâu tối đa.
- Candidate pruning.
- Sai số heuristic tại node lá.

Ngoài ra có thế cờ "double-threat" mà bên phòng thủ không thể chặn hết trong 1 nước.

Vì vậy mục tiêu đúng trong thực tế là:

- Không bỏ nước thắng/chặn ngay kiểu cơ bản.
- Giảm tối đa lỗi chiến thuật trong time limit cho phép.

---

## 5) Hướng nâng cấp để hard mạnh hơn nữa

## 5.1. Nâng cấp chiến thuật

- Nhận diện mạnh hơn các dạng double-threat.
- Bổ sung pattern nâng cao: broken-three, jump-four...
- Threat-space search cục bộ ở node “nóng”.

## 5.2. Nâng cấp tìm kiếm

- Principal Variation Search (PVS/NegaScout).
- Quiescence search chọn lọc.
- Killer move heuristic, history heuristic.

## 5.3. Nâng cấp quản lý thời gian

- Time management động theo độ nóng của thế cờ.
- Cho hard thêm thời gian khi gần trạng thái quyết định.

## 5.4. Nâng cấp hệ thống

- Song song hóa tìm kiếm (multi-thread).
- TT có giới hạn bộ nhớ + chiến lược thay thế tối ưu.

---

## 6) So sánh nhanh các nhóm thuật toán

| Thuật toán | Độ mạnh chiến thuật | Tốc độ | Dễ giải thích | Phù hợp đồ án |
|---|---:|---:|---:|---:|
| Random | Rất thấp | Rất nhanh | Rất dễ | Chỉ baseline |
| Rule-based | Thấp-vừa | Nhanh | Dễ | Bổ trợ tốt |
| Minimax thuần | Vừa | Chậm | Dễ | Không hợp bàn lớn |
| Negamax + Alpha-beta | Cao | Tốt | Dễ-vừa | Rất phù hợp |
| Alpha-beta + IDS + TT + heuristic | Rất cao | Tốt | Vừa | Lựa chọn hiện tại |
| MCTS thuần | Vừa-cao | Trung bình | Khó hơn | Có thể thử nghiệm |
| MCTS + Deep NN | Rất cao | Mạnh (sau train) | Khó | Quá nặng cho đồ án cơ bản |

---

## 7) Pseudo-code trình bày ngắn gọn với thầy

```text
choose_move(board, level):
  # 1) Luật bắt buộc
  if tồn tại nước AI thắng ngay: return nước đó
  if tồn tại nước người chơi thắng ngay: return nước chặn

  # 2) Tìm kiếm tăng dần độ sâu
  best = null
  for depth = 1..max_depth(level):
    thử:
      best = alpha_beta_root(board, depth, time_limit(level))
    nếu hết thời gian:
      break

  # 3) Trả về phương án tốt nhất đã hoàn thành
  return best
```

Điểm nhấn nên nói khi bảo vệ:

- AI không “đoán bừa”.
- AI tối ưu trên cây trạng thái trong giới hạn tài nguyên tính toán.
- Chất lượng đến từ tổ hợp: search + pruning + heuristic + cache + tactical rules.

---

## 8) Kết luận

Với yêu cầu game XO/Caro real-time trên 7x7, 9x9, 11x11 và cần dễ giải thích học thuật:

- Hướng tốt nhất là: **Alpha-beta + Iterative Deepening + Heuristic + Candidate + TT/Zobrist + Tactical checks**.

Nếu cần nâng lên cấp “siêu khó” trong tương lai:

- Bổ sung TSS/PVS/Quiescence,
- Hoặc đi hướng dài hạn: MCTS + Neural Network.

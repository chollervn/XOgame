from __future__ import annotations

import random
import time
from dataclasses import dataclass

from backend.game_engine import EMPTY_CELL, board_full, check_winner

INF = 10**15
WIN_SCORE = 10**9


class SearchTimeout(Exception):
    pass


@dataclass(frozen=True)
class DifficultyProfile:
    max_depth: int
    time_limit_seconds: float
    max_candidates: int
    candidate_radius: int
    randomness: float
    top_k_random: int


PROFILE_BY_SIZE = {
    "easy": {
        7: DifficultyProfile(2, 0.25, 10, 1, 0.35, 3),
        9: DifficultyProfile(2, 0.25, 10, 1, 0.35, 3),
        11: DifficultyProfile(1, 0.25, 10, 1, 0.35, 3),
    },
    "medium": {
        7: DifficultyProfile(3, 0.75, 16, 2, 0.12, 2),
        9: DifficultyProfile(3, 0.75, 16, 2, 0.12, 2),
        11: DifficultyProfile(2, 0.75, 16, 2, 0.12, 2),
    },
    "hard": {
        7: DifficultyProfile(5, 4.0, 28, 2, 0.0, 1),
        9: DifficultyProfile(5, 4.0, 28, 2, 0.0, 1),
        11: DifficultyProfile(4, 4.5, 30, 2, 0.0, 1),
    },
}

RUN_SCORES = {
    1: {1: 8, 2: 30},
    2: {1: 120, 2: 900},
    3: {1: 1200, 2: 8000},
    4: {1: 15000, 2: 120000},
}

DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))
SYMBOL_INDEX = {"X": 0, "O": 1}
_ZOBRIST_CACHE: dict[int, list[list[list[int]]]] = {}


def choose_ai_move(
    board: list[list[str]],
    ai_symbol: str,
    human_symbol: str,
    difficulty: str,
) -> tuple[int, int] | None:
    if board_full(board):
        return None

    size = len(board)
    profile = PROFILE_BY_SIZE[difficulty][size]
    all_empty_moves = _all_empty_moves(board)
    if not all_empty_moves:
        return None

    candidates = generate_candidate_moves(board, profile.candidate_radius, profile.max_candidates)

    if not candidates:
        return None

    immediate_win = _find_winning_move(board, all_empty_moves, ai_symbol)
    if immediate_win is not None:
        return immediate_win

    immediate_blocks = _find_all_winning_moves(board, all_empty_moves, human_symbol)
    if immediate_blocks:
        if len(immediate_blocks) == 1:
            return immediate_blocks[0]
        return max(
            immediate_blocks,
            key=lambda move: _quick_move_score(board, move, ai_symbol),
        )

    if difficulty in {"medium", "hard"}:
        safe_candidates = _safe_moves_against_immediate_loss(
            board=board,
            candidate_moves=candidates,
            ai_symbol=ai_symbol,
            human_symbol=human_symbol,
        )
        if safe_candidates:
            candidates = safe_candidates

    if difficulty == "hard":
        safe_global_moves = _safe_moves_against_immediate_loss(
            board=board,
            candidate_moves=all_empty_moves,
            ai_symbol=ai_symbol,
            human_symbol=human_symbol,
        )
        if safe_global_moves:
            candidates = _merge_move_lists(
                primary=candidates,
                secondary=_order_moves_for_root(board, safe_global_moves, ai_symbol),
                limit=max(profile.max_candidates * 2, 40),
            )

    start_time = time.perf_counter()
    zobrist = _get_zobrist(size)
    root_hash = _board_hash(board, zobrist)
    tt: dict[tuple[int, int, bool], int] = {}

    best_ranked: list[tuple[int, tuple[int, int]]] = [
        (evaluate_board(board, ai_symbol, human_symbol), candidates[0])
    ]

    for depth in range(1, profile.max_depth + 1):
        try:
            ranked = _search_root(
                board=board,
                depth=depth,
                ai_symbol=ai_symbol,
                human_symbol=human_symbol,
                alpha=-INF,
                beta=INF,
                start_time=start_time,
                time_limit=profile.time_limit_seconds,
                tt=tt,
                zobrist=zobrist,
                board_hash=root_hash,
                profile=profile,
                root_candidates=candidates,
            )
            if ranked:
                best_ranked = ranked
        except SearchTimeout:
            break

    chosen_move = _pick_move_with_difficulty_noise(best_ranked, profile)

    if difficulty == "hard":
        safe_global_moves = _safe_moves_against_immediate_loss(
            board=board,
            candidate_moves=all_empty_moves,
            ai_symbol=ai_symbol,
            human_symbol=human_symbol,
        )
        if safe_global_moves and _is_immediate_losing_move(board, chosen_move, ai_symbol, human_symbol):
            chosen_move = max(
                safe_global_moves,
                key=lambda move: _safe_move_priority(board, move, ai_symbol, human_symbol),
            )

    return chosen_move


def _search_root(
    board: list[list[str]],
    depth: int,
    ai_symbol: str,
    human_symbol: str,
    alpha: int,
    beta: int,
    start_time: float,
    time_limit: float,
    tt: dict[tuple[int, int, bool], int],
    zobrist: list[list[list[int]]],
    board_hash: int,
    profile: DifficultyProfile,
    root_candidates: list[tuple[int, int]],
) -> list[tuple[int, tuple[int, int]]]:
    _check_timeout(start_time, time_limit)

    ordered_moves = _order_moves_for_root(board, root_candidates, ai_symbol)

    ranked: list[tuple[int, tuple[int, int]]] = []
    local_alpha = alpha

    for move in ordered_moves:
        _check_timeout(start_time, time_limit)
        row, col = move
        board[row][col] = ai_symbol
        try:
            next_hash = board_hash ^ zobrist[row][col][SYMBOL_INDEX[ai_symbol]]
            score = _alphabeta(
                board=board,
                depth=depth - 1,
                maximizing=False,
                ai_symbol=ai_symbol,
                human_symbol=human_symbol,
                alpha=local_alpha,
                beta=beta,
                start_time=start_time,
                time_limit=time_limit,
                tt=tt,
                zobrist=zobrist,
                board_hash=next_hash,
                profile=profile,
            )
        finally:
            board[row][col] = EMPTY_CELL

        ranked.append((score, move))
        if score > local_alpha:
            local_alpha = score

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def _alphabeta(
    board: list[list[str]],
    depth: int,
    maximizing: bool,
    ai_symbol: str,
    human_symbol: str,
    alpha: int,
    beta: int,
    start_time: float,
    time_limit: float,
    tt: dict[tuple[int, int, bool], int],
    zobrist: list[list[list[int]]],
    board_hash: int,
    profile: DifficultyProfile,
) -> int:
    _check_timeout(start_time, time_limit)

    winner, _ = check_winner(board)
    if winner == ai_symbol:
        return WIN_SCORE + depth
    if winner == human_symbol:
        return -WIN_SCORE - depth
    if board_full(board):
        return 0
    if depth == 0:
        return evaluate_board(board, ai_symbol, human_symbol)

    key = (board_hash, depth, maximizing)
    if key in tt:
        return tt[key]

    candidates = generate_candidate_moves(
        board,
        profile.candidate_radius,
        profile.max_candidates,
    )

    if not candidates:
        return evaluate_board(board, ai_symbol, human_symbol)

    if maximizing:
        player = ai_symbol
        ordered_moves = sorted(
            candidates,
            key=lambda move: _quick_move_score(board, move, player),
            reverse=True,
        )
        value = -INF

        for row, col in ordered_moves:
            board[row][col] = player
            try:
                next_hash = board_hash ^ zobrist[row][col][SYMBOL_INDEX[player]]
                value = max(
                    value,
                    _alphabeta(
                        board=board,
                        depth=depth - 1,
                        maximizing=False,
                        ai_symbol=ai_symbol,
                        human_symbol=human_symbol,
                        alpha=alpha,
                        beta=beta,
                        start_time=start_time,
                        time_limit=time_limit,
                        tt=tt,
                        zobrist=zobrist,
                        board_hash=next_hash,
                        profile=profile,
                    ),
                )
            finally:
                board[row][col] = EMPTY_CELL

            alpha = max(alpha, value)
            if beta <= alpha:
                break
    else:
        player = human_symbol
        ordered_moves = sorted(
            candidates,
            key=lambda move: _quick_move_score(board, move, player),
            reverse=True,
        )
        value = INF

        for row, col in ordered_moves:
            board[row][col] = player
            try:
                next_hash = board_hash ^ zobrist[row][col][SYMBOL_INDEX[player]]
                value = min(
                    value,
                    _alphabeta(
                        board=board,
                        depth=depth - 1,
                        maximizing=True,
                        ai_symbol=ai_symbol,
                        human_symbol=human_symbol,
                        alpha=alpha,
                        beta=beta,
                        start_time=start_time,
                        time_limit=time_limit,
                        tt=tt,
                        zobrist=zobrist,
                        board_hash=next_hash,
                        profile=profile,
                    ),
                )
            finally:
                board[row][col] = EMPTY_CELL

            beta = min(beta, value)
            if beta <= alpha:
                break

    tt[key] = value
    return value


def evaluate_board(board: list[list[str]], ai_symbol: str, human_symbol: str) -> int:
    ai_score = _score_for_symbol(board, ai_symbol)
    human_score = _score_for_symbol(board, human_symbol)
    return int(ai_score - human_score * 1.05)


def _score_for_symbol(board: list[list[str]], symbol: str) -> int:
    size = len(board)
    score = 0

    for row in range(size):
        for col in range(size):
            if board[row][col] != symbol:
                continue

            for dr, dc in DIRECTIONS:
                prev_r = row - dr
                prev_c = col - dc
                if 0 <= prev_r < size and 0 <= prev_c < size and board[prev_r][prev_c] == symbol:
                    continue

                run_length = 0
                r, c = row, col
                while 0 <= r < size and 0 <= c < size and board[r][c] == symbol:
                    run_length += 1
                    r += dr
                    c += dc

                open_ends = 0
                if 0 <= prev_r < size and 0 <= prev_c < size and board[prev_r][prev_c] == EMPTY_CELL:
                    open_ends += 1
                if 0 <= r < size and 0 <= c < size and board[r][c] == EMPTY_CELL:
                    open_ends += 1

                score += _run_score(run_length, open_ends)

    return score


def _run_score(run_length: int, open_ends: int) -> int:
    if run_length >= 5:
        return 1_000_000
    if open_ends == 0:
        return 0
    if run_length in RUN_SCORES:
        return RUN_SCORES[run_length].get(open_ends, 0)
    return 0


def generate_candidate_moves(
    board: list[list[str]],
    radius: int,
    max_candidates: int,
) -> list[tuple[int, int]]:
    size = len(board)
    occupied: list[tuple[int, int]] = []
    for row in range(size):
        for col in range(size):
            if board[row][col] != EMPTY_CELL:
                occupied.append((row, col))

    if not occupied:
        center = size // 2
        return [(center, center)]

    candidates: set[tuple[int, int]] = set()
    for row, col in occupied:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr = row + dr
                nc = col + dc
                if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == EMPTY_CELL:
                    candidates.add((nr, nc))

    ordered = sorted(candidates, key=lambda move: _candidate_priority(board, move), reverse=True)
    return ordered[:max_candidates]


def _candidate_priority(board: list[list[str]], move: tuple[int, int]) -> float:
    row, col = move
    size = len(board)
    center = size // 2
    center_bias = size - (abs(row - center) + abs(col - center))

    neighbor_count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr = row + dr
            nc = col + dc
            if 0 <= nr < size and 0 <= nc < size and board[nr][nc] != EMPTY_CELL:
                neighbor_count += 1

    return neighbor_count * 10 + center_bias


def _quick_move_score(board: list[list[str]], move: tuple[int, int], symbol: str) -> int:
    row, col = move
    board[row][col] = symbol
    winner, _ = check_winner(board)
    if winner == symbol:
        board[row][col] = EMPTY_CELL
        return WIN_SCORE

    score = _line_score_around(board, move, symbol)
    board[row][col] = EMPTY_CELL
    return score


def _line_score_around(board: list[list[str]], move: tuple[int, int], symbol: str) -> int:
    row, col = move
    size = len(board)
    score = 0

    for dr, dc in DIRECTIONS:
        count = 1
        open_ends = 0

        r, c = row - dr, col - dc
        while 0 <= r < size and 0 <= c < size and board[r][c] == symbol:
            count += 1
            r -= dr
            c -= dc
        if 0 <= r < size and 0 <= c < size and board[r][c] == EMPTY_CELL:
            open_ends += 1

        r, c = row + dr, col + dc
        while 0 <= r < size and 0 <= c < size and board[r][c] == symbol:
            count += 1
            r += dr
            c += dc
        if 0 <= r < size and 0 <= c < size and board[r][c] == EMPTY_CELL:
            open_ends += 1

        score += _run_score(count, open_ends)

    return score


def _find_winning_move(
    board: list[list[str]],
    candidates: list[tuple[int, int]],
    symbol: str,
) -> tuple[int, int] | None:
    for row, col in candidates:
        board[row][col] = symbol
        winner, _ = check_winner(board)
        board[row][col] = EMPTY_CELL
        if winner == symbol:
            return row, col
    return None


def _find_all_winning_moves(
    board: list[list[str]],
    candidates: list[tuple[int, int]],
    symbol: str,
) -> list[tuple[int, int]]:
    wins: list[tuple[int, int]] = []
    for row, col in candidates:
        board[row][col] = symbol
        winner, _ = check_winner(board)
        board[row][col] = EMPTY_CELL
        if winner == symbol:
            wins.append((row, col))
    return wins


def _check_timeout(start_time: float, time_limit: float) -> None:
    if time.perf_counter() - start_time > time_limit:
        raise SearchTimeout


def _pick_move_with_difficulty_noise(
    ranked_moves: list[tuple[int, tuple[int, int]]],
    profile: DifficultyProfile,
) -> tuple[int, int]:
    if not ranked_moves:
        raise ValueError("No ranked moves available")

    if profile.randomness <= 0:
        return ranked_moves[0][1]

    if random.random() > profile.randomness:
        return ranked_moves[0][1]

    top_count = min(profile.top_k_random, len(ranked_moves))
    top_moves = ranked_moves[:top_count]
    return random.choice(top_moves)[1]


def _all_empty_moves(board: list[list[str]]) -> list[tuple[int, int]]:
    size = len(board)
    moves: list[tuple[int, int]] = []
    for row in range(size):
        for col in range(size):
            if board[row][col] == EMPTY_CELL:
                moves.append((row, col))
    return moves


def _safe_moves_against_immediate_loss(
    board: list[list[str]],
    candidate_moves: list[tuple[int, int]],
    ai_symbol: str,
    human_symbol: str,
) -> list[tuple[int, int]]:
    safe_moves: list[tuple[int, int]] = []

    for row, col in candidate_moves:
        board[row][col] = ai_symbol
        human_immediate_win = _find_winning_move(board, _all_empty_moves(board), human_symbol)
        board[row][col] = EMPTY_CELL
        if human_immediate_win is None:
            safe_moves.append((row, col))

    return safe_moves


def _order_moves_for_root(
    board: list[list[str]],
    moves: list[tuple[int, int]],
    symbol: str,
) -> list[tuple[int, int]]:
    return sorted(
        moves,
        key=lambda move: _quick_move_score(board, move, symbol),
        reverse=True,
    )


def _merge_move_lists(
    primary: list[tuple[int, int]],
    secondary: list[tuple[int, int]],
    limit: int,
) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()

    for move in primary:
        if move not in seen:
            merged.append(move)
            seen.add(move)
        if len(merged) >= limit:
            return merged

    for move in secondary:
        if move not in seen:
            merged.append(move)
            seen.add(move)
        if len(merged) >= limit:
            return merged

    return merged


def _is_immediate_losing_move(
    board: list[list[str]],
    move: tuple[int, int],
    ai_symbol: str,
    human_symbol: str,
) -> bool:
    row, col = move
    board[row][col] = ai_symbol
    try:
        return _find_winning_move(board, _all_empty_moves(board), human_symbol) is not None
    finally:
        board[row][col] = EMPTY_CELL


def _safe_move_priority(
    board: list[list[str]],
    move: tuple[int, int],
    ai_symbol: str,
    human_symbol: str,
) -> int:
    row, col = move
    board[row][col] = ai_symbol
    try:
        winner, _ = check_winner(board)
        if winner == ai_symbol:
            return WIN_SCORE
        return evaluate_board(board, ai_symbol, human_symbol)
    finally:
        board[row][col] = EMPTY_CELL


def _get_zobrist(size: int) -> list[list[list[int]]]:
    if size in _ZOBRIST_CACHE:
        return _ZOBRIST_CACHE[size]

    generator = random.Random(20260410 + size)
    table = [
        [
            [generator.getrandbits(64), generator.getrandbits(64)]
            for _ in range(size)
        ]
        for _ in range(size)
    ]
    _ZOBRIST_CACHE[size] = table
    return table


def _board_hash(board: list[list[str]], zobrist: list[list[list[int]]]) -> int:
    h = 0
    size = len(board)
    for row in range(size):
        for col in range(size):
            symbol = board[row][col]
            if symbol in SYMBOL_INDEX:
                h ^= zobrist[row][col][SYMBOL_INDEX[symbol]]
    return h

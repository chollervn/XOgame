import random
from dataclasses import dataclass
from backend.game_engine import EMPTY_CELL, check_winner

INF = 10**15
WIN_SCORE = 10**9

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
_ZOBRIST_CACHE = {}

def evaluate_board(board: list[list[str]], ai_symbol: str, human_symbol: str) -> int:
    ai_score = _score_for_symbol(board, ai_symbol)
    human_score = _score_for_symbol(board, human_symbol)
    return int(ai_score - human_score * 1.05)

def _score_for_symbol(board: list[list[str]], symbol: str) -> int:
    size = len(board)
    score = 0
    for row in range(size):
        for col in range(size):
            if board[row][col] != symbol: continue
            for dr, dc in DIRECTIONS:
                prev_r, prev_c = row - dr, col - dc
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
    if run_length >= 5: return 1_000_000
    if open_ends == 0: return 0
    if run_length in RUN_SCORES: return RUN_SCORES[run_length].get(open_ends, 0)
    return 0

def generate_candidate_moves(board: list[list[str]], radius: int, max_candidates: int) -> list[tuple[int, int]]:
    size = len(board)
    occupied = [(r, c) for r in range(size) for c in range(size) if board[r][c] != EMPTY_CELL]
    if not occupied: return [(size // 2, size // 2)]
    candidates = set()
    for row, col in occupied:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr, nc = row + dr, col + dc
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
            if dr == 0 and dc == 0: continue
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size and board[nr][nc] != EMPTY_CELL:
                neighbor_count += 1
    return neighbor_count * 10 + center_bias

def get_zobrist(size: int) -> list[list[list[int]]]:
    if size in _ZOBRIST_CACHE: return _ZOBRIST_CACHE[size]
    generator = random.Random(20260410 + size)
    table = [[[generator.getrandbits(64), generator.getrandbits(64)] for _ in range(size)] for _ in range(size)]
    _ZOBRIST_CACHE[size] = table
    return table

def board_hash(board: list[list[str]], zobrist: list[list[list[int]]]) -> int:
    h = 0
    size = len(board)
    for row in range(size):
        for col in range(size):
            symbol = board[row][col]
            if symbol in SYMBOL_INDEX: h ^= zobrist[row][col][SYMBOL_INDEX[symbol]]
    return h

def all_empty_moves(board: list[list[str]]) -> list[tuple[int, int]]:
    return [(r, c) for r in range(len(board)) for c in range(len(board)) if board[r][c] == EMPTY_CELL]

def quick_move_score(board: list[list[str]], move: tuple[int, int], symbol: str) -> int:
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
        if 0 <= r < size and 0 <= c < size and board[r][c] == EMPTY_CELL: open_ends += 1
        r, c = row + dr, col + dc
        while 0 <= r < size and 0 <= c < size and board[r][c] == symbol:
            count += 1
            r += dr
            c += dc
        if 0 <= r < size and 0 <= c < size and board[r][c] == EMPTY_CELL: open_ends += 1
        score += _run_score(count, open_ends)
    return score

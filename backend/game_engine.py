from __future__ import annotations

from typing import Optional

EMPTY_CELL = ""
WIN_LENGTH = 5
VALID_SIZES = {7, 9, 11}
VALID_SYMBOLS = {EMPTY_CELL, "X", "O"}
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))


def create_empty_board(size: int) -> list[list[str]]:
    return [[EMPTY_CELL for _ in range(size)] for _ in range(size)]


def is_valid_size(size: int) -> bool:
    return size in VALID_SIZES


def in_bounds(size: int, row: int, col: int) -> bool:
    return 0 <= row < size and 0 <= col < size


def board_full(board: list[list[str]]) -> bool:
    return all(cell != EMPTY_CELL for row in board for cell in row)


def validate_board(board: list[list[str]], size: int) -> tuple[bool, Optional[str]]:
    if size not in VALID_SIZES:
        return False, "Unsupported board size"

    if len(board) != size:
        return False, "Board row count does not match size"

    for row in board:
        if len(row) != size:
            return False, "Board column count does not match size"
        for cell in row:
            if cell not in VALID_SYMBOLS:
                return False, "Board has invalid symbol"

    return True, None


def check_winner(
    board: list[list[str]],
    win_length: int = WIN_LENGTH,
) -> tuple[Optional[str], list[tuple[int, int]]]:
    size = len(board)

    for row in range(size):
        for col in range(size):
            symbol = board[row][col]
            if symbol == EMPTY_CELL:
                continue

            for dr, dc in DIRECTIONS:
                prev_row = row - dr
                prev_col = col - dc
                if in_bounds(size, prev_row, prev_col) and board[prev_row][prev_col] == symbol:
                    continue

                run: list[tuple[int, int]] = []
                r, c = row, col
                while in_bounds(size, r, c) and board[r][c] == symbol:
                    run.append((r, c))
                    r += dr
                    c += dc

                if len(run) >= win_length:
                    return symbol, run[:win_length]

    return None, []

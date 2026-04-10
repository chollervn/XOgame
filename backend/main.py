from __future__ import annotations

import random
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.ai_engine import choose_ai_move
from backend.game_engine import (
    EMPTY_CELL,
    board_full,
    check_winner,
    create_empty_board,
    in_bounds,
    validate_board,
)

app = FastAPI(title="XO AI Game", version="1.0.0")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class Move(BaseModel):
    row: int
    col: int


class NewGameRequest(BaseModel):
    size: Literal[7, 9, 11] = 9
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class PlayRequest(BaseModel):
    size: Literal[7, 9, 11]
    difficulty: Literal["easy", "medium", "hard"]
    board: list[list[str]]
    human_symbol: Literal["X", "O"]
    ai_symbol: Literal["X", "O"]
    player_move: Move


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/new-game")
def new_game(payload: NewGameRequest) -> dict:
    board = create_empty_board(payload.size)
    human_starts = random.choice([True, False])

    if human_starts:
        human_symbol = "X"
        ai_symbol = "O"
        first_player = "human"
        ai_move = None
    else:
        human_symbol = "O"
        ai_symbol = "X"
        first_player = "ai"
        ai_move = choose_ai_move(board, ai_symbol, human_symbol, payload.difficulty)
        if ai_move is not None:
            row, col = ai_move
            board[row][col] = ai_symbol

    return {
        "size": payload.size,
        "difficulty": payload.difficulty,
        "board": board,
        "human_symbol": human_symbol,
        "ai_symbol": ai_symbol,
        "first_player": first_player,
        "current_turn": "human",
        "status": "playing",
        "winner": None,
        "winning_cells": [],
        "ai_move": ai_move,
    }


@app.post("/api/play")
def play_turn(payload: PlayRequest) -> dict:
    if payload.human_symbol == payload.ai_symbol:
        raise HTTPException(status_code=400, detail="Human and AI symbols must be different")

    is_valid, error_message = validate_board(payload.board, payload.size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    board = [row[:] for row in payload.board]

    winner, winning_cells = check_winner(board)
    if winner is not None:
        return {
            "board": board,
            "status": "human_win" if winner == payload.human_symbol else "ai_win",
            "winner": winner,
            "winning_cells": winning_cells,
            "current_turn": "none",
            "player_move": None,
            "ai_move": None,
        }

    if board_full(board):
        return {
            "board": board,
            "status": "draw",
            "winner": None,
            "winning_cells": [],
            "current_turn": "none",
            "player_move": None,
            "ai_move": None,
        }

    move = payload.player_move
    if not in_bounds(payload.size, move.row, move.col):
        raise HTTPException(status_code=400, detail="Move is out of board range")
    if board[move.row][move.col] != EMPTY_CELL:
        raise HTTPException(status_code=400, detail="Cell is already occupied")

    board[move.row][move.col] = payload.human_symbol
    winner, winning_cells = check_winner(board)
    if winner is not None:
        return {
            "board": board,
            "status": "human_win" if winner == payload.human_symbol else "ai_win",
            "winner": winner,
            "winning_cells": winning_cells,
            "current_turn": "none",
            "player_move": [move.row, move.col],
            "ai_move": None,
        }

    if board_full(board):
        return {
            "board": board,
            "status": "draw",
            "winner": None,
            "winning_cells": [],
            "current_turn": "none",
            "player_move": [move.row, move.col],
            "ai_move": None,
        }

    ai_move = choose_ai_move(
        board=board,
        ai_symbol=payload.ai_symbol,
        human_symbol=payload.human_symbol,
        difficulty=payload.difficulty,
    )

    if ai_move is None:
        return {
            "board": board,
            "status": "draw",
            "winner": None,
            "winning_cells": [],
            "current_turn": "none",
            "player_move": [move.row, move.col],
            "ai_move": None,
        }

    ai_row, ai_col = ai_move
    board[ai_row][ai_col] = payload.ai_symbol

    winner, winning_cells = check_winner(board)
    if winner == payload.ai_symbol:
        status = "ai_win"
        current_turn = "none"
    elif board_full(board):
        status = "draw"
        current_turn = "none"
    else:
        status = "playing"
        current_turn = "human"

    return {
        "board": board,
        "status": status,
        "winner": winner,
        "winning_cells": winning_cells,
        "current_turn": current_turn,
        "player_move": [move.row, move.col],
        "ai_move": [ai_row, ai_col],
    }

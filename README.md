# XO AI Game (5-in-a-row)

Single-player XO web game with Python AI.

## Features

- Play against AI on `7x7`, `9x9`, or `11x11` boards.
- Win condition: 5 consecutive symbols in any direction.
- 3 levels: `easy`, `medium`, `hard`.
- New game randomizes who starts first.
- The side that starts first is always `X`.
- Simple, responsive interface for desktop and mobile.

## Tech Stack

- Backend: FastAPI (Python)
- Frontend: HTML, CSS, JavaScript (vanilla)
- AI: Alpha-Beta search with heuristic evaluation

## Run Locally

### One-click (Windows)

Double-click `start_game.bat`.

- It auto-installs dependencies if missing.
- It starts the server and opens the browser automatically.
- If port `8000` is busy, it picks the next available port (`8001`, `8002`, ...).

### Manual

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start server:

```bash
uvicorn backend.main:app --reload
```

4. Open browser:

```text
http://127.0.0.1:8000
```

### Single command (all platforms)

```bash
python run_game.py
```

## API Endpoints

- `GET /api/health` -> health check
- `POST /api/new-game` -> create a new game setup
- `POST /api/play` -> apply human move, then AI move

## AI Algorithm (for presentation)

The AI on hard level is built on:

1. **Minimax style search** (implemented as alpha-beta game tree search).
2. **Alpha-Beta pruning** to cut branches that cannot improve the result.
3. **Iterative deepening** with a time budget per move.
4. **Heuristic scoring** of board patterns:
   - open four / closed four
   - open three / closed three
   - open two, etc.
5. **Candidate move generation** around existing stones to reduce branching.
6. **Move ordering** to evaluate strong tactical moves first.
7. **Transposition table + Zobrist hash** to cache repeated board states.

Evaluation concept:

```text
score(board) = score_for_ai_patterns - score_for_human_patterns
best_move = argmax(alpha_beta_search(...))
```

Difficulty behavior:

- **Easy**: shallow search, short time limit, random noise.
- **Medium**: deeper search, moderate time limit, small noise.
- **Hard**: deepest search, longest think time, no randomness.

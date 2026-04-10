const boardElement = document.getElementById("board");
const sizeSelect = document.getElementById("sizeSelect");
const difficultySelect = document.getElementById("difficultySelect");
const newGameButton = document.getElementById("newGameBtn");
const roleInfo = document.getElementById("roleInfo");
const turnInfo = document.getElementById("turnInfo");
const resultInfo = document.getElementById("resultInfo");

let renderedBoardSize = 0;
let boardCells = [];

const state = {
  size: 9,
  difficulty: "medium",
  board: [],
  humanSymbol: "X",
  aiSymbol: "O",
  firstPlayer: "human",
  currentTurn: "human",
  status: "idle",
  winner: null,
  winningCells: new Set(),
  lastHumanMove: null,
  lastAIMove: null,
  busy: false,
  pendingMoveToken: 0,
  pendingNewGameToken: 0,
};

newGameButton.addEventListener("click", () => {
  startNewGame().catch(handleError);
});

boardElement.addEventListener("click", (event) => {
  const cell = event.target.closest("button.cell");
  if (!cell) {
    return;
  }

  const index = Number(cell.dataset.index);
  const row = Math.floor(index / state.size);
  const col = index % state.size;
  playHumanMove(row, col).catch(handleError);
});

startNewGame().catch(handleError);

async function startNewGame() {
  const requestToken = ++state.pendingNewGameToken;
  setBusy(true);

  const payload = {
    size: Number(sizeSelect.value),
    difficulty: difficultySelect.value,
  };

  const response = await postJSON("/api/new-game", payload);
  if (requestToken !== state.pendingNewGameToken) {
    return;
  }

  state.pendingMoveToken = 0;
  state.size = response.size;
  state.difficulty = response.difficulty;
  state.board = response.board;
  state.humanSymbol = response.human_symbol;
  state.aiSymbol = response.ai_symbol;
  state.firstPlayer = response.first_player;
  state.currentTurn = response.current_turn;
  state.status = response.status;
  state.winner = response.winner;
  state.winningCells = normalizeWinningCells(response.winning_cells);
  state.lastHumanMove = null;
  state.lastAIMove = normalizeMove(response.ai_move);

  setBusy(false);
  renderAll();
}

async function playHumanMove(row, col) {
  if (state.busy || state.status !== "playing" || state.currentTurn !== "human") {
    return;
  }

  if (state.board[row][col] !== "") {
    return;
  }

  const moveToken = ++state.pendingMoveToken;
  const boardBeforeMove = state.board.map((boardRow) => boardRow.slice());

  state.board[row][col] = state.humanSymbol;
  state.lastHumanMove = { row, col };
  state.lastAIMove = null;
  setBusy(true);
  state.currentTurn = "ai";
  renderAll();

  try {
    const response = await postJSON("/api/play", {
      size: state.size,
      difficulty: state.difficulty,
      board: boardBeforeMove,
      human_symbol: state.humanSymbol,
      ai_symbol: state.aiSymbol,
      player_move: { row, col },
    });

    if (moveToken !== state.pendingMoveToken) {
      return;
    }

    state.board = response.board;
    state.status = response.status;
    state.currentTurn = response.current_turn;
    state.winner = response.winner;
    state.winningCells = normalizeWinningCells(response.winning_cells);
    state.lastHumanMove = normalizeMove(response.player_move) ?? { row, col };
    state.lastAIMove = normalizeMove(response.ai_move);

    setBusy(false);
    renderAll();
  } catch (error) {
    if (moveToken !== state.pendingMoveToken) {
      return;
    }

    state.board = boardBeforeMove;
    state.currentTurn = "human";
    state.lastHumanMove = null;
    state.lastAIMove = null;
    setBusy(false);
    renderAll();
    throw error;
  }
}

function renderAll() {
  renderBoard();
  renderStatus();
}

function renderBoard() {
  ensureBoardGrid();

  for (let row = 0; row < state.size; row += 1) {
    for (let col = 0; col < state.size; col += 1) {
      const index = row * state.size + col;
      const cellValue = state.board[row][col];
      const button = boardCells[index];
      button.className = "cell";
      button.textContent = cellValue;

      if (cellValue === "X") {
        button.classList.add("x");
      } else if (cellValue === "O") {
        button.classList.add("o");
      }

      if (state.winningCells.has(keyForCell(row, col))) {
        button.classList.add("win");
      }

      if (isMove(row, col, state.lastHumanMove)) {
        button.classList.add("last-human");
      }

      if (isMove(row, col, state.lastAIMove)) {
        button.classList.add("last-ai");
      }

      const canPlay =
        !state.busy && state.status === "playing" && state.currentTurn === "human" && cellValue === "";
      button.disabled = !canPlay;

    }
  }
}

function ensureBoardGrid() {
  if (renderedBoardSize === state.size && boardCells.length === state.size * state.size) {
    return;
  }

  renderedBoardSize = state.size;
  boardCells = [];
  boardElement.style.setProperty("--grid-size", String(state.size));
  boardElement.innerHTML = "";

  const fragment = document.createDocumentFragment();
  const totalCells = state.size * state.size;

  for (let index = 0; index < totalCells; index += 1) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "cell";
    button.dataset.index = String(index);
    fragment.appendChild(button);
    boardCells.push(button);
  }

  boardElement.appendChild(fragment);
}

function renderStatus() {
  const firstPlayerLabel = state.firstPlayer === "human" ? "You" : "AI";
  roleInfo.textContent = `You: ${state.humanSymbol} | AI: ${state.aiSymbol} | First: ${firstPlayerLabel}`;

  if (state.status === "idle") {
    turnInfo.textContent = "Click Start New Game to begin.";
    resultInfo.textContent = "";
    return;
  }

  if (state.status === "playing") {
    if (state.currentTurn === "human") {
      turnInfo.textContent = "Your turn.";
      if (state.firstPlayer === "ai" && state.lastAIMove) {
        resultInfo.textContent = "AI opened as X.";
      } else {
        resultInfo.textContent = "";
      }
    } else {
      turnInfo.textContent = "AI is thinking...";
      resultInfo.textContent = "";
    }
    return;
  }

  turnInfo.textContent = "Game finished.";
  if (state.status === "human_win") {
    resultInfo.textContent = "You win.";
  } else if (state.status === "ai_win") {
    resultInfo.textContent = "AI wins.";
  } else if (state.status === "draw") {
    resultInfo.textContent = "Draw.";
  } else {
    resultInfo.textContent = "";
  }
}

function setBusy(value) {
  state.busy = value;
  newGameButton.disabled = value;
  sizeSelect.disabled = value;
  difficultySelect.disabled = value;
}

function keyForCell(row, col) {
  return `${row}-${col}`;
}

function normalizeWinningCells(cells) {
  if (!Array.isArray(cells)) {
    return new Set();
  }
  const output = new Set();
  for (const item of cells) {
    const move = normalizeMove(item);
    if (move) {
      output.add(keyForCell(move.row, move.col));
    }
  }
  return output;
}

function normalizeMove(value) {
  if (!Array.isArray(value) || value.length !== 2) {
    return null;
  }
  const row = Number(value[0]);
  const col = Number(value[1]);
  if (!Number.isInteger(row) || !Number.isInteger(col)) {
    return null;
  }
  return { row, col };
}

function isMove(row, col, move) {
  return move !== null && move.row === row && move.col === col;
}

async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : "Request failed";
    throw new Error(detail);
  }
  return data;
}

function handleError(error) {
  const message = error instanceof Error ? error.message : "Unexpected error";
  turnInfo.textContent = "Something went wrong.";
  resultInfo.textContent = message;
  state.busy = false;
  newGameButton.disabled = false;
  sizeSelect.disabled = false;
  difficultySelect.disabled = false;
  renderBoard();
}

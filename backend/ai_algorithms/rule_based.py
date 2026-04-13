from backend.game_engine import EMPTY_CELL, check_winner
from backend.ai_utils import DifficultyProfile, all_empty_moves, quick_move_score
from backend.ai_algorithms.base import AIStrategy

class RuleBasedStrategy(AIStrategy):
    """Thuật toán phân tích luật cứng (Tìm nước wins / chặn loss ngay lập tức)."""

    def get_move(self, board: list[list[str]], ai_symbol: str, human_symbol: str, profile: DifficultyProfile) -> tuple[int, int] | None:
        empty_moves = all_empty_moves(board)
        if not empty_moves:
            return None

        # 1. Tìm nước AI có thể thắng ngay
        ai_win_move = self._find_winning_move(board, empty_moves, ai_symbol)
        if ai_win_move:
            return ai_win_move

        # 2. Ngăn người chơi thắng ngay (Chặn)
        human_win_moves = self._find_all_winning_moves(board, empty_moves, human_symbol)
        if human_win_moves:
            if len(human_win_moves) == 1:
                return human_win_moves[0]
            # Nếu có nhiều đường chặn, chọn đường tốt nhất cho AI
            return max(
                human_win_moves,
                key=lambda move: quick_move_score(board, move, ai_symbol),
            )
            
        return None

    def _find_winning_move(self, board, candidates, symbol):
        for row, col in candidates:
            board[row][col] = symbol
            winner, _ = check_winner(board)
            board[row][col] = EMPTY_CELL
            if winner == symbol:
                return row, col
        return None

    def _find_all_winning_moves(self, board, candidates, symbol):
        wins = []
        for row, col in candidates:
            board[row][col] = symbol
            winner, _ = check_winner(board)
            board[row][col] = EMPTY_CELL
            if winner == symbol:
                wins.append((row, col))
        return wins
